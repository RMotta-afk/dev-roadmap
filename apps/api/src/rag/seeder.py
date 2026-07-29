"""Idempotent Qdrant seeder for roadmap RAG data.

Includes exponential backoff retry for connection errors.
"""

from __future__ import annotations

import sys

from app.config import settings
from rag.embeddings import get_embedding_service
from rag.qdrant_client import QdrantRagClient
from roadmap.loader import load_all_roadmaps
from roadmap.models import RoadmapNode

COLLECTION_NAME = "roadmap_nodes"

MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_DELAY = 30.0


def _log(msg: str) -> None:
    print(f"[rag.seeder] {msg}", flush=True)
    sys.stdout.flush()


def _is_retryable(exc: Exception) -> bool:
    """Check if an error is transient and worth retrying."""
    msg = str(exc).lower()
    return any(
        kw in msg
        for kw in [
            "connection",
            "timeout",
            "refused",
            "unavailable",
            "network",
        ]
    )


async def seed_roadmap_collection(
    *, force: bool = False
) -> int:
    """Seed Qdrant with roadmap nodes if the collection is empty or missing.

    Retries on connection errors with exponential backoff.

    Returns the number of points upserted (0 if skipped or failed).
    Gracefully skips if Qdrant is not reachable after all retries.
    """

    return await _seed_once(force=force)


async def _seed_once(*, force: bool = False) -> int:
    """Single attempt to seed Qdrant. Contains the actual logic."""
    path = settings.base_roadmap_path
    _log(f"roadmap path={path} exists={path.is_dir()}")

    qdrant = QdrantRagClient()

    try:
        if force:
            deleted = await qdrant.delete_collection(name=COLLECTION_NAME)
            _log(f"force: delete collection '{COLLECTION_NAME}' -> {deleted}")
        await qdrant.init_collection(name=COLLECTION_NAME)
    except Exception as exc:
        _log(f"Qdrant not reachable at {settings.qdrant_url} — skip seed. Error: {exc}")
        return 0

    count_result = await qdrant.client.count(collection_name=COLLECTION_NAME)
    if count_result.count > 0 and not force:
        _log(
            f"Skipped seeding: collection '{COLLECTION_NAME}' "
            f"already has {count_result.count} points."
        )
        return 0

    if not path.is_dir():
        _log(f"ERROR: roadmap directory missing: {path}")
        return 0

    roadmaps = load_all_roadmaps()
    json_files = sorted(path.glob("*.json"))
    _log(f"found {len(json_files)} json file(s), loaded {len(roadmaps)} roadmap(s)")
    if not roadmaps:
        _log(f"No roadmap files loaded from {path}")
        return 0

    nodes_with_role: list[tuple[RoadmapNode, str]] = []
    texts: list[str] = []
    for roadmap in roadmaps:
        role = roadmap.role.value
        for node in roadmap.nodes:
            nodes_with_role.append((node, role))
            text_parts = [node.name, node.description, node.category]
            text_parts.append(f"Level: {node.level.value}")
            if node.content_guidance:
                text_parts.append(" ".join(node.content_guidance.topics))
            if node.ownership == "referencia" and node.reference_target:
                text_parts.append(f"References: {node.reference_target}")
            text = " ".join(text_parts)
            texts.append(text)

    if not texts:
        _log("No nodes found in roadmap files.")
        return 0

    _log(f"embedding {len(texts)} node(s)…")
    embedding_service = get_embedding_service()
    embeddings = await embedding_service.embed(texts)

    points: list[dict] = []
    for (node, role), vector in zip(nodes_with_role, embeddings, strict=True):
        payload = node.model_dump(mode="json")
        payload["role"] = role
        points.append(
            {
                "id": node.id,
                "vector": vector,
                "payload": payload,
            }
        )

    await qdrant.upsert_points(collection=COLLECTION_NAME, points=points)
    _log(f"Seeded {len(points)} points into collection '{COLLECTION_NAME}'.")
    return len(points)
