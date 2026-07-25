from __future__ import annotations

import hashlib
import json
import random
from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI

from app.config import settings


class ModelClient(ABC):
    @abstractmethod
    async def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def aclose(self) -> None: ...


class OpenAIModelClient(ModelClient):
    def __init__(
        self,
        api_key: str,
        llm_model: str,
        embedding_model: str,
        timeout: float = 15.0,
    ) -> None:
        self._llm_model = llm_model
        self._embedding_model = embedding_model
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=2)

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=model or self._llm_model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.embeddings.create(
            input=texts,
            model=self._embedding_model,
        )
        response.data.sort(key=lambda x: x.index)
        return [item.embedding for item in response.data]

    async def aclose(self) -> None:
        # openai.AsyncOpenAI.close() is sync
        self._client.close()


class MockModelClient(ModelClient):
    async def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("No LLM API key configured")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
            rng = random.Random(seed)
            vec = [rng.uniform(-1.0, 1.0) for _ in range(1536)]
            norm = sum(x * x for x in vec) ** 0.5
            if norm == 0:
                norm = 1
            vec = [x / norm for x in vec]
            results.append(vec)
        return results

    async def aclose(self) -> None:
        pass


_client: ModelClient | None = None


def get_llm_client() -> ModelClient:
    global _client
    if _client is None:
        if settings.llm_api_key:
            _client = OpenAIModelClient(
                api_key=settings.llm_api_key,
                llm_model=settings.llm_model,
                embedding_model=settings.embedding_model,
            )
        else:
            _client = MockModelClient()
    return _client
