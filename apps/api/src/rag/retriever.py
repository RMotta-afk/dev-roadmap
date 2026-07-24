"""Hybrid retriever with role/level filters."""

from qdrant_client.models import (
    FieldCondition,
    Filter as QdrantFilter,
    MatchValue,
)

from roadmap.models import RoadmapNode
from rag.embeddings import EmbeddingService, get_embedding_service
from rag.qdrant_client import QdrantRagClient


class RoadmapRetriever:
    """RAG retriever for roadmap nodes."""

    def __init__(
        self,
        qdrant_client: QdrantRagClient,
        embedding_service: EmbeddingService,
    ) -> None:
        self.qdrant_client = qdrant_client
        self.embedding_service = embedding_service

    async def retrieve(
        self,
        query: str,
        role: str | None = None,
        level: str | None = None,
        top_k: int = 10,
    ) -> list[RoadmapNode]:
        """Embed *query* and retrieve the most similar roadmap nodes.

        Optional *role* and *level* filters are applied as Qdrant payload
        filters. Results are returned sorted by relevance (highest score
        first).
        """
        vectors = await self.embedding_service.embed([query])
        vector = vectors[0]

        conditions: list[FieldCondition] = []
        if role is not None:
            conditions.append(FieldCondition(key="role", match=MatchValue(value=role)))
        if level is not None:
            conditions.append(FieldCondition(key="level", match=MatchValue(value=level)))

        qdrant_filter: QdrantFilter | None = None
        if conditions:
            qdrant_filter = QdrantFilter(must=conditions)

        results = await self.qdrant_client.search(
            collection="roadmap_nodes",
            vector=vector,
            filter=qdrant_filter,
            limit=top_k,
        )

        nodes: list[RoadmapNode] = []
        for result in results:
            payload = result["payload"]
            node = RoadmapNode.model_validate(payload)
            nodes.append(node)

        return nodes


def create_retriever() -> RoadmapRetriever:
    """Instantiate the default retriever with config-based services."""
    return RoadmapRetriever(
        qdrant_client=QdrantRagClient(),
        embedding_service=get_embedding_service(),
    )
