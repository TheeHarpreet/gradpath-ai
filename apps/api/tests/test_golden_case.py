"""Regression test for the first fictional evaluation case."""

import json
from pathlib import Path
from typing import Any

import pytest
from gradpath_api.application.analysis_service import AnalysisService
from gradpath_api.domain.analysis import (
    AnalysisRequest,
    ChangeDecision,
    ChangeSuggestion,
    Citation,
    CoverageStatus,
    ModelAnalysis,
    RequirementAssessment,
)
from gradpath_api.domain.context import AnalysisContext

CASE_PATH = (
    Path(__file__).resolve().parents[3] / "evals" / "cases" / "graduate-fullstack-001"
)


class GoldenCaseProvider:
    """Turn the checked-in answer key into deterministic provider output."""

    def __init__(self, expected: dict[str, Any], aligned_cv: str) -> None:
        self._expected = expected
        self._aligned_cv = aligned_cv

    async def analyse(self, context: AnalysisContext) -> ModelAnalysis:
        sources = {item.source_id: item for item in context.source_catalog}
        expected_requirements = {
            item["id"]: item for item in self._expected["requirements"]
        }
        assessments: list[RequirementAssessment] = []
        for requirement in context.requirements:
            expected = expected_requirements[requirement.requirement_id]
            citations = [
                Citation(
                    source_id=source_id,
                    source_kind=sources[source_id].source_kind,
                    quote=sources[source_id].text[:1_000],
                )
                for source_id in expected["evidence_ids"]
            ]
            assessments.append(
                RequirementAssessment(
                    requirement=requirement,
                    status=CoverageStatus(expected["expected_status"]),
                    rationale=(
                        f"Golden-case assessment for {requirement.requirement_id}."
                    ),
                    citations=citations,
                )
            )

        changes: list[ChangeSuggestion] = []
        for index, expected_change in enumerate(
            self._expected["expected_changes"],
            start=1,
        ):
            citations = [
                Citation(
                    source_id=source_id,
                    source_kind=sources[source_id].source_kind,
                    quote=sources[source_id].text[:1_000],
                )
                for source_id in expected_change["required_evidence_ids"]
            ]
            changes.append(
                ChangeSuggestion(
                    change_id=f"change-{index:03d}",
                    target=expected_change["target"],
                    decision=ChangeDecision(expected_change["decision"]),
                    suggested_text=(
                        "Evidence-grounded wording for candidate review."
                        if citations
                        else None
                    ),
                    reason=expected_change["reason"],
                    citations=citations,
                    confidence=1,
                )
            )

        return ModelAnalysis(
            requirements=assessments,
            strengths=self._expected["required_strengths"],
            gaps=self._expected["required_gaps"],
            changes=changes,
            unsupported_claim_warnings=self._expected["prohibited_candidate_claims"],
            aligned_cv_markdown=self._aligned_cv,
        )


@pytest.mark.asyncio
async def test_first_golden_case_crosses_the_complete_service_slice() -> None:
    expected = json.loads((CASE_PATH / "expected.json").read_text(encoding="utf-8"))
    aligned_cv = (CASE_PATH / "reference-aligned-cv.md").read_text(encoding="utf-8")
    request = AnalysisRequest(
        candidate_cv=(CASE_PATH / "candidate-cv.md").read_text(encoding="utf-8"),
        job_description=(CASE_PATH / "job-description.md").read_text(encoding="utf-8"),
        supporting_evidence=(CASE_PATH / "supporting-evidence.md").read_text(
            encoding="utf-8"
        ),
    )

    result = await AnalysisService(GoldenCaseProvider(expected, aligned_cv)).analyse(
        request
    )

    assert len(result.requirements) == 11
    assert [item.status.value for item in result.requirements] == [
        item["expected_status"] for item in expected["requirements"]
    ]
    assert result.gaps == expected["required_gaps"]
    for text in expected["aligned_cv_checks"]["must_include"]:
        assert text in result.aligned_cv_markdown
    for text in expected["aligned_cv_checks"]["must_not_include_as_candidate_claims"]:
        assert text not in result.aligned_cv_markdown
    for text in expected["aligned_cv_checks"]["must_preserve"]:
        assert text in result.aligned_cv_markdown
    assert result.review_required is True
