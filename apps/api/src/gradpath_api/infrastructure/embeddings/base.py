"""Provider-neutral embedding contracts."""

from __future__ import annotations

from typing import Protocol

from pydantic import Field, model_validator

from gradpath_api.domain.analysis import ContractModel


class EmbeddingProviderError(RuntimeError):
    """Raised when an embedding provider cannot return a safe result."""


class EmbeddingBatch(ContractModel):
    """Ordered embedding vectors plus safe usage metadata."""

    model: str = Field(min_length=1)
    dimensions: int = Field(gt=0, le=4096)
    vectors: list[list[float]] = Field(min_length=1)
    input_tokens: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def vectors_match_declared_dimensions(self) -> EmbeddingBatch:
        """Reject truncated, mixed, or unexpectedly sized vectors."""

        if any(len(vector) != self.dimensions for vector in self.vectors):
            raise ValueError("Embedding vectors do not match declared dimensions.")
        return self


class EmbeddingProvider(Protocol):
    """Convert ordered text inputs into vectors in the same order."""

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        """Embed one non-empty batch of texts."""

        ...
