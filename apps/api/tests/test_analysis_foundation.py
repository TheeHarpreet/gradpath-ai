"""Tests for deterministic source, requirement, retrieval and validation logic."""

import pytest
from gradpath_api.application.requirements import (
    RequirementExtractionError,
    extract_requirements,
)
from gradpath_api.application.retrieval import retrieve_evidence
from gradpath_api.application.sources import SourceCatalogError, build_source_catalog
from gradpath_api.application.validation import (
    AnalysisValidationError,
    validate_model_analysis,
)
from gradpath_api.domain.analysis import (
    AnalysisRequest,
    Citation,
    CoverageStatus,
    ModelAnalysis,
    RequirementAssessment,
    RequirementPriority,
    SourceKind,
)

CV_TEXT = """# Candidate

## Project

Built a React interface using TypeScript and tested it with Vitest.

## Education

Completed a Computer Science degree with a database module.
"""

JOB_TEXT = """# Graduate Engineer

## Essential requirements

1. Practical TypeScript development experience.
2. Evidence of automated testing.

## Desirable requirements

3. Exposure to AWS cloud services.
"""


def _request() -> AnalysisRequest:
    return AnalysisRequest(candidate_cv=CV_TEXT, job_description=JOB_TEXT)


def test_requirement_extraction_preserves_priority_and_source_text() -> None:
    requirements = extract_requirements(JOB_TEXT)

    assert [item.priority for item in requirements] == [
        RequirementPriority.ESSENTIAL,
        RequirementPriority.ESSENTIAL,
        RequirementPriority.DESIRABLE,
    ]
    assert requirements[0].source_text == (
        "Practical TypeScript development experience."
    )


def test_requirement_extraction_rejects_unstructured_vacancy() -> None:
    with pytest.raises(RequirementExtractionError):
        extract_requirements("A role without an explicit requirements list.")


def test_lexical_retrieval_returns_traceable_source_chunks() -> None:
    request = _request()
    catalog = build_source_catalog(request)
    requirements = extract_requirements(request.job_description)

    retrieved = retrieve_evidence(requirements, catalog)

    assert retrieved["req-001"][0].source_id == "cv-001"
    assert "TypeScript" in retrieved["req-001"][0].text
    assert retrieved["req-003"] == []


def test_source_catalog_rejects_duplicate_candidate_anchors() -> None:
    request = AnalysisRequest(
        candidate_cv=(
            "# Candidate\n\n## First {#duplicate}\n\nOne factual section.\n\n"
            "## Second {#duplicate}\n\nAnother factual section."
        ),
        job_description=JOB_TEXT,
    )

    with pytest.raises(SourceCatalogError, match="duplicate source IDs"):
        build_source_catalog(request)


def test_validation_rejects_a_quote_not_found_in_its_source() -> None:
    request = _request()
    catalog = build_source_catalog(request)
    requirements = extract_requirements(request.job_description)
    bad_citation = Citation(
        source_id="cv-001",
        source_kind=SourceKind.CANDIDATE_CV,
        quote="Deployed production systems to AWS.",
    )
    assessments = [
        RequirementAssessment(
            requirement=requirement,
            status=(
                CoverageStatus.SUPPORTED
                if requirement.requirement_id == "req-001"
                else CoverageStatus.UNSUPPORTED
            ),
            rationale="Test assessment.",
            citations=(
                [bad_citation] if requirement.requirement_id == "req-001" else []
            ),
        )
        for requirement in requirements
    ]
    analysis = ModelAnalysis(
        requirements=assessments,
        strengths=[],
        gaps=["AWS"],
        changes=[],
        unsupported_claim_warnings=[],
        aligned_cv_markdown="# Candidate\n\nDraft CV.",
    )

    with pytest.raises(AnalysisValidationError, match="not present"):
        validate_model_analysis(
            analysis,
            requirements=requirements,
            catalog=catalog,
        )


def test_validation_rejects_duplicate_requirement_assessments() -> None:
    request = _request()
    catalog = build_source_catalog(request)
    requirements = extract_requirements(request.job_description)
    assessments = [
        RequirementAssessment(
            requirement=requirement,
            status=CoverageStatus.UNSUPPORTED,
            rationale="No supporting evidence was found.",
            citations=[],
        )
        for requirement in requirements
    ]
    analysis = ModelAnalysis(
        requirements=[*assessments, assessments[0]],
        strengths=[],
        gaps=[],
        changes=[],
        unsupported_claim_warnings=[],
        aligned_cv_markdown="# Candidate\n\nDraft CV.",
    )

    with pytest.raises(AnalysisValidationError, match="exactly match"):
        validate_model_analysis(
            analysis,
            requirements=requirements,
            catalog=catalog,
        )
