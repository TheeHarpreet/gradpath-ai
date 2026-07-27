"""FastAPI application factory and command-line entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gradpath_api.api.router import api_router
from gradpath_api.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an isolated application instance for runtime or tests."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        docs_url="/docs" if resolved_settings.enable_api_docs else None,
        redoc_url="/redoc" if resolved_settings.enable_api_docs else None,
        openapi_url="/openapi.json" if resolved_settings.enable_api_docs else None,
    )
    app.state.settings = resolved_settings
    app.include_router(api_router)

    if resolved_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in resolved_settings.cors_origins],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    return app


app = create_app()


def main() -> None:
    """Run the development server through the package script."""

    import uvicorn

    uvicorn.run(
        "gradpath_api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
