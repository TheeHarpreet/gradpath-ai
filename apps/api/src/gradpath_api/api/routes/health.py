"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Machine-readable operational health response."""

    status: Literal["ok", "ready"]


@router.get("/live", response_model=HealthResponse, summary="Liveness probe")
async def liveness() -> HealthResponse:
    """Confirm that the application process can serve requests."""

    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness() -> HealthResponse:
    """Confirm that configured startup requirements currently pass.

    Database and object-store checks will be added when those adapters exist.
    """

    return HealthResponse(status="ready")
