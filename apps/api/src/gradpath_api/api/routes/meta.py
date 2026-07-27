"""Non-sensitive application metadata."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from gradpath_api.core.config import Settings

router = APIRouter()


class MetaResponse(BaseModel):
    """Public metadata used by clients and smoke tests."""

    name: str
    version: str
    environment: Literal["local", "test", "staging", "production"]


@router.get("/meta", response_model=MetaResponse)
async def metadata(request: Request) -> MetaResponse:
    """Return safe application identity data without secrets."""

    settings: Settings = request.app.state.settings
    return MetaResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
