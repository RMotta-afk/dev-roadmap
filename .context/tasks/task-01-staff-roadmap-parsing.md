# Task 1 — Fix Staff Roadmap Parsing and Content Separation

## Goal Reference

- **Goal:** G8 (Fix Staff roadmap parsing)
- **Depends on:** None (foundational — all other goals that use Staff-level data depend on this)
- **Depended on by:** G11 (compatibility score needs Staff nodes indexed)

## Problem

The archive parser silently drops every Staff group from all three roadmaps, producing `group_count: 0` and zero Staff-level nodes in `data/roadmaps/` for every role. The root cause is twofold: a regex bug in `archive_parser.py` and a missing ownership literal handler in `GROUP_PATTERN`.

### Root Cause 1 — Regex whitespace (affects backend + ai-engineer)

`apps/api/src/roadmap/archive_parser.py:51-55`:

```python
GROUP_PATTERN = re.compile(
    r'^\*\*(\d+)\.\s+(.+?)\s+(Básico|Intermediário|Avançado|Básico \+ Intermediário|'
    r'Intermediário \+ Avançado|Básico \+ Intermediário \+ Avançado)?\*\*\s*'
    r'\*\((próprio|referência\s*→\s*`([^`]+)`(?:,\s*(.+?))?)\)\*'
)
```

The `\s+` before the optional level-suffix group `(...)?` is **mandatory**. Every Staff group header has no Básico/Intermediário/Avançado suffix, so the trailing `\s+` before `\*\*` never finds whitespace — it sees `Padronização**` as contiguous characters and the entire line fails to match. All 6 Staff groups across backend (3 groups: Padronização, Escala, Decisões Organizacionais) and ai-engineer (3 groups: Padronização de AI, Arquitetura organizacional, Governança e escala) are silently dropped.

### Root Cause 2 — Ownership literal (affects frontend)

Frontend's Staff section uses `*(duplicado do Software Engineer — Sênior)*` as ownership instead of `próprio` or `referência → ...`. The regex only matches `próprio` or `referência → \`...\``, so Frontend Staff groups also fail to parse even after the whitespace fix.

### Root Cause 3 — No genuine Staff content for Frontend

`docs/archives/roadmap-frontend-indice.md:221-244` does not define original Frontend Staff competencies. It copy-pasts Senior Software Engineer groups and labels them `duplicado`. Per the user's instruction, we do NOT fabricate new Frontend Staff content; the parser should handle this as an intentional case.

## Affected Files

- `apps/api/src/roadmap/archive_parser.py` (regex fix + ownership handling)
- `docs/archives/roadmap-frontend-indice.md` (no content changes needed)
- `data/roadmaps/*/levels/staff/level.json` (needs regeneration with correct group_count > 0 for backend + ai-engineer; 0 for frontend with intent noted)
- `data/roadmaps/.manifest.json` (needs regeneration)
- Qdrant collection `roadmap_nodes` (needs re-seeding)

## Approach

### Step 1: Fix the GROUP_PATTERN regex in `archive_parser.py`

Make the whitespace before `**` optional when there is no level suffix:

```python
GROUP_PATTERN = re.compile(
    r'^\*\*(\d+)\.\s+(.+?)(?:\s+(Básico|Intermediário|Avançado|Básico \+ Intermediário|'
    r'Intermediário \+ Avançado|Básico \+ Intermediário \+ Avançado))?\*\*\s*'
    r'\*\((próprio|referência\s*→\s*`([^`]+)`(?:,\s*(.+?))?)\)\*'
)
```

The change: `(.+?)\s+(SUFFIX)?\*\*` → `(.+?)(?:\s+(SUFFIX))?\*\*` — the whitespace becomes part of the optional non-capturing group, so when there is no suffix there is no required whitespace before `**`.

### Step 2: Add `duplicado` ownership handler

Add `duplicado` as a recognized ownership literal. When `duplicado do Software Engineer — Sênior` is found, record it as `ownership = "referencia"` with `reference_target = "software_engineer, senior"` (matching the actual reference). This makes Frontend Staff intentionally have 0 own groups — they reference the Software Engineer Senior groups as their source.

### Step 3: Regenerate data/roadmaps

Run the parser generator to rebuild all `data/roadmaps/` JSON structures from corrected `docs/archives/*.md`:

```
cd apps/api
python scripts/generate_roadmaps.py
# or: python -m roadmap.archive_parser
```

Verify that after regeneration:
- `data/roadmaps/roadmap-software-engineer/levels/staff/level.json` has `group_count: 3`
- `data/roadmaps/roadmap-ai-engineer/levels/staff/level.json` has `group_count: 3`
- `data/roadmaps/roadmap-frontend-engineer/levels/staff/level.json` has `group_count: 0` (intentional — no original frontend Staff content exists)
- Each staff group has its skills properly populated

### Step 4: Re-seed Qdrant

Run the seeder to repopulate the Qdrant `roadmap_nodes` collection so Staff nodes are now indexed and available for RAG retrieval:

```
python scripts/seed_qdrant.py
```

## Progress

### ✅ T8.1 — Fix GROUP_PATTERN regex whitespace
- Changed `(.+?)\s+(SUFFIX)?\*\*` → `(.+?)(?:\s+(SUFFIX))?\*\*` in `archive_parser.py:51-55`
- Staff group headers with no Básico/Intermediário/Avançado suffix now match correctly

### ✅ T8.2 — Handle `duplicado` ownership marker + regenerate data
- Added `duplicado\s+do\s+(.+?)\s+—\s+(.+?)` alternative to GROUP_PATTERN
- Fixed ownership parsing logic (lines 134-152):
  - `duplicado` detected via `ownership_raw.startswith("duplicado")`
  - Maps role/level display names to canonical IDs via `ROLE_MAP`/`LEVEL_MAP`
  - Sets `reference_target = "{role_canonical}, {level_canonical}"` (e.g., `"software_engineer, senior"`)
  - Skips adding duplicado groups to `current_level.groups` (so frontend staff gets `group_count: 0`)
- Regenerated `data/roadmaps/` via `uv run python scripts/generate_roadmaps.py --force`
- Verified results:
  - `roadmap-software-engineer/levels/staff/level.json`: `group_count: 3` ✅
  - `roadmap-ai-engineer/levels/staff/level.json`: `group_count: 3` ✅
  - `roadmap-frontend-engineer/levels/staff/level.json`: `group_count: 0` ✅
  - Non-Staff groups (Pleno, Senior, Junior) unaffected — no regressions ✅

### ⬜ T8.3 — Re-seed Qdrant
- Pending: run `python scripts/seed_qdrant.py` and verify Staff nodes indexed

## Acceptance Criteria

1. ✅ Running the parser against all 3 `docs/archives/roadmap-*-indice.md` files produces `staff/level.json` with correct `group_count` for backend (3) and ai-engineer (3), and intentional 0 for frontend with documented reference target.
2. ✅ All Group headers in the archives are parseable (no silent drops).
3. ⬜ Every Staff group's skills arrays in `data/roadmaps/*` contain the expected number of skills (7-8 per group as written in the archives).
4. ⬜ After Qdrant re-seed, `retrieve("custo", role="software_engineer", level="staff", top_k=5)` returns non-empty results for backend Staff nodes like "Otimização de custo vs performance".
5. ✅ The existing non-Staff groups (Pleno, Senior, Junior) continue to parse correctly — no regressions.

## Dependencies

None — this is a foundational fix that all other goals that consume Staff data depend on.