"""FastAPI application factory and command-line entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from gradpath_api.api.router import api_router
from gradpath_api.application.analysis_service import AnalysisService
from gradpath_api.application.reranking import EvidenceAwareReranker
from gradpath_api.application.retrievers import HybridEvidenceRetriever
from gradpath_api.core.config import Settings, get_settings
from gradpath_api.infrastructure.ai.openai_provider import OpenAIAnalysisProvider
from gradpath_api.infrastructure.embeddings.openai_provider import (
    OpenAIEmbeddingProvider,
)
from gradpath_api.infrastructure.retrieval.postgres import PostgresRetrievalIndex


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
    app.state.analysis_service = _create_analysis_service(resolved_settings)
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


def _create_analysis_service(settings: Settings) -> AnalysisService | None:
    """Create the real provider only when a local or deployed secret exists."""

    if settings.openai_api_key is None:
        return None
    client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
    provider = OpenAIAnalysisProvider(
        client=client,
        model=settings.openai_model,
        reasoning_effort=settings.openai_reasoning_effort,
        store=settings.openai_store_responses,
    )
    embedding_provider = OpenAIEmbeddingProvider(
        client=client,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
    )
    retriever = HybridEvidenceRetriever(
        embedding_provider=embedding_provider,
        limit_per_requirement=settings.retrieval_limit,
        candidate_limit=settings.retrieval_candidate_limit,
        rrf_k=settings.retrieval_rrf_k,
        index=PostgresRetrievalIndex(str(settings.database_url)),
        reranker=EvidenceAwareReranker(),
    )
    return AnalysisService(provider, retriever=retriever)


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
