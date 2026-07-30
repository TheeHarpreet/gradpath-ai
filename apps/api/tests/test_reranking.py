"""Tests for bounded evidence-aware reranking."""

from gradpath_api.application.reranking import EvidenceAwareReranker
from gradpath_api.domain.analysis import JobRequirement, RequirementPriority
from gradpath_api.domain.source import RetrievedEvidence


def _candidate(source_id: str, text: str, score: float) -> RetrievedEvidence:
    return RetrievedEvidence(
        requirement_id="req-001",
        source_id=source_id,
        score=score,
        text=text,
    )


def test_reranker_promotes_documented_ci_cd_alias_without_changing_evidence() -> None:
    requirement = JobRequirement(
        requirement_id="req-001",
        priority=RequirementPriority.DESIRABLE,
        source_text="Familiarity with CI/CD workflows.",
    )
    unrelated = _candidate(
        "cv-profile",
        "Computer Science graduate interested in web applications.",
        0.04,
    )
    relevant = _candidate(
        "cv-project",
        "Used GitHub Actions to run tests on pull requests.",
        0.03,
    )

    reranked = EvidenceAwareReranker().rerank(
        requirement,
        [unrelated, relevant],
        limit=1,
    )

    assert reranked[0].source_id == relevant.source_id
    assert reranked[0].text == relevant.text
    assert reranked[0].score == relevant.score
    assert reranked[0].rerank_score is not None
