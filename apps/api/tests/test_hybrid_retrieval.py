"""Tests for provider-neutral embeddings and hybrid retrieval."""

import pytest
from gradpath_api.application.retrievers import (
    EvidenceRetrievalError,
    HybridEvidenceRetriever,
)
from gradpath_api.domain.analysis import (
    JobRequirement,
    RequirementPriority,
    SourceKind,
)
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk
from gradpath_api.infrastructure.embeddings.base import EmbeddingBatch
from gradpath_api.infrastructure.retrieval.base import RetrievalIndexError
from pydantic import ValidationError


class SemanticFixtureProvider:
    """Map selected semantic concepts to deterministic test vectors."""

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        vectors = [self._vector(text) for text in texts]
        return EmbeddingBatch(
            model="fixture-embedding-v1",
            dimensions=3,
            vectors=vectors,
            input_tokens=None,
        )

    @staticmethod
    def _vector(text: str) -> list[float]:
        normalized = text.casefold()
        if "ci/cd" in normalized or "github actions" in normalized:
            return [1.0, 0.0, 0.0]
        if "communication" in normalized or "presented" in normalized:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]


def _requirement(requirement_id: str, text: str) -> JobRequirement:
    return JobRequirement(
        requirement_id=requirement_id,
        priority=RequirementPriority.ESSENTIAL,
        source_text=text,
    )


@pytest.mark.asyncio
async def test_hybrid_retrieval_recovers_semantic_match_without_token_overlap() -> None:
    requirements = [_requirement("req-001", "Familiarity with CI/CD workflows.")]
    catalog = [
        SourceChunk(
            source_id="cv-actions",
            source_kind=SourceKind.CANDIDATE_CV,
            text="Configured GitHub Actions to run tests on pull requests.",
        ),
        SourceChunk(
            source_id="cv-unrelated",
            source_kind=SourceKind.CANDIDATE_CV,
            text="Completed a relational database module.",
        ),
    ]
    retriever = HybridEvidenceRetriever(
        embedding_provider=SemanticFixtureProvider(),
        limit_per_requirement=1,
        candidate_limit=2,
    )

    result = await retriever.retrieve(requirements, catalog)

    best = result["req-001"][0]
    assert best.source_id == "cv-actions"
    assert best.lexical_rank is None
    assert best.semantic_rank == 1


@pytest.mark.asyncio
async def test_hybrid_retrieval_preserves_exact_source_text_and_ids() -> None:
    requirements = [_requirement("req-001", "Clear communication.")]
    source = SourceChunk(
        source_id="evidence-demo",
        source_kind=SourceKind.SUPPORTING_EVIDENCE,
        text="Presented the project to tutors and incorporated their feedback.",
    )
    retriever = HybridEvidenceRetriever(
        embedding_provider=SemanticFixtureProvider(),
        limit_per_requirement=1,
        candidate_limit=1,
    )

    result = await retriever.retrieve(requirements, [source])

    assert result["req-001"][0].source_id == source.source_id
    assert result["req-001"][0].text == source.text


def test_embedding_batch_rejects_mixed_dimensions() -> None:
    with pytest.raises(ValidationError, match="declared dimensions"):
        EmbeddingBatch(
            model="broken-provider",
            dimensions=3,
            vectors=[[1.0, 0.0, 0.0], [1.0, 0.0]],
        )


class FailingSearchIndex:
    """Record cleanup after a controlled database query failure."""

    def __init__(self) -> None:
        self.deleted = False

    async def replace(
        self,
        scope_id: str,
        catalog: list[SourceChunk],
        embeddings: EmbeddingBatch,
    ) -> None:
        del scope_id, catalog, embeddings

    async def lexical_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        del scope_id, requirement, limit
        raise RetrievalIndexError("Sensitive database detail")

    async def semantic_search(
        self,
        scope_id: str,
        requirement: JobRequirement,
        query_vector: list[float],
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        del scope_id, requirement, query_vector, limit
        return []

    async def delete(self, scope_id: str) -> None:
        del scope_id
        self.deleted = True


@pytest.mark.asyncio
async def test_hybrid_retrieval_attempts_cleanup_after_index_query_failure() -> None:
    index = FailingSearchIndex()
    retriever = HybridEvidenceRetriever(
        embedding_provider=SemanticFixtureProvider(),
        limit_per_requirement=1,
        candidate_limit=1,
        index=index,
    )
    requirements = [_requirement("req-001", "Familiarity with CI/CD.")]
    catalog = [
        SourceChunk(
            source_id="cv-actions",
            source_kind=SourceKind.CANDIDATE_CV,
            text="Configured GitHub Actions for pull requests.",
        )
    ]

    with pytest.raises(EvidenceRetrievalError, match="query failed"):
        await retriever.retrieve(requirements, catalog)

    assert index.deleted is True
