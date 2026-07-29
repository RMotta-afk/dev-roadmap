# Roadmap Data Structure - Quick Reference

## Directory Structure

```
data/roadmaps/
└── roadmap-{role}/              # e.g., roadmap-ai-engineer
    ├── roadmap.json             # Root metadata (role, version, levels)
    ├── overview.md              # Human-readable description
    └── levels/
        └── {level}/             # e.g., junior, mid, senior, staff
            ├── level.json       # Level metadata
            └── group-N.json     # Skill groups (N = 1, 2, 3...)
```

## JSON Schema

### roadmap.json
```json
{
  "id": "ai_engineer",
  "role": "ai_engineer",
  "title": "Roadmap AI Engineer...",
  "version": "2.0",
  "description": "Career roadmap for...",
  "levels": ["junior", "mid", "senior", "staff"],
  "metadata": {
    "author": "Dev Roadmap Team",
    "created_at": "2025",
    "tags": ["career", "skills", "ai_engineer"]
  }
}
```

### levels/{level}/level.json
```json
{
  "level": "junior",
  "title": "JÚNIOR Uso de AI",
  "inherits_from": null,
  "group_count": 7,
  "groups": [
    {
      "id": "ai_engineer-junior-group-1",
      "number": 1,
      "name": "Modelos & Inference",
      "ownership": "proprio"
    }
  ]
}
```

### levels/{level}/group-N.json
```json
{
  "id": "ai_engineer-junior-group-1",
  "parent_id": "ai_engineer-junior",
  "type": "group",
  "group_number": 1,
  "name": "Modelos & Inference",
  "level": "junior",
  "role": "ai_engineer",
  "ownership": "proprio",
  "reference_target": null,
  "skills": [
    {
      "id": "ai_engineer-junior-group-1-skill-1-1",
      "parent_id": "ai_engineer-junior-group-1",
      "type": "skill",
      "item_number": "1.1",
      "name": "Comparar modelos por...",
      "description": "Comparar modelos por...",
      "level": "junior",
      "role": "ai_engineer",
      "category": "Modelos & Inference",
      "importance": 50,
      "estimated_hours": 10,
      "aliases": [],
      "ownership": "proprio",
      "reference_target": null
    }
  ]
}
```

## ID Structure

IDs follow a hierarchical pattern:

```
{role}-{level}-group-{groupNum}
{role}-{level}-group-{groupNum}-skill-{itemNum}
```

Examples:
- `ai_engineer-junior-group-1`
- `ai_engineer-junior-group-1-skill-1-1`
- `software_engineer-senior-group-12-skill-12-3`

## Field Reference

### Common Fields (All Nodes)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier | `"ai_engineer-junior-group-1-skill-1-1"` |
| `name` | string | Display name | `"Comparar modelos por..."` |
| `type` | string | Node type | `"skill"` or `"group"` |
| `level` | string | Career level | `"junior"`, `"mid"`, `"senior"`, `"staff"` |
| `role` | string | Role identifier | `"ai_engineer"`, `"software_engineer"`, `"frontend_engineer"` |

### Skill-Specific Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `parent_id` | string | Parent group ID | `"ai_engineer-junior-group-1"` |
| `item_number` | string | Skill number | `"1.1"`, `"2.3"` |
| `description` | string | Full description | Same as name |
| `category` | string | Group name | `"Modelos & Inference"` |
| `importance` | integer | Importance score (0-100) | `50` |
| `estimated_hours` | integer | Study time estimate | `10` |
| `aliases` | array | Alternative names | `[]` |
| `ownership` | string | Ownership type | `"proprio"` or `"referencia"` |
| `reference_target` | string/null | Reference info | `"software-basico, Software Engineer"` |

### Optional Fields (Backward Compatibility)

| Field | Type | Description |
|-------|------|-------------|
| `requirements_by_level` | object/null | Level-specific requirements |
| `interview` | object/null | Interview metadata |
| `content_guidance` | object/null | Study guidance with topics, examples |

## Ownership Types

### "proprio" (Own)
Skills that are native to this roadmap. These represent the core competencies for this specific role.

Example:
```json
{
  "ownership": "proprio",
  "reference_target": null,
  "name": "Implementar pipelines RAG com retrieval..."
}
```

### "referencia" (Reference)
Skills that reference another roadmap, typically foundational skills shared across roles.

Example:
```json
{
  "ownership": "referencia",
  "reference_target": "software-basico, Software Engineer",
  "name": "Sintaxe da linguagem principal"
}
```

## Level Inheritance

Levels build upon each other:

```
Junior (base level)
  ↓ inherits from
Mid (junior + new mid skills)
  ↓ inherits from
Senior (junior + mid + new senior skills)
  ↓ inherits from
Staff (all previous + new staff skills)
```

In the data:
```json
{
  "level": "mid",
  "inherits_from": "junior"
}
```

## Usage in Code

### Loading Data
```python
from roadmap import load_all_roadmaps, flatten_nodes

# Load all roadmaps
roadmaps = load_all_roadmaps()

# Get all skills as flat list
skills = flatten_nodes(roadmaps)
```

### Querying
```python
from roadmap import RoadmapIndex
from roadmap.models import CareerLevel, RoadmapRole

index = RoadmapIndex(skills)

# By ID
skill = index.by_id("ai_engineer-junior-group-1-skill-1-1")

# By role and level
ai_junior = index.by_role_level(RoadmapRole.ai_engineer, CareerLevel.junior)

# By parent (get group children)
group_skills = index.by_parent_id("ai_engineer-junior-group-1")

# By ownership
own_skills = index.by_ownership("proprio")

# Multi-criteria filter
filtered = index.filter_nodes(
    role=RoadmapRole.ai_engineer,
    level=CareerLevel.junior,
    ownership="proprio",
    node_type="skill"
)
```

### Hierarchy Navigation
```python
# Get full hierarchy context
hierarchy = index.get_hierarchy("ai_engineer-junior-group-1-skill-1-1")

# Access components
current_skill = hierarchy["node"]
parent_group = hierarchy["parent"]  # May be None if group not in index
children = hierarchy["children"]     # Empty for skills
siblings = hierarchy["siblings"]     # Other skills in same group
```

## Statistics (Current Data)

| Metric | Count |
|--------|-------|
| Total Roadmaps | 3 |
| Total Levels | 4 per roadmap |
| Total Groups | 56 |
| Total Skills | 420 |
| AI Engineer Skills | 166 |
| Frontend Engineer Skills | 144 |
| Software Engineer Skills | 110 |
| Próprio Skills | 248 (59%) |
| Referência Skills | 172 (41%) |

## File Locations

- **Source Archives**: `docs/archives/*.md`
- **Generated Data**: `data/roadmaps/`
- **Parser**: `apps/api/src/roadmap/archive_parser.py`
- **Models**: `apps/api/src/roadmap/models.py`
- **Loader**: `apps/api/src/roadmap/loader.py`
- **Index**: `apps/api/src/roadmap/index.py`

## Regenerating Data

To regenerate the JSON structure from markdown archives:

```bash
cd apps/api/src
python roadmap/archive_parser.py
```

This will parse `docs/archives/*.md` and output to `data/roadmaps/`.
