"""End-to-end orchestration for the first text analysis vertical slice."""

from __future__ import annotations

from uuid import uuid4

from gradpath_api.application.requirements import extract_requirements
from gradpath_api.application.retrieval import retrieve_evidence
from gradpath_api.application.sources import build_source_catalog
from gradpath_api.application.validation import validate_model_analysis
from gradpath_api.domain.analysis import AnalysisRequest, AnalysisResponse
from gradpath_api.domain.context import AnalysisContext
from gradpath_api.infrastructure.ai.base import AnalysisProvider


class AnalysisService:
    """Coordinate extraction, retrieval, model analysis, and verification."""

    def __init__(self, provider: AnalysisProvider) -> None:
        self._provider = provider

    async def analyse(self, request: AnalysisRequest) -> AnalysisResponse:
        """Run one analysis without persisting sensitive candidate text."""

        requirements = extract_requirements(request.job_description)
        catalog = build_source_catalog(request)
        context = AnalysisContext(
            request=request,
            requirements=requirements,
            source_catalog=catalog,
            retrieved_evidence=retrieve_evidence(requirements, catalog),
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
