"""Top-level API router composition."""

from fastapi import APIRouter

from gradpath_api.api.routes import analyses, documents, health, meta, workflows

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(meta.router, prefix="/api/v1", tags=["meta"])
api_router.include_router(analyses.router, prefix="/api/v1", tags=["analyses"])
api_router.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
api_router.include_router(documents.router, prefix="/api/v1", tags=["documents"])
