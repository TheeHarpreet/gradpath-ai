"""Typed state and API contracts for the resumable alignment workflow."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from gradpath_api.domain.analysis import (
    AnalysisRequest,
    ChangeSuggestion,
    ContractModel,
    JobRequirement,
    ModelAnalysis,
)
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk


class WorkflowStatus(StrEnum):
    """Externally visible lifecycle states for an alignment workflow."""

    RUNNING = "running"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewAction(StrEnum):
    """Candidate decisions for an individual generated suggestion."""

    ACCEPT = "accept"
    EDIT = "edit"
    REJECT = "reject"


class ClarificationQuestion(ContractModel):
    """A question tied to one uncertain vacancy requirement."""

    requirement_id: str = Field(pattern=r"^req-[0-9]{3,}$")
    question: str = Field(min_length=1, max_length=1_000)


class ClarificationAnswer(ContractModel):
    """Candidate-controlled evidence supplied after a workflow pause."""

    requirement_id: str = Field(pattern=r"^req-[0-9]{3,}$")
    answer: str | None = Field(default=None, max_length=5_000)


class ClarificationSubmission(ContractModel):
    """Answers for every question currently awaiting clarification."""

    answers: list[ClarificationAnswer] = Field(min_length=1)


class ChangeReview(ContractModel):
    """Candidate decision for one model-proposed CV change."""

    change_id: str = Field(pattern=r"^change-[0-9]{3,}$")
    action: ReviewAction
    edited_text: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def edits_require_text(self) -> ChangeReview:
        """An edit is not meaningful unless replacement wording is supplied."""

        if self.action is ReviewAction.EDIT and not self.edited_text:
            raise ValueError("edited decisions require edited_text")
        if self.action is not ReviewAction.EDIT and self.edited_text is not None:
            raise ValueError("edited_text is only valid for edit decisions")
        return self


class ReviewSubmission(ContractModel):
    """Human approval decisions and the exact CV the candidate approves."""

    decisions: list[ChangeReview]
    approved_cv_markdown: str = Field(min_length=1, max_length=100_000)


class WorkflowState(ContractModel):
    """Complete serializable state owned by the application workflow."""

    workflow_id: str = Field(pattern=r"^workflow-[a-z0-9-]+$")
    status: WorkflowStatus = WorkflowStatus.RUNNING
    request: AnalysisRequest
    requirements: list[JobRequirement] = Field(default_factory=list)
    source_catalog: list[SourceChunk] = Field(default_factory=list)
    retrieved_evidence: dict[str, list[RetrievedEvidence]] = Field(default_factory=dict)
    analysis: ModelAnalysis | None = None
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)
    clarification_rounds: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=2, ge=0, le=5)
    failure_code: str | None = None
    review_decisions: list[ChangeReview] = Field(default_factory=list)
    approved_cv_markdown: str | None = Field(default=None, max_length=100_000)
    events: list[str] = Field(default_factory=list)


class WorkflowResponse(ContractModel):
    """Safe client view of a workflow snapshot."""

    workflow_id: str
    status: WorkflowStatus
    retry_count: int
    clarification_questions: list[ClarificationQuestion]
    analysis: ModelAnalysis | None
    review_decisions: list[ChangeReview]
    approved_cv_markdown: str | None
    events: list[str]

    @classmethod
    def from_state(cls, state: WorkflowState) -> WorkflowResponse:
        """Hide internal evidence packages while retaining useful progress."""

        return cls(
            workflow_id=state.workflow_id,
            status=state.status,
            retry_count=state.retry_count,
            clarification_questions=state.clarification_questions,
            analysis=state.analysis,
            review_decisions=state.review_decisions,
            approved_cv_markdown=state.approved_cv_markdown,
            events=state.events,
        )


def expected_change_ids(changes: list[ChangeSuggestion]) -> set[str]:
    """Return the identifiers that must receive an explicit review decision."""

    return {change.change_id for change in changes}
