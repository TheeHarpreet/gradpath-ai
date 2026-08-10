"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Machine-readable operational health response."""

    status: Literal["ok", "ready", "degraded"]


@router.get("/live", response_model=HealthResponse, summary="Liveness probe")
async def liveness() -> HealthResponse:
    """Confirm that the application process can serve requests."""

    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness(request: Request, response: Response) -> HealthResponse:
    """Confirm that configured startup requirements currently pass.

    A production process without its paid analysis provider is not ready to
    receive traffic. Database checks are added with durable persistence.
    """

    settings = request.app.state.settings
    if (
        settings.environment == "production"
        and request.app.state.workflow_service is None
    ):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded")
    return HealthResponse(status="ready")
