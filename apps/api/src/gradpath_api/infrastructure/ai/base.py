"""Provider-neutral model analysis interface."""

from typing import Protocol

from gradpath_api.domain.analysis import ModelAnalysis
from gradpath_api.domain.context import AnalysisContext


class AnalysisProvider(Protocol):
    """Anything capable of producing the strict model analysis contract."""

    async def analyse(self, context: AnalysisContext) -> ModelAnalysis:
        """Analyse prepared evidence without changing application-owned inputs."""
        ...


class ModelProviderError(RuntimeError):
    """A provider failed without yielding a safe structured analysis."""


class ModelRefusalError(ModelProviderError):
    """The provider explicitly refused the analysis request."""
