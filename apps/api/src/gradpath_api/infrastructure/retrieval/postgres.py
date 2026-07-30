"""PostgreSQL full-text and pgvector retrieval index."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from gradpath_api.domain.analysis import JobRequirement
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk
from gradpath_api.infrastructure.embeddings.base import EmbeddingBatch
from gradpath_api.infrastructure.retrieval.base import RetrievalIndexError


class PostgresRetrievalIndex:
    """Persist analysis-scoped chunks and query both retrieval channels."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        connection = psycopg.connect(self._database_url, row_factory=dict_row)
        try:
            register_vector(connection)
            yield connection
        finally:
            connection.close()

    async def replace(
        self,
        scope_id: str,
        catalog: list[SourceChunk],
        embeddings: EmbeddingBatch,
    ) -> None:
        """Atomically replace all chunks for one analysis scope."""

        try:
            await asyncio.to_thread(self._replace, scope_id, catalog, embeddings)
        except psycopg.Error as exc:
            raise RetrievalIndexError("PostgreSQL retrieval write failed.") from exc

    def _replace(
        self,
        scope_id: str,
        catalog: list[SourceChunk],
        embeddings: EmbeddingBatch,
    ) -> None:
        if len(catalog) != len(embeddings.vectors):
            raise ValueError("Chunk and embedding counts do not match.")
        rows = [
            (
                scope_id,
                chunk.source_id,
                chunk.source_kind.value,
                chunk.text,
                embeddings.model,
                embeddings.dimensions,
                np.asarray(vector, dtype=np.float32),
            )
            for chunk, vector in zip(catalog, embeddings.vectors, strict=True)
        ]
        with self._connection() as connection, connection.transaction():
            connection.execute(
                "DELETE FROM retrieval_chunks WHERE scope_id = %s",
                (scope_id,),
            )
            connection.cursor().executemany(
                """
                INSERT INTO retrieval_chunks (
                    scope_id,
                    source_id,
                    source_kind,
                    content,
                    embedding_model,
                    embedding_dimensions,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )

    async def lexical_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Rank exact terms with PostgreSQL cover-density text ranking."""

        try:
            return await asyncio.to_thread(
                self._lexical_search,
                scope_id,
                requirement,
                limit,
            )
        except psycopg.Error as exc:
            raise RetrievalIndexError("PostgreSQL lexical search failed.") from exc

    def _lexical_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        limit: int,
    ) -> list[RetrievedEvidence]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    source_id,
                    content,
                    ts_rank_cd(
                        search_vector,
                        websearch_to_tsquery('english', %s)
                    ) AS score
                FROM retrieval_chunks
                WHERE scope_id = %s
                  AND search_vector @@ websearch_to_tsquery('english', %s)
                ORDER BY score DESC, source_id ASC
                LIMIT %s
                """,
                (
                    requirement.source_text,
                    scope_id,
                    requirement.source_text,
                    limit,
                ),
            ).fetchall()
        return [
            RetrievedEvidence(
                requirement_id=requirement.requirement_id,
                source_id=str(row["source_id"]),
                score=float(row["score"]),
                text=str(row["content"]),
                lexical_rank=rank,
            )
            for rank, row in enumerate(rows, start=1)
        ]

    async def semantic_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        query_vector: list[float],
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Rank meaning with exact pgvector cosine distance."""

        try:
            return await asyncio.to_thread(
                self._semantic_search,
                scope_id,
                requirement,
                query_vector,
                limit,
            )
        except psycopg.Error as exc:
            raise RetrievalIndexError("PostgreSQL vector search failed.") from exc

    def _semantic_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        query_vector: list[float],
        limit: int,
    ) -> list[RetrievedEvidence]:
        vector = np.asarray(query_vector, dtype=np.float32)
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    source_id,
                    content,
                    1 - (embedding <=> %s) AS score
                FROM retrieval_chunks
                WHERE scope_id = %s
                  AND embedding_dimensions = %s
                ORDER BY embedding <=> %s, source_id ASC
                LIMIT %s
                """,
                (vector, scope_id, len(query_vector), vector, limit),
            ).fetchall()
        return [
            RetrievedEvidence(
                requirement_id=requirement.requirement_id,
                source_id=str(row["source_id"]),
                score=max(float(row["score"]), 0.00000001),
                text=str(row["content"]),
                semantic_rank=rank,
                semantic_score=float(row["score"]),
            )
            for rank, row in enumerate(rows, start=1)
        ]

    async def delete(self, scope_id: str) -> None:
        """Remove candidate text and vectors for one completed analysis."""

        try:
            await asyncio.to_thread(self._delete, scope_id)
        except psycopg.Error as exc:
            raise RetrievalIndexError("PostgreSQL retrieval deletion failed.") from exc

    def _delete(self, scope_id: str) -> None:
        with self._connection() as connection, connection.transaction():
            connection.execute(
                "DELETE FROM retrieval_chunks WHERE scope_id = %s",
                (scope_id,),
            )
