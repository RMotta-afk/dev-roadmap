"""Load roadmap JSON files and flatten nodes."""

import json
from pathlib import Path

from app.config import settings
from roadmap.models import RoadmapFile, RoadmapNode


def load_roadmaps(directory: Path) -> list[RoadmapFile]:
    """Load all JSON roadmap files from *directory* into RoadmapFile objects."""
    files = sorted(directory.glob("*.json"))
    roadmaps: list[RoadmapFile] = []
    for path in files:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        roadmaps.append(RoadmapFile.model_validate(data))
    return roadmaps


def load_all_roadmaps() -> list[RoadmapFile]:
    """Load all JSON roadmap files from the configured base path."""
    return load_roadmaps(settings.base_roadmap_path)


def flatten_nodes(roadmaps: list[RoadmapFile]) -> list[RoadmapNode]:
    """Flatten all nodes from a list of RoadmapFile objects into a single list."""
    nodes: list[RoadmapNode] = []
    for roadmap in roadmaps:
        nodes.extend(roadmap.nodes)
    return nodes
