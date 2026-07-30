"""Candidate-controlled source records used by retrieval and citation checks."""

from pydantic import Field

from gradpath_api.domain.analysis import ContractModel, SourceKind


class SourceChunk(ContractModel):
    """One stable, citable section of a candidate-controlled document."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    source_kind: SourceKind
    text: str = Field(min_length=1, max_length=10_000)


class RetrievedEvidence(ContractModel):
    """A deterministically ranked chunk for one requirement."""

    requirement_id: str = Field(pattern=r"^req-[0-9]{3,}$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    score: float = Field(gt=0)
    text: str = Field(min_length=1, max_length=10_000)
    lexical_rank: int | None = Field(default=None, ge=1)
    semantic_rank: int | None = Field(default=None, ge=1)
    semantic_score: float | None = Field(default=None, ge=-1, le=1)
    rerank_score: float | None = Field(default=None, gt=0)
