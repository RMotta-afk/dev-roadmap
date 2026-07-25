import hashlib
import random
from abc import ABC, abstractmethod

from app.config import settings
from llm.client import get_llm_client


class EmbeddingService(ABC):
    """Abstract interface for text embedding services."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return a list of embedding vectors, one per input text."""
        ...


class OpenAIEmbeddingService(EmbeddingService):
    """Embedding service backed by the shared OpenAI ModelClient."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await get_llm_client().embed(texts)


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
