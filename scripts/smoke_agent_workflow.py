"""Run one fictional golden case through the real Step 5 agent workflow."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from gradpath_api.core.config import Settings
from gradpath_api.domain.analysis import AnalysisRequest
from gradpath_api.main import create_app

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "evals" / "cases" / "graduate-fullstack-001"


async def run() -> None:
    """Execute a network-backed smoke test and print only safe summary fields."""

    settings = Settings()
    app = create_app(settings)
    service = app.state.workflow_service
    if service is None:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    result = await service.start(
        AnalysisRequest(
            candidate_cv=(CASE / "candidate-cv.md").read_text(encoding="utf-8"),
            job_description=(CASE / "job-description.md").read_text(encoding="utf-8"),
            supporting_evidence=(CASE / "supporting-evidence.md").read_text(
                encoding="utf-8"
            ),
        )
    )
    summary = {
        "status": result.status,
        "retry_count": result.retry_count,
        "requirement_statuses": (
            [item.status for item in result.analysis.requirements]
            if result.analysis
            else []
        ),
        "clarification_count": len(result.clarification_questions),
        "change_count": len(result.analysis.changes) if result.analysis else 0,
        "event_count": len(result.events),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
