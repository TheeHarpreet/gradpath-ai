"""End-to-end orchestration for the first text analysis vertical slice."""

from __future__ import annotations

from uuid import uuid4

from gradpath_api.application.input_security import secure_analysis_request
from gradpath_api.application.requirements import extract_requirements
from gradpath_api.application.retrievers import (
    EvidenceRetriever,
    LexicalEvidenceRetriever,
)
from gradpath_api.application.sources import build_source_catalog
from gradpath_api.application.validation import validate_model_analysis
from gradpath_api.domain.analysis import AnalysisRequest, AnalysisResponse
from gradpath_api.domain.context import AnalysisContext
from gradpath_api.infrastructure.ai.base import AnalysisProvider


class AnalysisService:
    """Coordinate extraction, retrieval, model analysis, and verification."""

    def __init__(
        self,
        provider: AnalysisProvider,
        *,
        retriever: EvidenceRetriever | None = None,
    ) -> None:
        self._provider = provider
        self._retriever = retriever or LexicalEvidenceRetriever()

    async def analyse(self, request: AnalysisRequest) -> AnalysisResponse:
        """Run one analysis without persisting sensitive candidate text."""

        request, _ = secure_analysis_request(request)
        requirements = extract_requirements(request.job_description)
        catalog = build_source_catalog(request)
        retrieved_evidence = await self._retriever.retrieve(requirements, catalog)
        context = AnalysisContext(
            request=request,
            requirements=requirements,
            source_catalog=catalog,
            retrieved_evidence=retrieved_evidence,
        )
        model_analysis = await self._provider.analyse(context)
        validate_model_analysis(
            model_analysis,
            requirements=requirements,
            catalog=catalog,
        )
        return AnalysisResponse(
            analysis_id=f"analysis-{uuid4().hex}",
            **model_analysis.model_dump(),
        )
