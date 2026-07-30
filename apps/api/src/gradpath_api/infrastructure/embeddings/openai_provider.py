"""OpenAI embedding adapter with bounded batches and dimension validation."""

from __future__ import annotations

from openai import APIError as OpenAIAPIError
from openai import AsyncOpenAI

from gradpath_api.infrastructure.embeddings.base import (
    EmbeddingBatch,
    EmbeddingProviderError,
)


class OpenAIEmbeddingProvider:
    """Create ordered float embeddings through the OpenAI embeddings API."""

    def __init__(
        self,
        *,
        client: AsyncOpenAI,
        model: str,
        dimensions: int,
        batch_size: int,
    ) -> None:
        if batch_size < 1:
            raise ValueError("Embedding batch size must be positive.")
        self._client = client
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        """Embed texts in bounded batches while preserving input order."""

        if not texts or any(not text.strip() for text in texts):
            raise ValueError("Embedding inputs must contain non-empty text.")

        vectors: list[list[float]] = []
        total_tokens = 0
        try:
            for start in range(0, len(texts), self._batch_size):
                batch = texts[start : start + self._batch_size]
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                    encoding_format="float",
                )
                ordered = sorted(response.data, key=lambda item: item.index)
                if len(ordered) != len(batch):
                    raise EmbeddingProviderError(
                        "OpenAI returned an unexpected number of embeddings."
                    )
                vectors.extend(item.embedding for item in ordered)
                total_tokens += response.usage.prompt_tokens
        except OpenAIAPIError as exc:
            raise EmbeddingProviderError("OpenAI embedding request failed.") from exc

        return EmbeddingBatch(
            model=self._model,
            dimensions=self._dimensions,
            vectors=vectors,
            input_tokens=total_tokens,
        )
