# Roadmap Schema Migration - Completed

## Overview

Successfully migrated the roadmap system from flat markdown archives to a nested JSON structure with parent-child relationships. The new structure supports hierarchical organization, level-based filtering, and ownership tracking for better skill management.

## What Was Changed

### 1. Data Structure Transformation

**Before (Old Structure):**
- Flat markdown files in `docs/archives/`
- No structured hierarchy
- Limited metadata
- No parent-child relationships

**After (New Structure):**
```
data/roadmaps/
├── roadmap-ai-engineer/
│   ├── roadmap.json          # Root metadata
│   ├── overview.md           # Human-readable overview
│   └── levels/
│       ├── junior/
│       │   ├── level.json    # Level metadata
│       │   ├── group-1.json  # Skill group with children
│       │   └── group-N.json
│       ├── mid/
│       ├── senior/
│       └── staff/
├── roadmap-software-engineer/
└── roadmap-frontend-engineer/
```

### 2. Model Updates

**`RoadmapNode` (apps/api/src/roadmap/models.py)**
- Added `parent_id: str | None` - Links to parent group
- Added `role: RoadmapRole` - Role association
- Added `ownership: str` - "proprio" or "referencia"
- Added `reference_target: str | None` - Reference tracking
- Added `group_number: int | None` - Group ordering
- Added `item_number: str | None` - Skill numbering (e.g., "1.1")
- Made optional fields nullable for backward compatibility

**New `SkillGroup` Model**
- Represents a group containing multiple skills
- Contains metadata about the group itself
- Has its own parent_id for hierarchy

### 3. Core Components Updated

#### a. **Archive Parser** (`roadmap/archive_parser.py`)
- New parser to convert markdown archives to nested JSON
- Handles:
  - Level extraction (Júnior, Pleno, Sênior, Staff)
  - Skill group parsing with ownership detection
  - Individual skill extraction
  - Reference tracking
  - Hierarchical ID generation

#### b. **Loader** (`roadmap/loader.py`)
- Updated to handle nested directory structure
- Loads all skill groups from level subdirectories
- Flattens skills into RoadmapNode list
- Backward compatible with old flat structure
- New `load_skill_groups()` function for group-level queries

#### c. **Index** (`roadmap/index.py`)
- Added `by_parent_id()` - Get children of a node
- Added `by_ownership()` - Filter by ownership type
- Added `get_hierarchy()` - Get full hierarchy (parent, children, siblings)
- Added `filter_nodes()` - Multi-criteria filtering
- Enhanced role+level indexing

#### d. **Seeder** (`rag/seeder.py`)
- Updated text construction for embeddings
- Includes level information in embedded text
- Handles optional content_guidance
- Adds ownership and reference information to embeddings

#### e. **Retriever** (`rag/retriever.py`)
- Enhanced documentation
- Works with new node structure
- Supports filtering by updated fields

### 4. Configuration Update

**`.env`**
```
BASE_ROADMAP_PATH=data/roadmaps  # Changed from docs/archives
```

## Generated Data Statistics

Successfully parsed and converted 3 roadmaps:

| Roadmap | Role | Levels | Groups | Skills |
|---------|------|--------|--------|--------|
| AI Engineer | ai_engineer | 4 | 24 | 166 |
| Frontend Engineer | frontend_engineer | 4 | 21 | 144 |
| Software Engineer | software_engineer | 4 | 11 | 110 |

**Total:** 420 skill nodes across 56 groups

**Ownership Distribution:**
- Próprio (own): 248 skills (59%)
- Referência (reference): 172 skills (41%)

## Key Features

### 1. Hierarchical Organization
```
Role → Level → Group → Skills
```
Each node has a parent_id that links it to its group, enabling hierarchy traversal.

### 2. Level-Based Filtering
Skills are tagged with career levels (junior, mid, senior, staff), allowing precise filtering:
```python
junior_skills = index.by_level(CareerLevel.junior)
ai_junior = index.by_role_level(RoadmapRole.ai_engineer, CareerLevel.junior)
```

### 3. Ownership Tracking
Skills are marked as either:
- **"proprio"** - Owned by this roadmap
- **"referencia"** - References another roadmap (e.g., Software Engineer basics)

This enables:
- Filtering out references to focus on core skills
- Cross-roadmap dependency tracking
- Better context for skill recommendations

### 4. Enhanced Embeddings
Text embeddings now include:
- Skill name and description
- Category (parent group name)
- Level information
- Content guidance topics
- Reference information (if applicable)

This provides richer semantic search capabilities.

## Usage Examples

### Loading Roadmaps
```python
from roadmap import load_all_roadmaps, flatten_nodes, RoadmapIndex

# Load all roadmaps
roadmaps = load_all_roadmaps()

# Flatten to get all skills
all_skills = flatten_nodes(roadmaps)

# Create index for fast lookups
index = RoadmapIndex(all_skills)
```

### Filtering by Level
```python
from roadmap.models import CareerLevel, RoadmapRole

# Get all junior skills
junior_skills = index.by_level(CareerLevel.junior)

# Get AI Engineer junior skills
ai_junior = index.by_role_level(RoadmapRole.ai_engineer, CareerLevel.junior)
```

### Hierarchy Navigation
```python
# Get children of a group
group_skills = index.by_parent_id("ai_engineer-junior-group-1")

# Get full hierarchy
hierarchy = index.get_hierarchy("ai_engineer-junior-group-1-skill-1-1")
# Returns: {node, parent, children, siblings}
```

### Multi-Criteria Filtering
```python
# Get only "proprio" junior skills for AI Engineer
own_junior_ai = index.filter_nodes(
    role=RoadmapRole.ai_engineer,
    level=CareerLevel.junior,
    ownership="proprio",
    node_type="skill"
)
```

## Files Changed

### Created
- `apps/api/src/roadmap/archive_parser.py` - Archive to JSON converter
- `apps/api/src/roadmap/test_loader.py` - Test script
- `data/roadmaps/` - New structured data directory (420 skill files)

### Modified
- `apps/api/src/roadmap/models.py` - Updated RoadmapNode, added SkillGroup
- `apps/api/src/roadmap/loader.py` - Nested structure loading
- `apps/api/src/roadmap/index.py` - Hierarchy support
- `apps/api/src/roadmap/__init__.py` - Export updates
- `apps/api/src/rag/seeder.py` - Enhanced embeddings
- `apps/api/src/rag/retriever.py` - Documentation updates
- `apps/api/src/app/config.py` - Default path update
- `.env` - Path configuration

## Backward Compatibility

The loader maintains backward compatibility:
- If it finds nested directories, it uses the new structure
- If it finds flat JSON files, it falls back to the old behavior
- Optional fields in RoadmapNode ensure old data can still be parsed

## Next Steps (Not Implemented)

The following updates would enhance the system but were not included in scope:

1. **Update API Schemas** (`apps/api/src/app/schemas/analyze.py`)
   - Remove duplicate RoadmapNode definition
   - Use the updated model from roadmap.models

2. **Update Agent Logic** (`apps/api/src/agent/nodes/compare.py`)
   - Consider ownership when comparing nodes
   - Potentially treat reference nodes differently

3. **Add Vector DB Metadata**
   - Ensure all new fields are indexed in Qdrant
   - Add filters for ownership and parent_id in searches

4. **Testing**
   - Run full seeding process: `python -m rag.seeder`
   - Verify embeddings contain enhanced context
   - Test retrieval with level filters
   - Validate hierarchy queries in production

## Running the Seeder

To populate Qdrant with the new data:

```bash
cd apps/api/src
python -c "import asyncio; from rag.seeder import seed_roadmap_collection; asyncio.run(seed_roadmap_collection(force=True))"
```

This will:
1. Delete the old collection
2. Load all roadmaps from the new structure
3. Generate embeddings for 420 skills
4. Upsert to Qdrant with enhanced metadata

## Validation

Tested successfully:
- ✓ Archive parsing (3 roadmaps, 56 groups, 420 skills)
- ✓ JSON structure generation
- ✓ Model validation (all fields parse correctly)
- ✓ Loader (nested structure detection and loading)
- ✓ Index creation (420 nodes indexed)
- ✓ Level filtering (165 junior nodes)
- ✓ Role+level filtering (57 AI junior nodes)
- ✓ Parent-child relationships (6 children per sample group)
- ✓ Ownership distribution (248 próprio, 172 referência)

## Summary

The migration successfully transforms the roadmap system from flat markdown files to a rich, hierarchical, filterable structure. The new design enables:

- **Better organization** through parent-child relationships
- **Precise filtering** by role, level, and ownership
- **Richer embeddings** with contextual metadata
- **Cross-roadmap references** for skill dependencies
- **Scalable architecture** for future enhancements

All 420 skills are now structured, typed, and ready for embedding with enhanced semantic context.
