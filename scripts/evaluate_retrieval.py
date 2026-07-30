"""Evaluate lexical or live hybrid retrieval on a committed fictional case."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from gradpath_api.application.requirements import extract_requirements
from gradpath_api.application.reranking import EvidenceAwareReranker
from gradpath_api.application.retrieval_evaluation import evaluate_retrieval
from gradpath_api.application.retrievers import (
    HybridEvidenceRetriever,
    LexicalEvidenceRetriever,
)
from gradpath_api.application.sources import build_source_catalog
from gradpath_api.core.config import Settings
from gradpath_api.domain.analysis import AnalysisRequest
from gradpath_api.infrastructure.embeddings.base import EmbeddingBatch
from gradpath_api.infrastructure.embeddings.openai_provider import (
    OpenAIEmbeddingProvider,
)
from gradpath_api.infrastructure.retrieval.postgres import PostgresRetrievalIndex
from openai import AsyncOpenAI


class UsageRecordingEmbeddingProvider:
    """Record safe token totals without retaining texts or vectors."""

    def __init__(self, provider: OpenAIEmbeddingProvider) -> None:
        self._provider = provider
        self.input_tokens = 0

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        batch = await self._provider.embed(texts)
        self.input_tokens += batch.input_tokens or 0
        return batch


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("lexical", "hybrid"),
        required=True,
    )
    parser.add_argument(
        "--case",
        default="evals/cases/graduate-fullstack-001",
    )
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Use migrated PostgreSQL channels for hybrid retrieval.",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Apply the deterministic evidence-aware reranker.",
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> None:
    case = Path(args.case)
    request = AnalysisRequest(
        candidate_cv=(case / "candidate-cv.md").read_text(encoding="utf-8"),
        job_description=(case / "job-description.md").read_text(encoding="utf-8"),
        supporting_evidence=(case / "supporting-evidence.md").read_text(
            encoding="utf-8"
        ),
    )
    expected_payload: dict[str, Any] = json.loads(
        (case / "expected.json").read_text(encoding="utf-8")
    )
    expected = {
        str(item["id"]): {str(value) for value in item["evidence_ids"]}
        for item in expected_payload["requirements"]
    }
    requirements = extract_requirements(request.job_description)
    catalog = build_source_catalog(request)
    settings = Settings()

    if args.mode == "lexical":
        retriever = LexicalEvidenceRetriever(
            limit_per_requirement=settings.retrieval_limit
        )
        model = None
        usage_recorder = None
    else:
        if settings.openai_api_key is None:
            raise RuntimeError("OPENAI_API_KEY is required for hybrid evaluation.")
        usage_recorder = UsageRecordingEmbeddingProvider(
            OpenAIEmbeddingProvider(
                client=AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value()),
                model=settings.embedding_model,
                dimensions=settings.embedding_dimensions,
                batch_size=settings.embedding_batch_size,
            )
        )
        index = (
            PostgresRetrievalIndex(str(settings.database_url))
            if args.postgres
            else None
        )
        retriever = HybridEvidenceRetriever(
            embedding_provider=usage_recorder,
            limit_per_requirement=settings.retrieval_limit,
            candidate_limit=settings.retrieval_candidate_limit,
            rrf_k=settings.retrieval_rrf_k,
            index=index,
            reranker=EvidenceAwareReranker() if args.rerank else None,
        )
        model = settings.embedding_model

    retrieved = await retriever.retrieve(requirements, catalog)
    metrics = evaluate_retrieval(retrieved, expected)
    safe_rankings = {
        requirement_id: [result.source_id for result in results]
        for requirement_id, results in retrieved.items()
    }
    print(
        json.dumps(
            {
                "case_id": expected_payload["case_id"],
                "mode": args.mode,
                "storage": "postgres" if args.postgres else "memory",
                "embedding_model": model,
                "embedding_input_tokens": (
                    usage_recorder.input_tokens if usage_recorder else None
                ),
                "reranker": ("evidence-aware-v1" if args.rerank else None),
                "top_k": settings.retrieval_limit,
                "metrics": metrics.model_dump(),
                "rankings": safe_rankings,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(_run(_arguments()))
