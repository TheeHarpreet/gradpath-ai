"""Retrieval strategies used by the analysis application service."""

from __future__ import annotations

import math
from typing import Protocol
from uuid import uuid4

from gradpath_api.application.reranking import EvidenceReranker, IdentityReranker
from gradpath_api.application.retrieval import retrieve_evidence
from gradpath_api.domain.analysis import JobRequirement
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk
from gradpath_api.infrastructure.embeddings.base import (
    EmbeddingBatch,
    EmbeddingProvider,
    EmbeddingProviderError,
)
from gradpath_api.infrastructure.retrieval.base import (
    RetrievalIndex,
    RetrievalIndexError,
)


class EvidenceRetrievalError(RuntimeError):
    """Raised when the evidence retrieval pipeline cannot complete safely."""


class EvidenceRetriever(Protocol):
    """Return ranked candidate evidence for each extracted requirement."""

    async def retrieve(
        self,
        requirements: list[JobRequirement],
        catalog: list[SourceChunk],
    ) -> dict[str, list[RetrievedEvidence]]:
        """Retrieve evidence without changing source text or identifiers."""

        ...


class LexicalEvidenceRetriever:
    """Async adapter around the original transparent Step 3 baseline."""

    def __init__(self, *, limit_per_requirement: int = 3) -> None:
        self._limit = limit_per_requirement

    async def retrieve(
        self,
        requirements: list[JobRequirement],
        catalog: list[SourceChunk],
    ) -> dict[str, list[RetrievedEvidence]]:
        """Return the unchanged lexical baseline ranking."""

        return retrieve_evidence(
            requirements,
            catalog,
            limit_per_requirement=self._limit,
        )


class HybridEvidenceRetriever:
    """Fuse lexical and dense rankings with Reciprocal Rank Fusion."""

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        limit_per_requirement: int = 3,
        candidate_limit: int = 8,
        rrf_k: int = 60,
        index: RetrievalIndex | None = None,
        reranker: EvidenceReranker | None = None,
    ) -> None:
        if limit_per_requirement < 1 or candidate_limit < limit_per_requirement:
            raise ValueError("Retrieval limits are inconsistent.")
        if rrf_k < 1:
            raise ValueError("RRF constant must be positive.")
        self._embedding_provider = embedding_provider
        self._limit = limit_per_requirement
        self._candidate_limit = candidate_limit
        self._rrf_k = rrf_k
        self._index = index
        self._reranker = reranker or IdentityReranker()

    async def retrieve(
        self,
        requirements: list[JobRequirement],
        catalog: list[SourceChunk],
    ) -> dict[str, list[RetrievedEvidence]]:
        """Embed once, rank both channels, and return fused evidence."""

        if not requirements:
            return {}
        if not catalog:
            return {item.requirement_id: [] for item in requirements}

        texts = [chunk.text for chunk in catalog] + [
            requirement.source_text for requirement in requirements
        ]
        try:
            embeddings = await self._embedding_provider.embed(texts)
        except EmbeddingProviderError as exc:
            raise EvidenceRetrievalError("Embedding retrieval failed.") from exc
        if len(embeddings.vectors) != len(texts):
            raise ValueError("Embedding provider did not preserve input count.")

        chunk_vectors = embeddings.vectors[: len(catalog)]
        query_vectors = embeddings.vectors[len(catalog) :]
        if self._index is not None:
            return await self._retrieve_from_index(
                requirements,
                catalog,
                chunk_vectors,
                query_vectors,
                embeddings,
            )

        return self._retrieve_in_memory(
            requirements,
            catalog,
            chunk_vectors,
            query_vectors,
        )

    def _retrieve_in_memory(
        self,
        requirements: list[JobRequirement],
        catalog: list[SourceChunk],
        chunk_vectors: list[list[float]],
        query_vectors: list[list[float]],
    ) -> dict[str, list[RetrievedEvidence]]:
        """Execute the same ranking algorithm without persistence for tests."""

        lexical = retrieve_evidence(
            requirements,
            catalog,
            limit_per_requirement=self._candidate_limit,
        )

        output: dict[str, list[RetrievedEvidence]] = {}
        for requirement, query_vector in zip(
            requirements,
            query_vectors,
            strict=True,
        ):
            semantic_pairs = sorted(
                (
                    (chunk, _cosine_similarity(query_vector, vector))
                    for chunk, vector in zip(catalog, chunk_vectors, strict=True)
                ),
                key=lambda item: (-item[1], item[0].source_id),
            )[: self._candidate_limit]
            semantic = [
                RetrievedEvidence(
                    requirement_id=requirement.requirement_id,
                    source_id=chunk.source_id,
                    score=max(score, 0.00000001),
                    text=chunk.text,
                    semantic_rank=rank,
                    semantic_score=round(score, 6),
                )
                for rank, (chunk, score) in enumerate(semantic_pairs, start=1)
            ]
            output[requirement.requirement_id] = self._fuse(
                requirement,
                catalog,
                lexical[requirement.requirement_id],
                semantic,
            )
        return output

    async def _retrieve_from_index(
        self,
        requirements: list[JobRequirement],
        catalog: list[SourceChunk],
        chunk_vectors: list[list[float]],
        query_vectors: list[list[float]],
        embeddings: EmbeddingBatch,
    ) -> dict[str, list[RetrievedEvidence]]:
        """Use PostgreSQL channels and always delete the temporary scope."""

        assert self._index is not None
        scope_id = f"retrieval-{uuid4().hex}"
        chunk_embeddings = EmbeddingBatch(
            model=embeddings.model,
            dimensions=embeddings.dimensions,
            vectors=chunk_vectors,
            input_tokens=None,
        )
        try:
            await self._index.replace(scope_id, catalog, chunk_embeddings)
        except RetrievalIndexError as exc:
            raise EvidenceRetrievalError("Retrieval indexing failed.") from exc
        try:
            output: dict[str, list[RetrievedEvidence]] = {}
            for requirement, query_vector in zip(
                requirements,
                query_vectors,
                strict=True,
            ):
                try:
                    lexical = await self._index.lexical_search(
                        scope_id,
                        requirement,
                        limit=self._candidate_limit,
                    )
                    semantic = await self._index.semantic_search(
                        scope_id,
                        requirement,
                        query_vector,
                        limit=self._candidate_limit,
                    )
                except RetrievalIndexError as exc:
                    raise EvidenceRetrievalError(
                        "Evidence retrieval query failed."
                    ) from exc
                output[requirement.requirement_id] = self._fuse(
                    requirement,
                    catalog,
                    lexical,
                    semantic,
                )
            return output
        finally:
            try:
                await self._index.delete(scope_id)
            except RetrievalIndexError as exc:
                raise EvidenceRetrievalError("Retrieval cleanup failed.") from exc

    def _fuse(
        self,
        requirement: JobRequirement,
        catalog: list[SourceChunk],
        lexical: list[RetrievedEvidence],
        semantic: list[RetrievedEvidence],
    ) -> list[RetrievedEvidence]:
        """Fuse two bounded rankings and retain their diagnostic ranks."""

        lexical_rank = {item.source_id: rank for rank, item in enumerate(lexical, 1)}
        semantic_rank = {item.source_id: rank for rank, item in enumerate(semantic, 1)}
        semantic_score = {
            item.source_id: item.semantic_score or item.score for item in semantic
        }
        candidates = set(lexical_rank) | set(semantic_rank)
        by_id = {chunk.source_id: chunk for chunk in catalog}
        fused = [
            RetrievedEvidence(
                requirement_id=requirement.requirement_id,
                source_id=source_id,
                score=round(
                    _rrf_score(
                        lexical_rank.get(source_id),
                        semantic_rank.get(source_id),
                        k=self._rrf_k,
                    ),
                    8,
                ),
                text=by_id[source_id].text,
                lexical_rank=lexical_rank.get(source_id),
                semantic_rank=semantic_rank.get(source_id),
                semantic_score=round(semantic_score.get(source_id, 0.0), 6),
            )
            for source_id in candidates
        ]
        fused.sort(key=lambda item: (-item.score, item.source_id))
        return self._reranker.rerank(
            requirement,
            fused,
            limit=self._limit,
        )


def _rrf_score(
    lexical_rank: int | None,
    semantic_rank: int | None,
    *,
    k: int,
) -> float:
    """Combine available ranks without mixing their underlying score scales."""

    return sum(
        1 / (k + rank) for rank in (lexical_rank, semantic_rank) if rank is not None
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity and reject zero or mismatched vectors."""

    if len(left) != len(right):
        raise ValueError("Embedding dimensions do not match.")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Embedding vectors must have non-zero magnitude.")
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )
