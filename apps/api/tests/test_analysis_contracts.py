"""Safety-focused tests for analysis boundary models."""

import pytest
from gradpath_api.domain.analysis import (
    AnalysisRequest,
    ChangeDecision,
    ChangeSuggestion,
    CoverageStatus,
    JobRequirement,
    RequirementAssessment,
    RequirementPriority,
)
from pydantic import ValidationError


def test_analysis_request_rejects_empty_documents() -> None:
    """A request needs meaningful CV and vacancy text."""

    with pytest.raises(ValidationError):
        AnalysisRequest(candidate_cv="too short", job_description="also short")


def test_supported_assessment_requires_a_citation() -> None:
    """Positive match labels cannot exist without candidate evidence."""

    requirement = JobRequirement(
        requirement_id="req-001",
        priority=RequirementPriority.ESSENTIAL,
        source_text="Experience building REST APIs.",
    )

    with pytest.raises(
        ValidationError,
        match="supported assessments require at least one citation",
    ):
        RequirementAssessment(
            requirement=requirement,
            status=CoverageStatus.SUPPORTED,
            rationale="The candidate meets this requirement.",
        )


def test_unsupported_assessment_can_be_citation_free() -> None:
    """A genuine absence of evidence does not require a fabricated citation."""

    requirement = JobRequirement(
        requirement_id="req-011",
        priority=RequirementPriority.DESIRABLE,
        source_text="Familiarity with Kubernetes.",
    )

    assessment = RequirementAssessment(
        requirement=requirement,
        status=CoverageStatus.UNSUPPORTED,
        rationale="No supplied evidence mentions Kubernetes.",
    )

    assert assessment.citations == []


def test_rewritten_wording_requires_a_citation() -> None:
    """The change report cannot introduce uncited factual wording."""

    with pytest.raises(
        ValidationError,
        match="added or rewritten wording requires a citation",
    ):
        ChangeSuggestion(
            change_id="change-001",
            target="profile",
            decision=ChangeDecision.REWRITE,
            suggested_text="Experienced AWS engineer.",
            reason="Match the vacancy.",
            confidence=0.9,
        )
