"""Parser to convert markdown archive files into nested JSON structures."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class SkillItem:
    """Individual skill item within a group."""
    item_number: str  # e.g., "1.1", "2.3"
    description: str
    

@dataclass
class SkillGroup:
    """Skill group containing multiple skill items."""
    group_number: int
    name: str
    level: str  # "junior", "mid", "senior", "staff"
    ownership: Literal["proprio", "referencia"]
    reference_target: str | None  # e.g., "software-basico, Software Engineer"
    skills: list[SkillItem]


@dataclass
class RoadmapLevel:
    """Career level container."""
    level: str  # "junior", "mid", "senior", "staff"
    title: str  # e.g., "JÚNIOR Fundamentos"
    inherits_from: str | None
    groups: list[SkillGroup]


@dataclass
class RoadmapMetadata:
    """Root roadmap metadata."""
    role: str  # "software_engineer", "ai_engineer", "frontend_engineer"
    title: str
    levels: list[str]


class ArchiveParser:
    """Parse markdown archive files into structured data."""
    
    LEVEL_PATTERN = re.compile(r"^##\s+(JÚNIOR|PLENO|SÊNIOR|STAFF)\s+—\s+(.+)$")
    GROUP_PATTERN = re.compile(
        r'^\*\*(\d+)\.\s+(.+?)\s+(Básico|Intermediário|Avançado|Básico \+ Intermediário|'
        r'Intermediário \+ Avançado|Básico \+ Intermediário \+ Avançado)?\*\*\s*'
        r'\*\((próprio|referência\s*→\s*`([^`]+)`(?:,\s*(.+?))?)\)\*'
    )
    SKILL_PATTERN = re.compile(r'^-\s+(\d+\.\d+)\s+(.+)$')
    INHERITS_PATTERN = re.compile(r'_Herda todo o bloco (\w+)')
    
    LEVEL_MAP = {
        "JÚNIOR": "junior",
        "PLENO": "mid",
        "SÊNIOR": "senior",
        "STAFF": "staff"
    }
    
    ROLE_MAP = {
        "ai-engineer": "ai_engineer",
        "backend": "software_engineer",
        "frontend": "frontend_engineer"
    }
    
    def parse_file(self, file_path: Path) -> tuple[RoadmapMetadata, list[RoadmapLevel]]:
        """Parse a markdown archive file."""
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Extract role from filename
        filename = file_path.stem  # e.g., "roadmap-ai-engineer-indice"
        role_part = filename.replace("roadmap-", "").replace("-indice", "")
        role = self.ROLE_MAP.get(role_part, role_part)
        
        # Parse title from first line
        title = lines[0].strip("# \n")
        
        levels: list[RoadmapLevel] = []
        current_level: RoadmapLevel | None = None
        current_group: SkillGroup | None = None
        
        for line in lines[1:]:
            line = line.rstrip()
            
            # Check for level header
            level_match = self.LEVEL_PATTERN.match(line)
            if level_match:
                # Save previous level
                if current_level and current_group:
                    current_level.groups.append(current_group)
                    current_group = None
                if current_level:
                    levels.append(current_level)
                
                level_raw = level_match.group(1)
                level_title = level_match.group(2)
                current_level = RoadmapLevel(
                    level=self.LEVEL_MAP[level_raw],
                    title=level_title,
                    inherits_from=None,
                    groups=[]
                )
                continue
            
            # Check for inheritance note
            if current_level and "_Herda todo o bloco" in line:
                inherits_match = self.INHERITS_PATTERN.search(line)
                if inherits_match:
                    parent_level = inherits_match.group(1)
                    if parent_level == "Júnior":
                        current_level.inherits_from = "junior"
                    elif parent_level == "Pleno":
                        current_level.inherits_from = "mid"
                    elif parent_level == "Sênior":
                        current_level.inherits_from = "senior"
                continue
            
            # Check for group header
            group_match = self.GROUP_PATTERN.match(line)
            if group_match and current_level:
                # Save previous group
                if current_group:
                    current_level.groups.append(current_group)
                
                group_num = int(group_match.group(1))
                group_name = group_match.group(2).strip()
                ownership_raw = group_match.group(4)
                
                if ownership_raw == "próprio":
                    ownership = "proprio"
                    reference_target = None
                else:
                    ownership = "referencia"
                    ref_id = group_match.group(5)
                    ref_roadmap = group_match.group(6) or ""
                    reference_target = f"{ref_id}, {ref_roadmap}".strip(", ")
                
                current_group = SkillGroup(
                    group_number=group_num,
                    name=group_name,
                    level=current_level.level,
                    ownership=ownership,
                    reference_target=reference_target,
                    skills=[]
                )
                continue
            
            # Check for skill item
            skill_match = self.SKILL_PATTERN.match(line)
            if skill_match and current_group:
                item_num = skill_match.group(1)
                description = skill_match.group(2).strip()
                current_group.skills.append(
                    SkillItem(item_number=item_num, description=description)
                )
        
        # Save last group and level
        if current_level and current_group:
            current_level.groups.append(current_group)
        if current_level:
            levels.append(current_level)
        
        metadata = RoadmapMetadata(
            role=role,
            title=title,
            levels=[lvl.level for lvl in levels]
        )
        
        return metadata, levels


def generate_nested_structure(
    metadata: RoadmapMetadata,
    levels: list[RoadmapLevel],
    output_dir: Path
) -> dict:
    """Generate nested directory structure with JSON files.

    Returns dict with statistics: {roadmaps: 1, groups: N, skills: M}
    """

    base_dir = output_dir / f"roadmap-{metadata.role.replace('_', '-')}"
    base_dir.mkdir(parents=True, exist_ok=True)

    root_meta = {
        "id": metadata.role,
        "role": metadata.role,
        "title": metadata.title,
        "version": "2.0",
        "description": f"Career roadmap for {metadata.title}",
        "levels": metadata.levels,
        "metadata": {
            "author": "Dev Roadmap Team",
            "created_at": "2025",
            "tags": ["career", "skills", metadata.role],
        },
    }

    with open(base_dir / "roadmap.json", "w", encoding="utf-8") as f:
        json.dump(root_meta, f, indent=2, ensure_ascii=False)

    lines = [
        f"# {metadata.title}",
        "",
        f"This roadmap defines the career progression path for {metadata.title.lower()}.",
        "",
        "## Levels",
        "",
    ]
    for level in metadata.levels:
        lvl_title = next((lvl.title for lvl in levels if lvl.level == level), "")
        lines.append(f"- **{level.capitalize()}**: {lvl_title}")
    lines.append("")
    lines.extend([
        "## Structure",
        "",
        "Each level contains multiple skill groups. Skills are organized hierarchically:",
        "- Each level may inherit skills from previous levels",
        "- Skill groups contain individual skills",
        '- Skills can be "próprio" (owned) or "referência" (reference to another roadmap)',
        "",
        "## Usage",
        "",
        "Filter by `level` to retrieve skills for a specific career stage.",
        "Use `parent_id` relationships to navigate the skill hierarchy.",
        "",
    ])
    overview_md = "\n".join(lines)

    with open(base_dir / "overview.md", "w", encoding="utf-8") as f:
        f.write(overview_md)

    levels_dir = base_dir / "levels"
    levels_dir.mkdir(exist_ok=True)

    stats = {"roadmaps": 1, "groups": 0, "skills": 0}

    for level in levels:
        level_dir = levels_dir / level.level
        level_dir.mkdir(exist_ok=True)

        level_meta = {
            "level": level.level,
            "title": level.title,
            "inherits_from": level.inherits_from,
            "group_count": len(level.groups),
            "groups": [
                {
                    "id": f"{metadata.role}-{level.level}-group-{g.group_number}",
                    "number": g.group_number,
                    "name": g.name,
                    "ownership": g.ownership,
                }
                for g in level.groups
            ],
        }

        with open(level_dir / "level.json", "w", encoding="utf-8") as f:
            json.dump(level_meta, f, indent=2, ensure_ascii=False)

        for group in level.groups:
            group_id = f"{metadata.role}-{level.level}-group-{group.group_number}"
            parent_id = f"{metadata.role}-{level.level}"

            group_data = {
                "id": group_id,
                "parent_id": parent_id,
                "type": "group",
                "group_number": group.group_number,
                "name": group.name,
                "level": level.level,
                "role": metadata.role,
                "ownership": group.ownership,
                "reference_target": group.reference_target,
                "skills": [
                    {
                        "id": f"{group_id}-skill-{skill.item_number.replace('.', '-')}",
                        "parent_id": group_id,
                        "type": "skill",
                        "item_number": skill.item_number,
                        "name": skill.description,
                        "description": skill.description,
                        "level": level.level,
                        "role": metadata.role,
                        "category": group.name,
                        "importance": 50,
                        "estimated_hours": 10,
                        "aliases": [],
                        "ownership": group.ownership,
                        "reference_target": group.reference_target,
                    }
                    for skill in group.skills
                ],
            }

            filename = f"group-{group.group_number}.json"
            with open(level_dir / filename, "w", encoding="utf-8") as f:
                json.dump(group_data, f, indent=2, ensure_ascii=False)

            stats["groups"] += 1
            stats["skills"] += len(group.skills)

    return stats


def main() -> None:
    """Convert all archive markdown files to nested JSON structures."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parents[3]
    archives_dir = repo_root / "docs" / "archives"
    output_dir = repo_root / "data" / "roadmaps"

    if not archives_dir.is_dir():
        print(f"ERROR: Archives directory not found: {archives_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    parser_instance = ArchiveParser()
    total_stats = {"roadmaps": 0, "groups": 0, "skills": 0}

    for archive_file in sorted(archives_dir.glob("roadmap-*.md")):
        print(f"\nProcessing: {archive_file.name}")
        try:
            metadata, levels = parser_instance.parse_file(archive_file)
            stats = generate_nested_structure(metadata, levels, output_dir)
            total_stats["roadmaps"] += stats["roadmaps"]
            total_stats["groups"] += stats["groups"]
            total_stats["skills"] += stats["skills"]
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n[OK] All archives processed.")
    print(
        f"  Total: {total_stats['roadmaps']} roadmap(s), "
        f"{total_stats['groups']} groups, {total_stats['skills']} skills"
    )


if __name__ == "__main__":
    main()
