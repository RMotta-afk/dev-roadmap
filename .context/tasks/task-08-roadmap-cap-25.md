# Task 8 — Bump Roadmap Objective Cap from 20 to 25

## Goal Reference

- **Goal:** Increase the maximum number of objectives in the personalized roadmap from 20 to 25, giving users more comprehensive coverage of the full current→target journey.
- **Depends on:** Task 5 (level-range expansion means we now have more gaps across multiple levels; bumping the cap lets the user see the whole picture)
- **Depended on by:** Task 9 (update test asserting cap)

## Problem

`apps/api/src/agent/nodes/roadmap_select.py:63` hardcodes the roadmap to 20 items:

```python
for nid in prioritized_ids[:20]:  # cap at 20 items
```

This limit was set when the roadmap only contained gaps from a single level. With Task 5 expanding gap selection across the current→target level range (potentially spanning junior + mid + senior + staff), 20 items may truncate important gaps from intermediate levels.

## Affected Files

- `apps/api/src/agent/nodes/roadmap_select.py` — change `[:20]` to `[:25]`

## Approach

Single-line change at `roadmap_select.py:63`:

```python
# Before:
for nid in prioritized_ids[:20]:  # cap at 20 items

# After:
for nid in prioritized_ids[:25]:  # cap at 25 items
```

No other changes needed. The validator guardrail (`is_valid_subset`) and prioritization logic are unaffected.

## Acceptance Criteria

1. A user with 25+ gap nodes across their level range receives exactly 25 roadmap items (not 20).
2. A user with fewer than 25 gap nodes continues to receive all of them (no behavioral change for small gap sets).
3. No regression in the strict-subset guardrail (ADR-008).
