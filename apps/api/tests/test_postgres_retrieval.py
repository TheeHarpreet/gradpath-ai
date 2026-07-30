"""Integration tests for PostgreSQL full-text and pgvector retrieval."""

import os

import pytest
from gradpath_api.core.config import Settings
from gradpath_api.domain.analysis import (
    JobRequirement,
    RequirementPriority,
    SourceKind,
)
from gradpath_api.domain.source import SourceChunk
from gradpath_api.infrastructure.embeddings.base import EmbeddingBatch
from gradpath_api.infrastructure.retrieval.postgres import PostgresRetrievalIndex

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.getenv("GRADPATH_RUN_POSTGRES_TESTS") != "1",
        reason="Set GRADPATH_RUN_POSTGRES_TESTS=1 to run PostgreSQL tests.",
    ),
]


def _requirement(requirement_id: str, text: str) -> JobRequirement:
    return JobRequirement(
        requirement_id=requirement_id,
        priority=RequirementPriority.ESSENTIAL,
        source_text=text,
    )


@pytest.mark.asyncio
async def test_postgres_index_searches_both_channels_and_deletes_scope() -> None:
    settings = Settings(_env_file=None, environment="test")
    index = PostgresRetrievalIndex(str(settings.database_url))
    scope_id = "integration-rag-scope"
    catalog = [
        SourceChunk(
            source_id="cv-actions",
            source_kind=SourceKind.CANDIDATE_CV,
            text="Configured GitHub Actions to run tests for every pull request.",
        ),
        SourceChunk(
            source_id="cv-database",
            source_kind=SourceKind.CANDIDATE_CV,
            text="Designed a normalized relational database schema.",
        ),
    ]
    embeddings = EmbeddingBatch(
        model="integration-fixture-v1",
        dimensions=3,
        vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    )
    lexical_requirement = _requirement("req-001", "GitHub Actions testing")
    semantic_requirement = _requirement("req-002", "Familiarity with CI/CD")

    await index.replace(scope_id, catalog, embeddings)
    try:
        lexical = await index.lexical_search(
            scope_id,
            lexical_requirement,
            limit=2,
        )
        semantic = await index.semantic_search(
            scope_id,
            semantic_requirement,
            [1.0, 0.0, 0.0],
            limit=2,
        )

        assert lexical[0].source_id == "cv-actions"
        assert lexical[0].text == catalog[0].text
        assert semantic[0].source_id == "cv-actions"
        assert semantic[0].semantic_score == pytest.approx(1.0)
    finally:
        await index.delete(scope_id)

    assert await index.lexical_search(scope_id, lexical_requirement, limit=2) == []
    assert (
        await index.semantic_search(
            scope_id,
            semantic_requirement,
            [1.0, 0.0, 0.0],
            limit=2,
        )
        == []
    )
