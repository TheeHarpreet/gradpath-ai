"""Bounded, explainable reranking for candidate evidence."""

from __future__ import annotations

import re
from typing import Protocol

from gradpath_api.domain.analysis import JobRequirement
from gradpath_api.domain.source import RetrievedEvidence

_TOKEN = re.compile(r"[a-z0-9+#./-]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "experience",
    "familiarity",
    "for",
    "in",
    "of",
    "or",
    "the",
    "to",
    "understanding",
    "using",
    "with",
}
_CONCEPT_ALIASES: tuple[tuple[frozenset[str], frozenset[str]], ...] = (
    (
        frozenset({"ci/cd", "continuous integration", "continuous delivery"}),
        frozenset({"github actions", "pipeline", "pull request"}),
    ),
    (
        frozenset({"rest api", "restful api", "http api"}),
        frozenset({"fastapi", "endpoint", "api"}),
    ),
    (
        frozenset({"container", "containerisation", "containerization"}),
        frozenset({"docker", "compose.yaml", "dockerfile"}),
    ),
    (
        frozenset({"communication", "communicate", "collaborative"}),
        frozenset({"presented", "demonstrated", "feedback", "handover notes"}),
    ),
    (
        frozenset({"relational database", "sql database"}),
        frozenset({"postgresql", "sql", "database schema"}),
    ),
)


class EvidenceReranker(Protocol):
    """Reorder an already bounded evidence candidate set."""

    def rerank(
        self,
        requirement: JobRequirement,
        candidates: list[RetrievedEvidence],
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Return at most the requested number of unchanged evidence items."""

        ...


class IdentityReranker:
    """Preserve fused ranking for comparison and controlled fallback."""

    def rerank(
        self,
        requirement: JobRequirement,
        candidates: list[RetrievedEvidence],
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Return the existing order without adding a score."""

        del requirement
        return candidates[:limit]


class EvidenceAwareReranker:
    """Reward exact coverage and documented engineering concept aliases."""

    def rerank(
        self,
        requirement: JobRequirement,
        candidates: list[RetrievedEvidence],
        *,
        limit: int,
    ) -> list[RetrievedEvidence]:
        """Reorder candidates without altering their IDs, text, or RRF score."""

        query = requirement.source_text.casefold()
        query_tokens = _meaningful_tokens(query)
        scored: list[RetrievedEvidence] = []
        for candidate in candidates:
            content = candidate.text.casefold()
            overlap = len(query_tokens & _meaningful_tokens(content))
            aliases = _alias_matches(query, content)
            rerank_score = candidate.score + (overlap * 0.005) + (aliases * 0.02)
            scored.append(
                candidate.model_copy(update={"rerank_score": round(rerank_score, 8)})
            )
        scored.sort(
            key=lambda item: (
                -(item.rerank_score or item.score),
                -item.score,
                item.source_id,
            )
        )
        return scored[:limit]


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN.findall(text)
        if len(token) > 1 and token not in _STOP_WORDS
    }


def _alias_matches(query: str, content: str) -> int:
    matches = 0
    for query_phrases, evidence_phrases in _CONCEPT_ALIASES:
        query_match = any(phrase in query for phrase in query_phrases)
        evidence_match = any(phrase in content for phrase in evidence_phrases)
        matches += query_match and evidence_match
    return matches
