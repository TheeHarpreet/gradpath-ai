"""Generate fictional CV exports for Step 7 render verification."""

from pathlib import Path

from gradpath_api.application.documents import build_cv_docx, build_cv_pdf

SAMPLE_CV = """# Alex Example

alex.example@email.test | Manchester, UK | github.com/example

## Profile

Computer Science graduate and junior software developer with evidence from
full-stack web projects, automated testing, data analysis, and cloud deployment.
Interested in graduate software engineering, frontend, backend, and full-stack
roles.

## Technical Skills

- Languages: Python, TypeScript, JavaScript, SQL, HTML, CSS
- Frameworks: React, FastAPI, Node.js
- Testing: Pytest, Vitest, React Testing Library
- Tools: Git, GitHub Actions, Docker, PostgreSQL

## Projects

### GradPath AI | Full-stack developer

- Built a React and TypeScript workflow that compares a candidate CV with a job
  description and keeps the candidate in control of every suggested change.
- Created a FastAPI service with typed contracts, evidence citations,
  clarification pauses, human approval gates, and downloadable DOCX and PDF
  exports.
- Added hybrid retrieval, an agent workflow, and a Model Context Protocol server
  while preventing unsupported candidate claims from reaching the final CV.
- Wrote automated tests and containerised the web and API services with Docker.

### Graduate Data Explorer | Developer

- Analysed a fictional graduate-employment dataset with Python and SQL,
  documenting validation rules and data-quality limitations.
- Designed an accessible React dashboard with filters, summary metrics, and
  responsive charts.
- Added unit and integration tests and documented a cloud deployment approach.

## Education

### BSc Computer Science | Example University | 2023-2026

- Studied software engineering, databases, web development, algorithms, and
  data analysis.
- Final-year project focused on building and evaluating a tested web application.

## Additional Experience

- Used Git branches and pull requests to organise incremental project delivery.
- Explained architecture decisions, API boundaries, privacy controls, and
  testing evidence in project documentation.
- Practised breaking product requirements into small implementation steps and
  verifying each step before release.

## Interests

Open-source software, accessible web interfaces, developer tooling, and
responsible AI-assisted engineering.
"""


def main() -> None:
    output = Path("tmp/step7-export-qa")
    output.mkdir(parents=True, exist_ok=True)
    (output / "fictional-gradpath-cv.docx").write_bytes(build_cv_docx(SAMPLE_CV))
    (output / "fictional-gradpath-cv.pdf").write_bytes(build_cv_pdf(SAMPLE_CV))


if __name__ == "__main__":
    main()
