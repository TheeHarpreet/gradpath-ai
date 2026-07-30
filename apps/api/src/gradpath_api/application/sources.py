"""Turn pasted candidate text into stable citation units."""

from __future__ import annotations

import re

from gradpath_api.domain.analysis import AnalysisRequest, SourceKind
from gradpath_api.domain.source import SourceChunk

_BLOCK_BREAK = re.compile(r"\n\s*\n")
_MARKDOWN_HEADING = re.compile(r"^\s*#{1,6}\s+(?P<body>.+?)\s*$")
_MARKDOWN_ANCHOR = re.compile(r"\s+\{#(?P<anchor>[a-z0-9-]+)\}\s*$")
_MAX_SOURCE_CHUNKS = 100


class SourceCatalogError(ValueError):
    """Raised when candidate sources cannot form unambiguous citation units."""


def build_source_catalog(request: AnalysisRequest) -> list[SourceChunk]:
    """Create deterministic chunks from candidate-controlled documents."""

    chunks = _chunk_document(
        request.candidate_cv,
        prefix="cv",
        source_kind=SourceKind.CANDIDATE_CV,
    )
    if request.supporting_evidence:
        chunks.extend(
            _chunk_document(
                request.supporting_evidence,
                prefix="evidence",
                source_kind=SourceKind.SUPPORTING_EVIDENCE,
            )
        )
    source_ids = [chunk.source_id for chunk in chunks]
    if len(source_ids) > _MAX_SOURCE_CHUNKS:
        raise SourceCatalogError("Candidate sources contain too many sections.")
    if len(source_ids) != len(set(source_ids)):
        raise SourceCatalogError("Candidate sources contain duplicate source IDs.")
    return chunks


def _chunk_document(
    text: str,
    *,
    prefix: str,
    source_kind: SourceKind,
) -> list[SourceChunk]:
    """Create heading-based sections, falling back to paragraph chunks."""

    if not any(_MARKDOWN_HEADING.match(line) for line in text.splitlines()):
        return [
            SourceChunk(
                source_id=f"{prefix}-{index:03d}",
                source_kind=source_kind,
                text=block.strip(),
            )
            for index, block in enumerate(_BLOCK_BREAK.split(text), start=1)
            if block.strip()
        ]

    chunks: list[SourceChunk] = []
    heading: str | None = None
    anchor: str | None = None
    body: list[str] = []

    def flush_section() -> None:
        nonlocal body
        content = "\n".join(body).strip()
        if not content:
            body = []
            return
        text_with_heading = f"{heading}\n{content}" if heading else content
        chunks.append(
            SourceChunk(
                source_id=anchor or f"{prefix}-{len(chunks) + 1:03d}",
                source_kind=source_kind,
                text=text_with_heading,
            )
        )
        body = []

    for line in text.splitlines():
        match = _MARKDOWN_HEADING.match(line)
        if match:
            flush_section()
            raw_heading = match.group("body")
            anchor_match = _MARKDOWN_ANCHOR.search(raw_heading)
            anchor = anchor_match.group("anchor") if anchor_match else None
            heading = _MARKDOWN_ANCHOR.sub("", raw_heading).strip()
            continue
        body.append(line)
    flush_section()
    return chunks
