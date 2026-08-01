"""Generate portfolio-ready PNG diagrams for the Step 5 agent workflow."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "images"
NAVY = "#14213d"
BLUE = "#2563eb"
PALE_BLUE = "#dbeafe"
PALE_GREEN = "#dcfce7"
PALE_AMBER = "#fef3c7"
PALE_RED = "#fee2e2"
WHITE = "#ffffff"
INK = "#111827"
MUTED = "#4b5563"


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a standard Windows font for consistent local generation."""

    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(name, size)


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    fill: str,
) -> None:
    """Draw one labelled architecture component."""

    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=BLUE, width=3)
    x1, y1, x2, _ = xy
    center = (x1 + x2) / 2
    draw.text(
        (center, y1 + 20),
        title,
        font=font(23, bold=True),
        fill=INK,
        anchor="ma",
    )
    draw.multiline_text(
        (center, y1 + 58),
        subtitle,
        font=font(17),
        fill=MUTED,
        anchor="ma",
        align="center",
        spacing=5,
    )


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    label: str = "",
) -> None:
    """Draw a horizontal relationship arrow and optional label."""

    draw.line([start, end], fill=NAVY, width=4)
    x, y = end
    direction = 1 if end[0] > start[0] else -1
    draw.polygon(
        [(x, y), (x - direction * 12, y - 7), (x - direction * 12, y + 7)],
        fill=NAVY,
    )
    if label:
        draw.text(
            ((start[0] + end[0]) / 2, start[1] - 10),
            label,
            font=font(15),
            fill=MUTED,
            anchor="ms",
        )


def interactions() -> None:
    """Generate the component-interaction diagram."""

    image = Image.new("RGB", (1600, 900), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text(
        (800, 55),
        "GradPath AI — Step 5 agent interactions",
        font=font(36, bold=True),
        fill=NAVY,
        anchor="ma",
    )
    draw.text(
        (800, 105),
        "The model judges evidence; application code controls safety and state",
        font=font(21),
        fill=MUTED,
        anchor="ma",
    )
    box(
        draw,
        (70, 290, 350, 470),
        "Candidate",
        "CV + job description\nclarifications\nreview decisions",
        PALE_GREEN,
    )
    box(
        draw,
        (470, 260, 820, 500),
        "LangGraph control plane",
        "typed state\nrouting + bounded retries\nhuman pauses",
        PALE_BLUE,
    )
    box(
        draw,
        (940, 185, 1510, 395),
        "Agents SDK specialist",
        "tool-less structured analysis\nrequirements + citations\ndraft + changes",
        PALE_AMBER,
    )
    box(
        draw,
        (940, 515, 1510, 725),
        "Deterministic safeguards",
        "hybrid retrieval\nexact citation verification\nschema + policy checks",
        PALE_RED,
    )
    arrow(draw, (350, 350), (470, 350), "submit / resume")
    arrow(draw, (820, 300), (940, 250))
    draw.text(
        (875, 255),
        "prepared evidence",
        font=font(15),
        fill=MUTED,
        anchor="ms",
    )
    arrow(draw, (940, 360), (820, 400))
    draw.text((880, 370), "typed output", font=font(15), fill=MUTED, anchor="ms")
    arrow(draw, (820, 435), (940, 575))
    arrow(draw, (940, 665), (820, 475))
    arrow(draw, (470, 440), (350, 440), "clarify / review")
    draw.rounded_rectangle((70, 785, 1510, 850), radius=16, fill=NAVY)
    draw.text(
        (790, 818),
        "Invariant: no draft becomes final until the candidate explicitly approves it",
        font=font(22, bold=True),
        fill=WHITE,
        anchor="mm",
    )
    image.save(OUTPUT / "step-5-agent-interactions.png")


def sequence() -> None:
    """Generate the resumable request sequence diagram."""

    image = Image.new("RGB", (1600, 1000), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text(
        (800, 45),
        "GradPath AI — Step 5 resumable sequence",
        font=font(36, bold=True),
        fill=NAVY,
        anchor="ma",
    )
    columns = [
        (170, "Candidate"),
        (530, "API / LangGraph"),
        (930, "Retrieval + verifier"),
        (1350, "Agents SDK"),
    ]
    for x, label in columns:
        draw.text((x, 120), label, font=font(22, bold=True), fill=INK, anchor="ma")
        draw.line((x, 150, x, 920), fill="#9ca3af", width=2)
    steps = [
        (190, 170, 530, "Start workflow"),
        (250, 530, 930, "Retrieve owned evidence"),
        (310, 930, 530, "Ranked evidence + provenance"),
        (370, 530, 1350, "Typed evidence package"),
        (430, 1350, 530, "Structured analysis"),
        (490, 530, 930, "Verify claims and citations"),
        (550, 930, 530, "Pass / retry / clarify"),
        (640, 530, 170, "Pause for clarification or review"),
        (720, 170, 530, "Candidate-controlled response"),
        (790, 530, 930, "Recheck evidence and decisions"),
        (860, 530, 170, "Candidate-approved CV"),
    ]
    for y, start_x, end_x, label in steps:
        arrow(draw, (start_x, y), (end_x, y), label)
    draw.text(
        (800, 955),
        "Provider and validation retries are bounded; every pause is typed state.",
        font=font(19),
        fill=MUTED,
        anchor="mm",
    )
    image.save(OUTPUT / "step-5-agent-sequence.png")


def main() -> None:
    """Write both diagrams to the documentation image directory."""

    OUTPUT.mkdir(parents=True, exist_ok=True)
    interactions()
    sequence()


if __name__ == "__main__":
    main()
