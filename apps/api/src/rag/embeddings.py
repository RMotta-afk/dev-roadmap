import hashlib
import random
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import settings


class EmbeddingService(ABC):
    """Abstract interface for text embedding services."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return a list of embedding vectors, one per input text."""
        ...


class OpenAIEmbeddingService(EmbeddingService):
    """Embedding service backed by the OpenAI API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.embedding_model
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self.client.post(
            "/embeddings",
            json={
                "input": texts,
                "model": self.model,
            },
        )
        response.raise_for_status()
        data = response.json()
        embeddings = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class MockEmbeddingService(EmbeddingService):
    """Deterministic mock embedding service for local development / tests."""

    DIMENSION = 1536

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
            rng = random.Random(seed)
            vec = [rng.uniform(-1.0, 1.0) for _ in range(self.DIMENSION)]
            # Normalise to unit length so cosine distance works properly in tests
            norm = sum(x * x for x in vec) ** 0.5
            if norm == 0:
                norm = 1
            vec = [x / norm for x in vec]
            results.append(vec)
        return results


def get_embedding_service() -> EmbeddingService:
    """Return an embedding service based on current configuration."""
    if settings.llm_api_key:
        return OpenAIEmbeddingService()
    return MockEmbeddingService()
