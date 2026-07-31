# Task 14 — Bump Roadmap Cap from 25 to 35

## Goal Reference

- **Goal:** Increase the maximum number of objectives in the personalized roadmap from 25 to 35, accommodating the larger pool of gap nodes produced by Task 13 (cross-level focus gaps).
- **Depends on:** Task 13 (cross-level focus gaps produce more gap nodes, making a higher cap necessary)
- **Depended on by:** Task 9 (test asserting the cap value must be updated). Note: supersedes Task 8 which previously bumped the cap from 20→25.

## Problem

`apps/api/src/agent/nodes/roadmap_select.py:93` hardcodes the roadmap to 25 items:

```python
for nid in prioritized_ids[:25]:  # cap at 25 items
```

This limit was set before cross-level focus gaps (Task 13) expanded the pool of candidate nodes. With foundational junior-level nodes now potentially included for a user's focus areas, 25 items may truncate important prerequisite skills that the user needs but that rank lower in prioritization.

## Affected Files

- `apps/api/src/agent/nodes/roadmap_select.py:93` — change `[:25]` to `[:35]`
- `apps/api/tests/` — update existing test `test_roadmap_capped_at_25` → `test_roadmap_capped_at_35` (or equivalent, depending on where the test was placed by Task 9)
- `docs/sdd/architecture.md` — update the `roadmap_select` node description from "up to 25" → "up to 35" (section 9, line 89 in current SDD per Task 10)

## Approach

### Step 1 — Change the cap constant

**Before** (`roadmap_select.py:93`):
```python
for nid in prioritized_ids[:25]:  # cap at 25 items
```

**After:**
```python
for nid in prioritized_ids[:35]:  # cap at 35 items
```

### Step 2 — Update the test

Find and update the test that asserts the cap value (likely `test_roadmap_capped_at_25` created by Task 9). Rename it and update the assertion from `25` → `35`. Also update `test_roadmap_returns_all_when_under_cap` to use a value < 35 instead of < 25.

### Step 3 — Update architecture docs

In `docs/sdd/architecture.md`, find the `roadmap_select` node description (section 9, the line saying "up to 25 gap nodes") and change `25` to `35`.

## Acceptance Criteria

1. A user with 35+ gap nodes across their level range receives exactly 35 roadmap items (not 25).
2. A user with fewer than 35 gap nodes continues to receive all of them.
3. The test assertion is updated to expect 35.
4. The SDD no longer mentions 25 as the cap.
5. No regression in the strict-subset guardrail (ADR-008).
