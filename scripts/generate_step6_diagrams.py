"""Generate PNG architecture diagrams for the Step 6 MCP integration."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "images"
NAVY = "#14213d"
BLUE = "#2563eb"
INK = "#111827"
MUTED = "#4b5563"
WHITE = "#ffffff"
FILLS = ["#dcfce7", "#dbeafe", "#fef3c7", "#fee2e2"]


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load standard Windows fonts for deterministic local rendering."""

    return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)


def title(draw: ImageDraw.ImageDraw, heading: str, subtitle: str) -> None:
    """Draw a consistent diagram heading."""

    draw.text((800, 50), heading, font=font(36, bold=True), fill=NAVY, anchor="ma")
    draw.text((800, 98), subtitle, font=font(20), fill=MUTED, anchor="ma")


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    heading: str,
    lines: str,
    fill: str,
) -> None:
    """Draw one labelled component."""

    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=BLUE, width=3)
    x1, y1, x2, _ = xy
    center = (x1 + x2) / 2
    draw.text(
        (center, y1 + 25),
        heading,
        font=font(22, bold=True),
        fill=INK,
        anchor="ma",
    )
    draw.multiline_text(
        (center, y1 + 68),
        lines,
        font=font(17),
        fill=MUTED,
        anchor="ma",
        align="center",
        spacing=6,
    )


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    label: str,
) -> None:
    """Draw a horizontal arrow with a centred label."""

    draw.line([start, end], fill=NAVY, width=4)
    direction = 1 if end[0] > start[0] else -1
    x, y = end
    draw.polygon(
        [(x, y), (x - direction * 12, y - 7), (x - direction * 12, y + 7)],
        fill=NAVY,
    )
    draw.text(
        ((start[0] + end[0]) / 2, y - 12),
        label,
        font=font(15),
        fill=MUTED,
        anchor="ms",
    )


def trust_boundary() -> None:
    """Generate the MCP capability and trust-boundary diagram."""

    image = Image.new("RGB", (1600, 900), WHITE)
    draw = ImageDraw.Draw(image)
    title(
        draw,
        "GradPath AI — Step 6 MCP trust boundary",
        "Private stdio connectivity with candidate scope and approval-gated writes",
    )
    components = [
        (
            (55, 290, 330, 500),
            "Candidate",
            "asks agent\napproves exact write",
            FILLS[0],
        ),
        (
            (425, 250, 735, 540),
            "Agents SDK",
            "discovers MCP tools\npauses write call\nresumes approved run",
            FILLS[1],
        ),
        (
            (830, 225, 1160, 565),
            "GradPath MCP",
            "3 narrow tools\n2 read resources\nstdio transport\nfixed profile scope",
            FILLS[2],
        ),
        (
            (1255, 270, 1545, 520),
            "Tracker service",
            "ownership checks\nstage transitions\nsingle-use token\naudit result",
            FILLS[3],
        ),
    ]
    for xy, heading, lines, fill in components:
        box(draw, xy, heading, lines, fill)
    arrow(draw, (330, 360), (425, 360), "request")
    arrow(draw, (735, 330), (830, 330), "tools/call")
    arrow(draw, (1160, 360), (1255, 360), "scoped use case")
    arrow(draw, (1255, 440), (1160, 440), "safe result")
    arrow(draw, (830, 480), (735, 480), "tool output")
    arrow(draw, (425, 450), (330, 450), "approval / result")
    draw.rounded_rectangle((55, 695, 1545, 820), radius=18, fill=NAVY)
    draw.multiline_text(
        (800, 735),
        "Not exposed: apply to jobs • email employers • delete records • "
        "arbitrary SQL\n"
        "URLs • shell/filesystem access • CV bodies • other candidates' data",
        font=font(21, bold=True),
        fill=WHITE,
        anchor="ma",
        align="center",
        spacing=8,
    )
    image.save(OUTPUT / "step-6-mcp-trust-boundary.png")


def approval_sequence() -> None:
    """Generate the MCP read and approved-write sequence diagram."""

    image = Image.new("RGB", (1600, 1000), WHITE)
    draw = ImageDraw.Draw(image)
    title(
        draw,
        "GradPath AI — Step 6 approval sequence",
        "A model can propose a write; application and server controls authorize it",
    )
    columns = [
        (150, "Candidate"),
        (500, "Agents SDK"),
        (830, "MCP server"),
        (1190, "Tracker service"),
        (1470, "Repository"),
    ]
    for x, label in columns:
        draw.text((x, 145), label, font=font(21, bold=True), fill=INK, anchor="ma")
        draw.line((x, 175, x, 920), fill="#9ca3af", width=2)
    steps = [
        (215, 150, 500, "inspect tracker"),
        (280, 500, 830, "list_job_applications"),
        (345, 830, 1190, "list for profile-demo-001"),
        (410, 1190, 1470, "owned query"),
        (475, 1470, 500, "2 fictional records"),
        (555, 500, 150, "request exact write approval"),
        (625, 150, 500, "approve interruption"),
        (695, 500, 830, "update + one-time token"),
        (760, 830, 1190, "verify scope, transition, token"),
        (825, 1190, 1470, "persist approved stage"),
        (890, 1470, 150, "applied + audit event"),
    ]
    for y, start_x, end_x, label in steps:
        arrow(draw, (start_x, y), (end_x, y), label)
    image.save(OUTPUT / "step-6-mcp-approval-sequence.png")


def main() -> None:
    """Generate both Step 6 PNG artifacts."""

    OUTPUT.mkdir(parents=True, exist_ok=True)
    trust_boundary()
    approval_sequence()


if __name__ == "__main__":
    main()
