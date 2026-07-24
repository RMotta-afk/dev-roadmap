import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter as QdrantFilter,
)

from app.config import settings


def _to_uuid(value: Any) -> uuid.UUID:
    """Coerce a value into a UUID suitable for Qdrant point IDs.

    Valid UUID strings are parsed as-is; everything else is hashed to a
    deterministic UUID so that the same string always maps to the same id.
    """
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return uuid.uuid5(uuid.NAMESPACE_URL, str(value))


class QdrantRagClient:
    """Async wrapper around the official Qdrant client for RAG operations."""

    def __init__(self) -> None:
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            kwargs: dict[str, Any] = {"url": settings.qdrant_url}
            if settings.qdrant_api_key:
                kwargs["api_key"] = settings.qdrant_api_key
            self._client = AsyncQdrantClient(**kwargs)
        return self._client

    async def init_collection(self, name: str = "roadmap_nodes") -> bool:
        """Create the collection if it does not already exist."""
        exists = await self.client.collection_exists(collection_name=name)
        if exists:
            return False

        await self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        return True

    async def upsert_points(
        self,
        collection: str,
        points: list[dict[str, Any]],
    ) -> None:
        """Upsert points into the specified collection.

        Each point dict should contain:
            - "id": optional point id (defaults to a random UUID)
            - "vector": list[float]
            - "payload": dict[str, Any]
        """
        qdrant_points: list[PointStruct] = []
        for p in points:
            point_id = _to_uuid(p.get("id", uuid.uuid4()))
            qdrant_points.append(
                PointStruct(
                    id=point_id,
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
            )

        await self.client.upsert(
            collection_name=collection,
            points=qdrant_points,
            wait=True,
        )

    async def search(
        self,
        collection: str,
        vector: list[float],
        filter: QdrantFilter | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search a collection by vector similarity."""
        results = await self.client.search(
            collection_name=collection,
            query_vector=vector,
            query_filter=filter,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]
