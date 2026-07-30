"""Deterministic information-retrieval metrics for committed eval cases."""

from __future__ import annotations

from pydantic import Field

from gradpath_api.domain.analysis import ContractModel
from gradpath_api.domain.source import RetrievedEvidence


class RetrievalMetrics(ContractModel):
    """Aggregate ranking quality for queries with expected evidence."""

    evaluated_queries: int = Field(ge=0)
    expected_evidence: int = Field(ge=0)
    retrieved_relevant_evidence: int = Field(ge=0)
    hit_rate_at_k: float = Field(ge=0, le=1)
    recall_at_k: float = Field(ge=0, le=1)
    mean_reciprocal_rank: float = Field(ge=0, le=1)


def evaluate_retrieval(
    retrieved: dict[str, list[RetrievedEvidence]],
    expected: dict[str, set[str]],
) -> RetrievalMetrics:
    """Measure hit rate, recall, and first-relevant-result rank."""

    relevant_expectations = {
        requirement_id: evidence_ids
        for requirement_id, evidence_ids in expected.items()
        if evidence_ids
    }
    if not relevant_expectations:
        return RetrievalMetrics(
            evaluated_queries=0,
            expected_evidence=0,
            retrieved_relevant_evidence=0,
            hit_rate_at_k=0,
            recall_at_k=0,
            mean_reciprocal_rank=0,
        )

    hit_count = 0
    expected_count = 0
    retrieved_relevant_count = 0
    reciprocal_rank_total = 0.0
    for requirement_id, evidence_ids in relevant_expectations.items():
        ranked_ids = [item.source_id for item in retrieved.get(requirement_id, [])]
        matching_ranks = [
            rank
            for rank, source_id in enumerate(ranked_ids, start=1)
            if source_id in evidence_ids
        ]
        hit_count += bool(matching_ranks)
        expected_count += len(evidence_ids)
        retrieved_relevant_count += len(matching_ranks)
        if matching_ranks:
            reciprocal_rank_total += 1 / min(matching_ranks)

    query_count = len(relevant_expectations)
    return RetrievalMetrics(
        evaluated_queries=query_count,
        expected_evidence=expected_count,
        retrieved_relevant_evidence=retrieved_relevant_count,
        hit_rate_at_k=round(hit_count / query_count, 4),
        recall_at_k=round(retrieved_relevant_count / expected_count, 4),
        mean_reciprocal_rank=round(reciprocal_rank_total / query_count, 4),
    )
