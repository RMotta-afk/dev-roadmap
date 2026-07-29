"""Load roadmap JSON files and flatten nodes."""

import json
from pathlib import Path

from app.config import settings
from roadmap.models import RoadmapFile, RoadmapNode, SkillGroup


def load_roadmaps(directory: Path) -> list[RoadmapFile]:
    """Load all JSON roadmap files from *directory* into RoadmapFile objects.
    
    Handles both old flat format and new nested structure.
    For nested structure, loads from roadmap-{role}/ directories.
    """
    roadmaps: list[RoadmapFile] = []
    
    # Check if directory contains nested structure (roadmap-* subdirectories)
    roadmap_dirs = sorted([d for d in directory.iterdir() if d.is_dir() and d.name.startswith("roadmap-")])
    
    if roadmap_dirs:
        # New nested structure
        for roadmap_dir in roadmap_dirs:
            roadmap_json = roadmap_dir / "roadmap.json"
            if not roadmap_json.exists():
                continue
            
            with roadmap_json.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            
            # Load metadata file
            roadmap_file = RoadmapFile.model_validate(data)
            
            # Load all skill nodes from level directories
            levels_dir = roadmap_dir / "levels"
            if levels_dir.exists():
                all_nodes: list[RoadmapNode] = []
                
                for level_dir in sorted(levels_dir.iterdir()):
                    if not level_dir.is_dir():
                        continue
                    
                    # Load all group files in this level
                    for group_file in sorted(level_dir.glob("group-*.json")):
                        with group_file.open("r", encoding="utf-8") as fh:
                            group_data = json.load(fh)
                        
                        # Extract skills from the group
                        skills = group_data.get("skills", [])
                        for skill in skills:
                            node = RoadmapNode.model_validate(skill)
                            all_nodes.append(node)
                
                roadmap_file.nodes = all_nodes
            
            roadmaps.append(roadmap_file)
    else:
        # Old flat structure (backward compatibility)
        files = sorted(directory.glob("*.json"))
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


def load_skill_groups(directory: Path, role: str, level: str) -> list[SkillGroup]:
    """Load skill groups for a specific role and level.
    
    Args:
        directory: Base roadmap directory
        role: Role identifier (e.g., "ai_engineer")
        level: Level identifier (e.g., "junior")
    
    Returns:
        List of SkillGroup objects
    """
    roadmap_dir = directory / f"roadmap-{role.replace('_', '-')}"
    level_dir = roadmap_dir / "levels" / level
    
    if not level_dir.exists():
        return []
    
    groups: list[SkillGroup] = []
    for group_file in sorted(level_dir.glob("group-*.json")):
        with group_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        group = SkillGroup.model_validate(data)
        groups.append(group)
    
    return groups
