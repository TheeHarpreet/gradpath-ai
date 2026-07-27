"""Evidence-grounded CV analysis endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from gradpath_api.application.analysis_service import AnalysisService
from gradpath_api.application.requirements import RequirementExtractionError
from gradpath_api.application.validation import AnalysisValidationError
from gradpath_api.domain.analysis import AnalysisRequest, AnalysisResponse
from gradpath_api.infrastructure.ai.base import ModelProviderError

router = APIRouter()


def get_analysis_service(request: Request) -> AnalysisService:
    """Return the configured service without exposing provider credentials."""

    service: AnalysisService | None = request.app.state.analysis_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The analysis provider is not configured.",
        )
    return service


AnalysisServiceDependency = Annotated[AnalysisService, Depends(get_analysis_service)]


@router.post("/analyses", response_model=AnalysisResponse)
async def create_analysis(
    payload: AnalysisRequest,
    service: AnalysisServiceDependency,
) -> AnalysisResponse:
    """Analyse pasted text and return a cited, review-required CV draft."""

    try:
        return await service.analyse(payload)
    except RequirementExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except (AnalysisValidationError, ModelProviderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The analysis provider did not return a safe result.",
        ) from exc
