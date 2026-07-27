"""Complete, serializable context supplied to an analysis provider."""

from gradpath_api.domain.analysis import AnalysisRequest, ContractModel, JobRequirement
from gradpath_api.domain.source import RetrievedEvidence, SourceChunk


class AnalysisContext(ContractModel):
    """Application-prepared input that a model is not allowed to redefine."""

    request: AnalysisRequest
    requirements: list[JobRequirement]
    source_catalog: list[SourceChunk]
    retrieved_evidence: dict[str, list[RetrievedEvidence]]
