"""Transparent lexical retrieval baseline for the first vertical slice."""

from __future__ import annotations

import re

from gradpath_api.domain.analysis import JobRequirement
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk

_TOKEN = re.compile(r"[a-z0-9+#.-]+")
_STOP_WORDS = {
    "a",
    "ability",
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


def retrieve_evidence(
    requirements: list[JobRequirement],
    catalog: list[SourceChunk],
    *,
    limit_per_requirement: int = 3,
) -> dict[str, list[RetrievedEvidence]]:
    """Rank source chunks by explainable weighted token overlap."""

    result: dict[str, list[RetrievedEvidence]] = {}
    for requirement in requirements:
        query_tokens = _meaningful_tokens(requirement.source_text)
        ranked: list[RetrievedEvidence] = []
        for chunk in catalog:
            chunk_tokens = _meaningful_tokens(chunk.text)
            overlap = query_tokens & chunk_tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            ranked.append(
                RetrievedEvidence(
                    requirement_id=requirement.requirement_id,
                    source_id=chunk.source_id,
                    score=round(score, 4),
                    text=chunk.text,
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.source_id))
        result[requirement.requirement_id] = ranked[:limit_per_requirement]
    return result


def _meaningful_tokens(text: str) -> set[str]:
    """Return normalized content tokens used by the baseline scorer."""

    return {
        token
        for token in _TOKEN.findall(text.casefold())
        if len(token) > 1 and token not in _STOP_WORDS
    }
