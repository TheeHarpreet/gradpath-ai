"""Create analysis-scoped hybrid retrieval storage.

Revision ID: 20260730_0001
Revises:
Create Date: 2026-07-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260730_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable pgvector and create isolated retrieval records."""

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE retrieval_chunks (
            scope_id text NOT NULL,
            source_id text NOT NULL,
            source_kind text NOT NULL CHECK (
                source_kind IN ('candidate_cv', 'supporting_evidence')
            ),
            content text NOT NULL CHECK (length(content) BETWEEN 1 AND 10000),
            embedding_model text NOT NULL,
            embedding_dimensions integer NOT NULL CHECK (
                embedding_dimensions BETWEEN 1 AND 2000
            ),
            embedding vector NOT NULL,
            search_vector tsvector GENERATED ALWAYS AS (
                to_tsvector('english', content)
            ) STORED,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (scope_id, source_id),
            CHECK (vector_dims(embedding) = embedding_dimensions)
        )
        """
    )
    op.execute("CREATE INDEX ix_retrieval_chunks_scope ON retrieval_chunks (scope_id)")
    op.execute(
        """
        CREATE INDEX ix_retrieval_chunks_search
        ON retrieval_chunks USING gin (search_vector)
        """
    )


def downgrade() -> None:
    """Remove retrieval records but retain the shared vector extension."""

    op.execute("DROP TABLE IF EXISTS retrieval_chunks")
