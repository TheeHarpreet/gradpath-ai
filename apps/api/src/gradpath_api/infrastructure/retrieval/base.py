"""Persistence contract for hybrid evidence retrieval."""

from __future__ import annotations

from typing import Protocol

from gradpath_api.domain.analysis import JobRequirement
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk
from gradpath_api.infrastructure.embeddings.base import EmbeddingBatch


class RetrievalIndexError(RuntimeError):
    """Raised when retrieval persistence is unavailable or inconsistent."""


class RetrievalIndex(Protocol):
    """Store and query one isolated set of candidate evidence chunks."""

    async def replace(
        self,
        scope_id: str,
        catalog: list[SourceChunk],
        embeddings: EmbeddingBatch,
    ) -> None:
        """Atomically replace all chunks for an isolated analysis scope."""

        ...

    async def lexical_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Return full-text candidates within the supplied scope."""

        ...

    async def semantic_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        query_vector: list[float],
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Return exact cosine candidates within the supplied scope."""

        ...

    async def delete(self, scope_id: str) -> None:
        """Delete chunks and derived vectors for one analysis scope."""

        ...
