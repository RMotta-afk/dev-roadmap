"""Idempotent Qdrant seeder for roadmap RAG data."""

import json
import logging

from app.config import settings
from rag.embeddings import get_embedding_service
from rag.qdrant_client import QdrantRagClient
from roadmap.loader import load_all_roadmaps
from roadmap.models import RoadmapNode

logger = logging.getLogger("rag.seeder")
COLLECTION_NAME = "roadmap_nodes"


async def seed_roadmap_collection() -> None:
    """Seed Qdrant with roadmap nodes if the collection is empty or missing."""
    qdrant = QdrantRagClient()

    # Ensure collection exists (creates with 1536-dim cosine vectors if missing)
    await qdrant.init_collection(name=COLLECTION_NAME)

    # Idempotency check: skip if collection already contains points
    count_result = await qdrant.client.count(collection_name=COLLECTION_NAME)
    if count_result.count > 0:
        logger.info(
            "Skipped seeding: collection '%s' already has %s points.",
            COLLECTION_NAME,
            count_result.count,
        )
        return

    # Load all roadmap files from the configured base path
    roadmaps = load_all_roadmaps()
    if not roadmaps:
        logger.warning(
            "No roadmap files found at %s.", settings.base_roadmap_path
        )
        return

    # Pair each node with its parent roadmap role and build embedding texts
    nodes_with_role: list[tuple[RoadmapNode, str]] = []
    texts: list[str] = []
    for roadmap in roadmaps:
        role = roadmap.role.value
        for node in roadmap.nodes:
            nodes_with_role.append((node, role))
            text = (
                f"{node.name} {node.description} "
                f"{' '.join(node.content_guidance.topics)}"
            )
            texts.append(text)

    if not texts:
        logger.warning("No nodes found in roadmap files.")
        return

    # Generate embeddings in a single batch call
    embedding_service = get_embedding_service()
    embeddings = await embedding_service.embed(texts)

    # Build Qdrant points with structured payloads
    points: list[dict] = []
    for (node, role), vector in zip(nodes_with_role, embeddings):
        points.append(
            {
                "id": node.id,
                "vector": vector,
                "payload": {
                    "role": role,
                    "level": node.level.value,
                    "node_id": node.id,
                    "category": node.category,
                    "importance": node.importance,
                    "name": node.name,
                    "description": node.description,
                    "content_guidance": json.dumps(
                        node.content_guidance.model_dump(), ensure_ascii=False
                    ),
                },
            }
        )

    await qdrant.upsert_points(collection=COLLECTION_NAME, points=points)
    logger.info(
        "Seeded %s points into collection '%s'.",
        len(points),
        COLLECTION_NAME,
    )
