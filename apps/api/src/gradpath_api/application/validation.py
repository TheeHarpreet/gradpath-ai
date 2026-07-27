"""Independent validation of model-supplied citations and requirements."""

from __future__ import annotations

import re

from gradpath_api.domain.analysis import JobRequirement, ModelAnalysis
from gradpath_api.domain.source import SourceChunk

_WHITESPACE = re.compile(r"\s+")


class AnalysisValidationError(ValueError):
    """Raised when model output violates an evidence contract."""


def validate_model_analysis(
    analysis: ModelAnalysis,
    *,
    requirements: list[JobRequirement],
    catalog: list[SourceChunk],
) -> None:
    """Reject missing requirements, invented sources, and fabricated quotes."""

    expected = {item.requirement_id: item for item in requirements}
    received = {
        item.requirement.requirement_id: item.requirement
        for item in analysis.requirements
    }
    if len(analysis.requirements) != len(requirements) or received != expected:
        raise AnalysisValidationError(
            "Model requirements do not exactly match application extraction."
        )

    sources = {chunk.source_id: chunk for chunk in catalog}
    citations = [
        citation
        for assessment in analysis.requirements
        for citation in assessment.citations
    ]
    citations.extend(
        citation for change in analysis.changes for citation in change.citations
    )

    for citation in citations:
        chunk = sources.get(citation.source_id)
        if chunk is None:
            raise AnalysisValidationError(
                f"Citation references unknown source {citation.source_id}."
            )
        if chunk.source_kind != citation.source_kind:
            raise AnalysisValidationError(
                f"Citation source kind does not match {citation.source_id}."
            )
        if _normalize(citation.quote) not in _normalize(chunk.text):
            raise AnalysisValidationError(
                f"Citation quote is not present in {citation.source_id}."
            )


def _normalize(text: str) -> str:
    """Normalize harmless whitespace differences before exact quote checking."""

    return _WHITESPACE.sub(" ", text).strip().casefold()
