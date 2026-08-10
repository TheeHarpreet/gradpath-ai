"""Explicit LangGraph workflow for evidence-grounded CV alignment."""

from __future__ import annotations

from typing import Any, Literal, TypedDict, cast
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from gradpath_api.application.input_security import secure_analysis_request
from gradpath_api.application.requirements import extract_requirements
from gradpath_api.application.retrievers import EvidenceRetriever
from gradpath_api.application.sources import build_source_catalog
from gradpath_api.application.validation import (
    AnalysisValidationError,
    validate_model_analysis,
)
from gradpath_api.application.workflow_repository import WorkflowRepository
from gradpath_api.domain.analysis import AnalysisRequest, CoverageStatus
from gradpath_api.domain.context import AnalysisContext
from gradpath_api.domain.workflow import (
    ClarificationQuestion,
    ClarificationSubmission,
    ReviewSubmission,
    WorkflowResponse,
    WorkflowState,
    WorkflowStatus,
    expected_change_ids,
)
from gradpath_api.infrastructure.ai.base import AnalysisProvider, ModelProviderError


class WorkflowConflictError(ValueError):
    """A resume request is invalid for the workflow's current state."""


class WorkflowGraphState(TypedDict, total=False):
    """LangGraph's mutable representation of the domain snapshot."""

    snapshot: WorkflowState
    entrypoint: Literal["start", "clarification", "review"]
    review: ReviewSubmission


class AlignmentWorkflowService:
    """Start and resume bounded workflows while persisting every pause."""

    def __init__(
        self,
        *,
        provider: AnalysisProvider,
        retriever: EvidenceRetriever,
        repository: WorkflowRepository,
        max_retries: int = 2,
        max_clarification_rounds: int = 1,
    ) -> None:
        self._provider = provider
        self._retriever = retriever
        self._repository = repository
        self._max_retries = max_retries
        self._max_clarification_rounds = max_clarification_rounds
        self._graph = self._build_graph()

    async def start(self, request: AnalysisRequest) -> WorkflowResponse:
        request, redactions = secure_analysis_request(request)
        state = WorkflowState(
            workflow_id=f"workflow-{uuid4().hex}",
            request=request,
            max_retries=self._max_retries,
            events=["workflow_started"],
            privacy_redactions=redactions.total,
        )
        if redactions.total:
            state.events.append("personal_data_redacted")
        result = await self._graph.ainvoke({"snapshot": state, "entrypoint": "start"})
        return await self._save_and_respond(result)

    async def get(self, workflow_id: str) -> WorkflowResponse:
        return WorkflowResponse.from_state(await self._repository.get(workflow_id))

    async def delete(self, workflow_id: str) -> None:
        """Remove candidate-controlled workflow data from the active store."""

        await self._repository.delete(workflow_id)

    async def clarify(
        self,
        workflow_id: str,
        submission: ClarificationSubmission,
    ) -> WorkflowResponse:
        state = await self._repository.get(workflow_id)
        if state.status is not WorkflowStatus.AWAITING_CLARIFICATION:
            raise WorkflowConflictError("Workflow is not awaiting clarification.")

        expected = {item.requirement_id for item in state.clarification_questions}
        received = {item.requirement_id for item in submission.answers}
        if received != expected or len(received) != len(submission.answers):
            raise WorkflowConflictError(
                "Submit exactly one answer for every clarification question."
            )

        additions = [
            f"Requirement {item.requirement_id}: {item.answer}"
            for item in submission.answers
            if item.answer
        ]
        existing = state.request.supporting_evidence
        combined = "\n\n".join(part for part in [existing, *additions] if part)
        state.request = state.request.model_copy(
            update={"supporting_evidence": combined or None}
        )
        state.clarification_questions = []
        state.clarification_rounds += 1
        state.status = WorkflowStatus.RUNNING
        state.events.append("clarification_received")
        result = await self._graph.ainvoke(
            {"snapshot": state, "entrypoint": "clarification"}
        )
        return await self._save_and_respond(result)

    async def review(
        self,
        workflow_id: str,
        submission: ReviewSubmission,
    ) -> WorkflowResponse:
        state = await self._repository.get(workflow_id)
        if state.status is not WorkflowStatus.AWAITING_REVIEW or state.analysis is None:
            raise WorkflowConflictError("Workflow is not awaiting review.")

        expected = expected_change_ids(state.analysis.changes)
        received = {item.change_id for item in submission.decisions}
        if received != expected or len(received) != len(submission.decisions):
            raise WorkflowConflictError(
                "Submit exactly one decision for every proposed change."
            )

        result = await self._graph.ainvoke(
            {"snapshot": state, "entrypoint": "review", "review": submission}
        )
        return await self._save_and_respond(result)

    def _build_graph(self) -> Any:
        graph = StateGraph(WorkflowGraphState)
        graph.add_node("prepare", self._prepare)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("analyse", self._analyse)
        graph.add_node("verify", self._verify)
        graph.add_node("pause_clarification", self._pause_clarification)
        graph.add_node("pause_review", self._pause_review)
        graph.add_node("assemble", self._assemble)
        graph.add_conditional_edges(START, self._entrypoint)
        graph.add_edge("prepare", "retrieve")
        graph.add_edge("retrieve", "analyse")
        graph.add_edge("analyse", "verify")
        graph.add_conditional_edges("verify", self._after_verify)
        graph.add_edge("pause_clarification", END)
        graph.add_edge("pause_review", END)
        graph.add_edge("assemble", END)
        return graph.compile(name="gradpath-alignment")

    @staticmethod
    def _entrypoint(
        state: WorkflowGraphState,
    ) -> Literal["prepare", "retrieve", "assemble"]:
        if state["entrypoint"] == "start":
            return "prepare"
        if state["entrypoint"] == "clarification":
            return "retrieve"
        return "assemble"

    @staticmethod
    def _prepare(state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        snapshot.requirements = extract_requirements(snapshot.request.job_description)
        snapshot.source_catalog = build_source_catalog(snapshot.request)
        snapshot.events.append("inputs_prepared")
        return {"snapshot": snapshot}

    async def _retrieve(self, state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        snapshot.source_catalog = build_source_catalog(snapshot.request)
        snapshot.retrieved_evidence = await self._retriever.retrieve(
            snapshot.requirements,
            snapshot.source_catalog,
        )
        snapshot.events.append("evidence_retrieved")
        return {"snapshot": snapshot}

    async def _analyse(self, state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        try:
            snapshot.analysis = await self._provider.analyse(
                AnalysisContext(
                    request=snapshot.request,
                    requirements=snapshot.requirements,
                    source_catalog=snapshot.source_catalog,
                    retrieved_evidence=snapshot.retrieved_evidence,
                )
            )
            snapshot.failure_code = None
            snapshot.events.append("agent_analysis_completed")
        except ModelProviderError:
            snapshot.analysis = None
            snapshot.failure_code = "provider_failure"
            snapshot.events.append("provider_failure")
        return {"snapshot": snapshot}

    @staticmethod
    def _verify(state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        if snapshot.analysis is not None:
            try:
                validate_model_analysis(
                    snapshot.analysis,
                    requirements=snapshot.requirements,
                    catalog=snapshot.source_catalog,
                )
                snapshot.failure_code = None
                snapshot.events.append("analysis_verified")
            except AnalysisValidationError:
                snapshot.analysis = None
                snapshot.failure_code = "unsafe_model_output"
                snapshot.events.append("unsafe_model_output")
        if snapshot.failure_code is not None:
            snapshot.retry_count += 1
        return {"snapshot": snapshot}

    def _after_verify(
        self, state: WorkflowGraphState
    ) -> Literal["analyse", "pause_clarification", "pause_review", "assemble"]:
        snapshot = state["snapshot"]
        if snapshot.failure_code is not None:
            if snapshot.retry_count <= snapshot.max_retries:
                snapshot.events.append("retry_scheduled")
                return "analyse"
            snapshot.status = WorkflowStatus.FAILED
            snapshot.events.append("retry_limit_exceeded")
            return "assemble"

        assert snapshot.analysis is not None
        questions = [
            ClarificationQuestion(
                requirement_id=item.requirement.requirement_id,
                question=item.clarification_question,
            )
            for item in snapshot.analysis.requirements
            if item.status is CoverageStatus.UNCERTAIN and item.clarification_question
        ]
        if questions and snapshot.clarification_rounds < self._max_clarification_rounds:
            snapshot.clarification_questions = questions
            return "pause_clarification"
        return "pause_review"

    @staticmethod
    def _pause_clarification(state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        snapshot.status = WorkflowStatus.AWAITING_CLARIFICATION
        snapshot.events.append("awaiting_clarification")
        return {"snapshot": snapshot}

    @staticmethod
    def _pause_review(state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        snapshot.status = WorkflowStatus.AWAITING_REVIEW
        snapshot.events.append("awaiting_review")
        return {"snapshot": snapshot}

    @staticmethod
    def _assemble(state: WorkflowGraphState) -> WorkflowGraphState:
        snapshot = state["snapshot"]
        if snapshot.status is WorkflowStatus.FAILED:
            return {"snapshot": snapshot}
        review = state.get("review")
        if review is None:
            snapshot.status = WorkflowStatus.FAILED
            snapshot.failure_code = "missing_review"
            snapshot.events.append("workflow_failed")
            return {"snapshot": snapshot}
        snapshot.review_decisions = review.decisions
        snapshot.approved_cv_markdown = review.approved_cv_markdown
        snapshot.status = WorkflowStatus.COMPLETED
        snapshot.events.append("human_review_applied")
        snapshot.events.append("workflow_completed")
        return {"snapshot": snapshot}

    async def _save_and_respond(self, result: dict[str, Any]) -> WorkflowResponse:
        state = cast(WorkflowState, result["snapshot"])
        await self._repository.save(state)
        return WorkflowResponse.from_state(state)
