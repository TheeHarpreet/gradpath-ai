"""HTTP contract tests for starting and resuming an agent workflow."""

import pytest
from gradpath_api.application.alignment_workflow import AlignmentWorkflowService
from gradpath_api.application.retrievers import LexicalEvidenceRetriever
from gradpath_api.application.workflow_repository import InMemoryWorkflowRepository
from gradpath_api.core.config import Settings
from gradpath_api.domain.analysis import (
    ChangeDecision,
    ChangeSuggestion,
    Citation,
    CoverageStatus,
    ModelAnalysis,
    RequirementAssessment,
    SourceKind,
)
from gradpath_api.domain.context import AnalysisContext
from gradpath_api.main import create_app
from httpx import ASGITransport, AsyncClient

CV_TEXT = """# Alex Example

## Project

Built a React interface using TypeScript and added Vitest component tests.

## Education

Completed a fictional Computer Science degree at Example University.
"""

JOB_TEXT = """# Graduate Engineer

## Essential requirements

1. Practical TypeScript development experience.

## Desirable requirements

2. Exposure to AWS cloud services.
"""


class SafeProvider:
    """Return a fixed typed result through the real workflow graph."""

    async def analyse(self, context: AnalysisContext) -> ModelAnalysis:
        citation = Citation(
            source_id="cv-001",
            source_kind=SourceKind.CANDIDATE_CV,
            quote=(
                "Built a React interface using TypeScript and added Vitest "
                "component tests."
            ),
        )
        return ModelAnalysis(
            requirements=[
                RequirementAssessment(
                    requirement=context.requirements[0],
                    status=CoverageStatus.SUPPORTED,
                    rationale="Direct TypeScript evidence.",
                    citations=[citation],
                ),
                RequirementAssessment(
                    requirement=context.requirements[1],
                    status=CoverageStatus.UNSUPPORTED,
                    rationale="No AWS evidence.",
                ),
            ],
            strengths=["TypeScript"],
            gaps=["AWS"],
            changes=[
                ChangeSuggestion(
                    change_id="change-001",
                    target="profile",
                    decision=ChangeDecision.REWRITE,
                    suggested_text="Graduate with TypeScript project experience.",
                    reason="Lead with relevant evidence.",
                    citations=[citation],
                    confidence=0.9,
                )
            ],
            unsupported_claim_warnings=["Do not claim AWS experience."],
            aligned_cv_markdown="# Alex Example\n\nTypeScript project experience.",
        )


@pytest.mark.asyncio
async def test_workflow_http_lifecycle_requires_explicit_review() -> None:
    app = create_app(Settings(_env_file=None, environment="test"))
    app.state.workflow_service = AlignmentWorkflowService(
        provider=SafeProvider(),
        retriever=LexicalEvidenceRetriever(),
        repository=InMemoryWorkflowRepository(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        started = await client.post(
            "/api/v1/workflows",
            json={"candidate_cv": CV_TEXT, "job_description": JOB_TEXT},
        )
        assert started.status_code == 200
        snapshot = started.json()
        assert snapshot["status"] == "awaiting_review"
        assert snapshot["approved_cv_markdown"] is None

        completed = await client.post(
            f"/api/v1/workflows/{snapshot['workflow_id']}/review",
            json={
                "decisions": [{"change_id": "change-001", "action": "accept"}],
                "approved_cv_markdown": snapshot["analysis"]["aligned_cv_markdown"],
            },
        )

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        deleted = await client.delete(f"/api/v1/workflows/{snapshot['workflow_id']}")
        missing = await client.get(f"/api/v1/workflows/{snapshot['workflow_id']}")

    assert deleted.status_code == 204
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_workflow_endpoint_is_unavailable_without_a_provider() -> None:
    app = create_app(Settings(_env_file=None, environment="test"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/workflows",
            json={"candidate_cv": CV_TEXT, "job_description": JOB_TEXT},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "The workflow provider is not configured."}
