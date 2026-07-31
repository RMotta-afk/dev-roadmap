# Task 5 — Fix Compatibility Score to Span Current→Target Level Range

## Goal Reference

- **Goal:** Fix compatibility score + roadmap gap selection to measure readiness across the full progression path from current level to target level, not just the target level's own node set.
- **Depends on:** Task 4 (compare.py already classifies the full target-level node set — this task extends it to a multi-level range)
- **Depended on by:** Task 9 (tests), Task 10 (docs)

## Problem

The compatibility score and roadmap gap selection both evaluate against a **single level's node set only** — whatever `target_level` is in `CareerFrame`. This ignores the intermediate curriculum the user must traverse.

### Root Cause 1 — `compare.py` fetches only the target level

`apps/api/src/agent/nodes/compare.py:109`:
```python
target_nodes = index.by_role_level(target_role, target_level)
```

If a user is `junior` aiming for `staff`, this fetches only `staff`-level nodes. The `mid` and `senior` nodes — which the user also needs to learn — are invisible to both classification and scoring.

### Root Cause 2 — `RoadmapIndex` has no range helper

`roadmap/index.py` has `by_role_level` (single level) and `by_level` (single level) but no method to aggregate nodes across a contiguous level range. The `CareerLevel` enum (`junior < mid < senior < staff`) has no ordering constant to compute progression ranges.

### Root Cause 3 — `level_guess.py` dead code leakage

`_compute_target_readiness` (lines 32–62) duplicates the scoring logic inside `_node` but is never called. It can confuse future readers and drifts from the actual implementation.

## Affected Files

- `apps/api/src/roadmap/models.py` — add `CareerLevel` ordering constant (e.g., `LEVEL_ORDER`)
- `apps/api/src/roadmap/index.py` — add `by_role_level_range(role, from_level, to_level) -> list[RoadmapNode]`
- `apps/api/src/agent/nodes/compare.py` — replace `by_role_level` call with `by_role_level_range`
- `apps/api/src/agent/nodes/level_guess.py` — remove dead `_compute_target_readiness` function; verify scoring still works correctly with the now-expanded matched_nodes set

## Approach

### Step 1 — Add `CareerLevel` ordering

In `roadmap/models.py`, add a module-level dict or list that establishes ordering:

```python
LEVEL_ORDER: list[CareerLevel] = [
    CareerLevel.junior,
    CareerLevel.mid,
    CareerLevel.senior,
    CareerLevel.staff,
]
```

Add a helper `levels_in_range(from_level: CareerLevel, to_level: CareerLevel) -> list[CareerLevel]` that slices `LEVEL_ORDER[from_idx : to_idx + 1]`, inclusive of both ends. Raise `ValueError` (or return empty) if `from_level` is above `to_level`.

### Step 2 — Add `by_role_level_range` to `RoadmapIndex`

```python
def by_role_level_range(
    self,
    role: RoadmapRole,
    from_level: CareerLevel,
    to_level: CareerLevel,
) -> list[RoadmapNode]:
    seen: set[str] = set()
    result: list[RoadmapNode] = []
    for level in levels_in_range(from_level, to_level):
        nodes = self.by_role_level(role, level)
        for node in nodes:
            if node.id not in seen:
                seen.add(node.id)
                result.append(node)
    return result
```

This deduplicates by `id` across levels in case any node appears at multiple levels.

### Step 3 — Update `compare.py`

Replace lines 99–111 in `compare.py`:

```python
current_level = state.career_frame.current_level
target_role = state.career_frame.target_role
target_level = state.career_frame.target_level

if not target_role:
    target_role = state.career_frame.current_role
if not target_level:
    target_level = state.career_frame.current_level

# Aggregate nodes from current level through target level (inclusive)
if target_level == current_level:
    target_nodes = index.by_role_level(target_role, target_level)
else:
    target_nodes = index.by_role_level_range(
        target_role, current_level, target_level
    )
    if not target_nodes:
        target_nodes = index.by_level_range(current_level, target_level)
```

Where `by_level_range` (no role filter) is also added as a fallback.

### Step 4 — Remove dead code in `level_guess.py`

Delete the `_compute_target_readiness` function (lines 32–62) since it is never called and its logic is duplicated inline in `_node` (lines 204–219). This prevents the two implementations from diverging.

### Step 5 — Update `roadmap_select.py` cap (see Task 8)

No code change needed here for the level range — `roadmap_select` already reads from `state.matched_nodes` and filters for `status == "gap"`. Once `compare` populates matched_nodes from the full range, the roadmap automatically spans multi-level gaps.

## Acceptance Criteria

1. A `junior` user aiming for `staff` gets a compatibility score that reflects all `junior` + `mid` + `senior` + `staff` node weights, not just `staff`.
2. A `senior` user aiming for `staff` gets a compatibility score that reflects only `senior` + `staff` node weights.
3. Nodes duplicated across levels (same `id`) are counted only once in the score denominator.
4. `by_role_level_range` returns an empty list when `from_level > to_level`.
5. Dead `_compute_target_readiness` function is removed.
6. All existing tests pass.
7. (See Task 9 for dedicated level-range regression tests.)

## Dependencies

- Task 4 must be implemented (the current `compare.py` already classifies all target-level nodes rather than RAG samples — this task extends that behavior to a range).
