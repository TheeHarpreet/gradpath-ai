"""Tests for retrieval-quality calculations."""

from gradpath_api.application.retrieval_evaluation import evaluate_retrieval
from gradpath_api.domain.source import RetrievedEvidence


def _result(requirement_id: str, source_id: str, score: float) -> RetrievedEvidence:
    return RetrievedEvidence(
        requirement_id=requirement_id,
        source_id=source_id,
        score=score,
        text=f"Fictional source {source_id}",
    )


def test_retrieval_metrics_count_hits_recall_and_first_relevant_rank() -> None:
    retrieved = {
        "req-001": [
            _result("req-001", "irrelevant", 1.0),
            _result("req-001", "evidence-a", 0.8),
        ],
        "req-002": [_result("req-002", "evidence-c", 0.9)],
    }
    expected = {
        "req-001": {"evidence-a", "evidence-b"},
        "req-002": {"evidence-c"},
        "req-003": set(),
    }

    metrics = evaluate_retrieval(retrieved, expected)

    assert metrics.evaluated_queries == 2
    assert metrics.expected_evidence == 3
    assert metrics.retrieved_relevant_evidence == 2
    assert metrics.hit_rate_at_k == 1.0
    assert metrics.recall_at_k == 0.6667
    assert metrics.mean_reciprocal_rank == 0.75
