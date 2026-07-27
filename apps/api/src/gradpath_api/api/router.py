"""Top-level API router composition."""

from fastapi import APIRouter

from gradpath_api.api.routes import health, meta

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(meta.router, prefix="/api/v1", tags=["meta"])
