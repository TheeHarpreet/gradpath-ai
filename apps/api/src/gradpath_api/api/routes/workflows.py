"""Start, inspect, and resume agentic CV-alignment workflows."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from gradpath_api.application.alignment_workflow import (
    AlignmentWorkflowService,
    WorkflowConflictError,
)
from gradpath_api.application.input_security import UnsafeInputError
from gradpath_api.application.requirements import RequirementExtractionError
from gradpath_api.application.retrievers import EvidenceRetrievalError
from gradpath_api.application.sources import SourceCatalogError
from gradpath_api.application.workflow_repository import WorkflowNotFoundError
from gradpath_api.domain.analysis import AnalysisRequest
from gradpath_api.domain.workflow import (
    ClarificationSubmission,
    ReviewSubmission,
    WorkflowResponse,
)

router = APIRouter()


def get_workflow_service(request: Request) -> AlignmentWorkflowService:
    """Resolve the workflow service without exposing provider credentials."""

    service: AlignmentWorkflowService | None = request.app.state.workflow_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The workflow provider is not configured.",
        )
    return service


WorkflowServiceDependency = Annotated[
    AlignmentWorkflowService, Depends(get_workflow_service)
]


@router.post("/workflows", response_model=WorkflowResponse)
async def start_workflow(
    payload: AnalysisRequest,
    service: WorkflowServiceDependency,
) -> WorkflowResponse:
    """Start an analysis and pause when candidate input is required."""

    try:
        return await service.start(payload)
    except (RequirementExtractionError, SourceCatalogError, UnsafeInputError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except EvidenceRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The workflow could not retrieve candidate evidence.",
        ) from exc


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    service: WorkflowServiceDependency,
) -> WorkflowResponse:
    """Return the current safe workflow snapshot."""

    try:
        return await service.get(workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    service: WorkflowServiceDependency,
) -> None:
    """Permanently remove the active workflow snapshot."""

    try:
        await service.delete(workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post(
    "/workflows/{workflow_id}/clarifications",
    response_model=WorkflowResponse,
)
async def submit_clarification(
    workflow_id: str,
    payload: ClarificationSubmission,
    service: WorkflowServiceDependency,
) -> WorkflowResponse:
    """Resume a paused workflow with candidate-controlled detail."""

    try:
        return await service.clarify(workflow_id, payload)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except WorkflowConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/workflows/{workflow_id}/review", response_model=WorkflowResponse)
async def submit_review(
    workflow_id: str,
    payload: ReviewSubmission,
    service: WorkflowServiceDependency,
) -> WorkflowResponse:
    """Complete a workflow only with explicit candidate decisions and CV text."""

    try:
        return await service.review(workflow_id, payload)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except WorkflowConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
