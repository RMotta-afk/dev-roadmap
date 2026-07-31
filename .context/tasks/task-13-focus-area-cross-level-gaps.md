# Task 13 — Include Focus-Area Skill Gaps Across All Levels (Junior Through Target)

## Goal Reference

- **Goal:** When a user has an explicit focus area (e.g. "cloud") and aims significantly above their current level (e.g. mid→staff), include foundational focus-area nodes from levels below their current level (e.g. junior cloud skills) that they haven't demonstrated. The roadmap must cover the full knowledge chain for the chosen focus, not just gaps at or above current level.
- **Depends on:** Task 12 (reliable focus-area extraction from description)
- **Depended on by:** None

## Problem

`apps/api/src/agent/nodes/compare.py:111-119` aggregates target nodes using the level range `current_level → target_level` only:

```python
if target_level == current_level:
    target_nodes = index.by_role_level(target_role, target_level)
else:
    target_nodes = index.by_role_level_range(
        target_role, current_level, target_level
    )
```

For a `mid`-level user targeting `staff` with focus `"cloud"`, this produces only `[mid, senior, staff]` nodes. Junior-level cloud fundamentals (e.g. basic networking, IAM, storage concepts) are entirely excluded, even if the user never learned them. The user receives a roadmap missing prerequisite foundation skills for their chosen focus area.

## Affected Files

- `apps/api/src/agent/nodes/compare.py` — `compare_node` function, target_nodes computation (lines 111-119)
- `apps/api/src/roadmap/index.py` — add new method `nodes_by_role_and_focus_areas()` or equivalent query helper
- `apps/api/src/roadmap/models.py` — `RoadmapNode` model already has `name`, `category`, `aliases` fields sufficient for focus matching; no changes needed here

## Approach

### Step 1 — Add `by_role_level_range_focus_filtered` to `RoadmapIndex`

Add a new method to `RoadmapIndex` in `index.py` that returns nodes matching a role, level range, and focus-area token/alias match:

```python
def by_role_level_range_focus_filtered(
    self,
    role: RoadmapRole,
    from_level: CareerLevel,
    to_level: CareerLevel,
    focus_tokens: set[str],
) -> list[RoadmapNode]:
    """Return nodes for *role* from *from_level* through *to_level* (inclusive)
    whose name, category, or aliases match any of *focus_tokens*.
    Deduplicated by id."""
    seen: set[str] = set()
    result: list[RoadmapNode] = []
    for level in levels_in_range(from_level, to_level):
        for node in self.by_role_level(role, level):
            if node.id in seen:
                continue
            # Check focus match
            searchable = {node.name.lower(), node.category.lower()}
            searchable.update(a.lower() for a in node.aliases)
            if not focus_tokens or any(
                token in s for s in searchable for token in focus_tokens
            ):
                seen.add(node.id)
                result.append(node)
    return result
```

### Step 2 — Modify `compare_node` to union in lower-level focus nodes

In `compare.py`, after computing the original `target_nodes` (current→target), also compute a second set from `junior → current_level` using the new focus-filtered method when `focus_areas` is non-empty. Merge both sets deduplicated by id before classification:

```python
# Build focus tokens from career frame
focus_tokens: set[str] = set()
if state.career_frame and state.career_frame.focus_areas:
    for phrase in state.career_frame.focus_areas:
        for token in phrase.lower().split():
            focus_tokens.add(token)

# Original: nodes from current level through target level
target_nodes = index.by_role_level_range(
    target_role, current_level, target_level
)

# Supplement: focus-matched nodes from junior through current level
if focus_tokens and current_level != CareerLevel.junior:
    base_nodes = index.by_role_level_range_focus_filtered(
        target_role,
        CareerLevel.junior,
        current_level,
        focus_tokens,
    )
    # Merge deduplicated — base_nodes which are not already in target_nodes
    existing_ids = {n.id for n in target_nodes}
    for node in base_nodes:
        if node.id not in existing_ids:
            target_nodes.append(node)
            existing_ids.add(node.id)
```

### Step 3 — Fallback if no target_nodes found

Keep the existing fallback (line 118-119) for when `by_role_level_range` returns empty for the target role — fall back to `by_level_range` across all roles.

## Acceptance Criteria

1. A `mid` user targeting `staff` with `focus_areas=["Cloud"]` receives cloud-tagged junior-level nodes (e.g. "AWS Fundamentals", "Cloud Networking") if they are gaps, not just mid/senior/staff-level cloud nodes.
2. A user with no focus areas has no behavioral change — only the original `current_level→target_level` range is used.
3. A `junior` user (where `current_level == CareerLevel.junior`) has no behavioral change since the lower range is empty.
4. Deduplication works correctly: if a node appears in both the base range (junior→current) and the main range (current→target), it appears only once in the matched_nodes list.
5. The strict-subset guardrail (ADR-008) is unaffected — all selected nodes are still sourced from the canonical index.
6. All existing tests continue to pass.
