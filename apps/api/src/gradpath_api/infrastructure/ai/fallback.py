"""Ordered provider fallback without weakening output validation."""

from gradpath_api.domain.analysis import ModelAnalysis
from gradpath_api.domain.context import AnalysisContext
from gradpath_api.infrastructure.ai.base import AnalysisProvider, ModelProviderError


class FallbackAnalysisProvider:
    """Try configured providers in order and fail safely when all are unavailable."""

    def __init__(self, providers: list[AnalysisProvider]) -> None:
        if not providers:
            raise ValueError("At least one analysis provider is required.")
        self._providers = providers

    async def analyse(self, context: AnalysisContext) -> ModelAnalysis:
        failures: list[ModelProviderError] = []
        for provider in self._providers:
            try:
                return await provider.analyse(context)
            except ModelProviderError as exc:
                failures.append(exc)
        raise ModelProviderError(
            "Every configured analysis provider failed."
        ) from failures[-1]
