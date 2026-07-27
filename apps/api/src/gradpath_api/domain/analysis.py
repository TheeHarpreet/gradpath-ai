"""Typed contracts for evidence-grounded CV analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    """Strict base model for data that crosses an application boundary."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceKind(StrEnum):
    """Candidate-controlled source types accepted by the first vertical slice."""

    CANDIDATE_CV = "candidate_cv"
    SUPPORTING_EVIDENCE = "supporting_evidence"


class RequirementPriority(StrEnum):
    """How the vacancy presents a requirement."""

    ESSENTIAL = "essential"
    DESIRABLE = "desirable"
    UNCLEAR = "unclear"


class CoverageStatus(StrEnum):
    """Permitted evidence-coverage assessments."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    UNCERTAIN = "uncertain"


class ChangeDecision(StrEnum):
    """How a proposed CV change should be handled."""

    ADD = "add"
    EXPAND = "expand"
    REWRITE = "rewrite"
    REORDER = "reorder"
    REMOVE = "remove"
    KEEP = "keep"
    EXCLUDE = "exclude"


class AnalysisRequest(ContractModel):
    """Pasted-text inputs for the first usable analysis endpoint."""

    candidate_cv: str = Field(min_length=50, max_length=50_000)
    job_description: str = Field(min_length=50, max_length=50_000)
    supporting_evidence: str | None = Field(
        default=None,
        max_length=50_000,
    )


class Citation(ContractModel):
    """A precise reference to candidate-controlled evidence."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    source_kind: SourceKind
    quote: str = Field(min_length=1, max_length=1_000)


class JobRequirement(ContractModel):
    """A requirement extracted from the supplied job description."""

    requirement_id: str = Field(pattern=r"^req-[0-9]{3,}$")
    priority: RequirementPriority
    source_text: str = Field(min_length=1, max_length=2_000)


class RequirementAssessment(ContractModel):
    """Evidence coverage for one job requirement."""

    requirement: JobRequirement
    status: CoverageStatus
    rationale: str = Field(min_length=1, max_length=2_000)
    citations: list[Citation] = Field(default_factory=list)
    clarification_question: str | None = Field(default=None, max_length=1_000)

    @model_validator(mode="after")
    def supported_assessments_require_evidence(self) -> RequirementAssessment:
        """Prevent positive coverage labels without candidate evidence."""

        positive = {
            CoverageStatus.SUPPORTED,
            CoverageStatus.PARTIALLY_SUPPORTED,
        }
        if self.status in positive and not self.citations:
            raise ValueError("supported assessments require at least one citation")
        return self


class ChangeSuggestion(ContractModel):
    """One explainable proposed change to the candidate's CV."""

    change_id: str = Field(pattern=r"^change-[0-9]{3,}$")
    target: str = Field(min_length=1, max_length=200)
    decision: ChangeDecision
    original_text: str | None = Field(default=None, max_length=5_000)
    suggested_text: str | None = Field(default=None, max_length=5_000)
    reason: str = Field(min_length=1, max_length=2_000)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def factual_additions_require_evidence(self) -> ChangeSuggestion:
        """Require evidence whenever wording is added or rewritten."""

        evidence_required = {
            ChangeDecision.ADD,
            ChangeDecision.EXPAND,
            ChangeDecision.REWRITE,
        }
        if self.decision in evidence_required and not self.citations:
            raise ValueError("added or rewritten wording requires a citation")
        return self


class AnalysisResponse(ContractModel):
    """Complete reviewable output from one analysis run."""

    analysis_id: str = Field(pattern=r"^analysis-[a-z0-9-]+$")
    requirements: list[RequirementAssessment]
    strengths: list[str]
    gaps: list[str]
    changes: list[ChangeSuggestion]
    unsupported_claim_warnings: list[str]
    aligned_cv_markdown: str = Field(min_length=1, max_length=100_000)
    review_required: bool = True


class ModelAnalysis(ContractModel):
    """Structured model output before application-owned metadata is attached."""

    requirements: list[RequirementAssessment]
    strengths: list[str]
    gaps: list[str]
    changes: list[ChangeSuggestion]
    unsupported_claim_warnings: list[str]
    aligned_cv_markdown: str = Field(min_length=1, max_length=100_000)
