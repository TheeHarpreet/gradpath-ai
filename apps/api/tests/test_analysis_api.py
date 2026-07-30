"""End-to-end API tests with a deterministic in-memory model provider."""

import pytest
from gradpath_api.application.analysis_service import AnalysisService
from gradpath_api.application.retrievers import EvidenceRetrievalError
from gradpath_api.core.config import Settings
from gradpath_api.domain.analysis import (
    ChangeDecision,
    ChangeSuggestion,
    Citation,
    CoverageStatus,
    JobRequirement,
    ModelAnalysis,
    RequirementAssessment,
    SourceKind,
)
from gradpath_api.domain.context import AnalysisContext
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk
from gradpath_api.main import create_app
from httpx import ASGITransport, AsyncClient

CV_TEXT = """# Alex Example

## Project

Built a React interface using TypeScript and added Vitest component tests.

## Education

Completed a fictional Computer Science degree at Example University.
"""

JOB_TEXT = """# Graduate Frontend Engineer

## Essential requirements

1. Practical TypeScript development experience.

## Desirable requirements

2. Exposure to AWS cloud services.
"""


class DeterministicProvider:
    """Return a known-safe result without a network request."""

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
                    rationale="The project directly demonstrates TypeScript.",
                    citations=[citation],
                ),
                RequirementAssessment(
                    requirement=context.requirements[1],
                    status=CoverageStatus.UNSUPPORTED,
                    rationale="No supplied source demonstrates AWS exposure.",
                ),
            ],
            strengths=["TypeScript project experience"],
            gaps=["AWS cloud services"],
            changes=[
                ChangeSuggestion(
                    change_id="change-001",
                    target="profile",
                    decision=ChangeDecision.REWRITE,
                    suggested_text=(
                        "Computer Science graduate with TypeScript experience."
                    ),
                    reason="Lead with evidence relevant to the vacancy.",
                    citations=[citation],
                    confidence=0.95,
                )
            ],
            unsupported_claim_warnings=["Do not claim AWS experience."],
            aligned_cv_markdown=(
                "# Alex Example\n\nComputer Science graduate with TypeScript "
                "project experience."
            ),
        )


class FailingRetriever:
    """Simulate a retrieval failure without exposing its underlying detail."""

    async def retrieve(
        self,
        requirements: list[JobRequirement],
        catalog: list[SourceChunk],
    ) -> dict[str, list[RetrievedEvidence]]:
        del requirements, catalog
        raise EvidenceRetrievalError("Sensitive retrieval detail")


@pytest.mark.asyncio
async def test_analysis_endpoint_crosses_the_complete_application_slice() -> None:
    settings = Settings(_env_file=None, environment="test")
    app = create_app(settings)
    app.state.analysis_service = AnalysisService(DeterministicProvider())

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/analyses",
            json={
                "candidate_cv": CV_TEXT,
                "job_description": JOB_TEXT,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"].startswith("analysis-")
    assert payload["requirements"][0]["status"] == "supported"
    assert payload["requirements"][1]["status"] == "unsupported"
    assert payload["review_required"] is True
    assert "AWS" not in payload["aligned_cv_markdown"]


@pytest.mark.asyncio
async def test_analysis_endpoint_is_unavailable_without_a_provider() -> None:
    settings = Settings(_env_file=None, environment="test")
    app = create_app(settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/analyses",
            json={
                "candidate_cv": CV_TEXT,
                "job_description": JOB_TEXT,
            },
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "The analysis provider is not configured."}


@pytest.mark.asyncio
async def test_analysis_endpoint_masks_retrieval_failures() -> None:
    settings = Settings(_env_file=None, environment="test")
    app = create_app(settings)
    app.state.analysis_service = AnalysisService(
        DeterministicProvider(),
        retriever=FailingRetriever(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/analyses",
            json={
                "candidate_cv": CV_TEXT,
                "job_description": JOB_TEXT,
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The analysis provider did not return a safe result."
    }
    assert "Sensitive" not in response.text
