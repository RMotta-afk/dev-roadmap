# Task 4 — Fix Compatibility Score Using Full Target Roadmap (Unified Gap Selection)

## Goal Reference

- **Goal:** G11 (Fix compatibility score + unify gap selection)
- **Depends on:** Task 1 (Staff nodes must exist in RoadmapIndex so they can be scored) + Task 2 (better matching = better classification accuracy = meaningful score)
- **Depended on by:** None (consumer-facing fix)

## Problem

The compatibility score is structurally broken in two ways:

### Root Cause 1 — Denominator is only the RAG-retrieved subset, not the full target roadmap

`level_guess.py:200-216`:

```python
covered_weight = 0.0
total_weight = 0.0
for match in state.matched_nodes:
    node = index.by_id(match.id)
    if node:
        weight = float(node.importance) if node.importance else 50.0
        total_weight += weight
        if match.status in ("covered", "known_via_experience"):
            covered_weight += weight
```

But `state.matched_nodes` comes from `compare_node`, which only classifies nodes **retrieved by RAG queries seeded from the user's own skill/tech/competency terms** (`compare.py:82-98`). Nodes that the user has zero signal for are never queried, never retrieved, and never appear in `matched_nodes` — so they're invisible to the score.

Example: A user targeting Staff backend has no mention of "Otimização de custo vs performance" anywhere in their CV. The RAG query for their existing skills never returns this node. Therefore: (a) it's not in `matched_nodes`, (b) it doesn't count toward `total_weight`, and (c) it doesn't count as a gap either. The result: the score is inflated because the denominator only includes nodes semantically close to what the user already claims to know.

The **correct** denominator is `Σ(importance)` for **every node** in the target role + target level from `RoadmapIndex.by_role_level()`.

### Root Cause 2 — `compare_node` doesn't produce a complete classification map

`compare.py:82-98` uses RAG retrieval per query term:

```python
for item in query_terms:
    results: list[RoadmapNode] = await retriever.retrieve(
        item, role=target_role, level=target_level, top_k=5
    )
```

This produces a biased sample of nodes — it never sees nodes that are irrelevant to the user's existing skills. So: (a) the score is wrong, and (b) the personalized roadmap's gap list (from `roadmap_select_node`) also uses only the RAG-retrieved nodes, meaning the user's personalized roadmap can miss entire categories of gaps.

### Root Cause 3 — `roadmap_select_node` uses the same biased `matched_nodes`

`roadmap_select.py:48-51`:

```python
matched = state.matched_nodes or []
gap_matches = [m for m in matched if m.status == "gap"]
```

Since `matched` only contains RAG-retrieved nodes, the personalized roadmap is built from an incomplete gap set. True gaps (the entire Staff backend curriculum if the user has no signal for it) are invisible.

## Affected Files

- `apps/api/src/agent/nodes/compare.py` — refactor to classify ALL target role+level nodes instead of only RAG-retrieved ones
- `apps/api/src/agent/nodes/level_guess.py` — fix score denominator to use full target node set
- `apps/api/src/agent/nodes/roadmap_select.py` — use complete gap set from compare_node
- `apps/api/src/roadmap/index.py` — add helper to get all nodes for a role+level (already exists via `by_role_level`)
- `apps/api/src/agent/state.py` — may need `matched_nodes` semantics adjusted (currently stores RAG-retrieved; may need a separate `all_target_nodes` field, or repurpose the same field)

## Approach

### Step 1 — Refactor `compare_node` to classify the complete target node set

**Current behavior**: iterate over user skill/tech/competency query terms → RAG retrieve → classify only retrieved nodes.

**New behavior**: 
1. Get all target nodes via `index.by_role_level(target_role, target_level)` (already available).
2. Build user skill/tech/competency sets as before (for classification).
3. For each node in the full target set, classify as `covered` / `known_via_experience` / `gap` using the enhanced matching:
   - `covered`: node name/aliases ∩ user explicit skills → fast set intersection
   - `known_via_experience`: competency + embedding similarity fallback (Task 2's improvement)
   - `gap`: everything else

This is the core architectural change. The RAG retrieval still runs (needed for semantic retrieval ranking), but classification now happens against the full node set, not just the RAG sample.

Key code change in `compare.py`:
```python
# Get ALL target nodes for classification (not just RAG-retrieved)
target_nodes = index.by_role_level(target_role, target_level)
# Fall back to all nodes of the target level if role-level returns nothing
if not target_nodes:
    target_nodes = index.by_level(target_level)

seen_ids: set[str] = set()
matched_nodes: list[MatchedNode] = []

for node in target_nodes:
    if node.id in seen_ids:
        continue
    seen_ids.add(node.id)
    status, reason, evidence = _classify_node(node, user_skills, competency_map, retriever)
    matched_nodes.append(MatchedNode(id=node.id, status=status, reason=reason, evidence=evidence))
```

Where `_classify_node` encapsulates the existing 3-check logic (exact → competency → embedding similarity).

### Step 2 — Fix `level_guess_node` denominator

`level_guess.py:200-216` already uses `state.matched_nodes`, so once Step 1 is done (compare_node produces the complete set), the score denominator is automatically correct. No separate change needed here.

The score formula itself (`_compute_compatibility_score`) is correct — it just needs the corrected input.

### Step 3 — Unify `roadmap_select_node` gap selection with complete set

`roadmap_select.py:48-51` already reads from `state.matched_nodes` and filters for `status == "gap"`. Once Step 1 is done, `matched_nodes` contains the complete gap set, so gap prioritization automatically uses all true gaps instead of the biased RAG sample.

No separate code change needed here either — the unification happens naturally through Step 1.

### Step 4 — Add unit tests

Create tests for:
1. `_compute_compatibility_score` edge cases (0 weight, all covered, all gaps, clamping)
2. Full score computation with a mock `RoadmapIndex` containing known nodes at known importance weights, verifying that:
   - Score = 0 when no nodes are covered
   - Score = 100 when all nodes are covered
   - Score is correct for partial coverage (weighted by importance)
   - Nodes not in the target role/level are excluded from denominator
3. Test that a user with empty skills gets score 0 for any non-trivial target (exposing the previous bug where the denominator was artificially small)

## Acceptance Criteria

1. Given a Staff backend user with no skills mentioned in their CV, the compatibility score is 0 (not inflated to 50%+ from partial RAG match on unrelated terms).
2. Given a Staff backend user with all Staff-level skills explicitly listed in their CV, the score is 100.
3. Score is weighted by `importance` (default 50) — a node with `importance: 80` contributes 80 weight, not 50.
4. The personalized roadmap in the final result includes ALL gap nodes from the complete target roadmap, not just nodes retrieved via RAG on user's existing terms.
5. Unit tests for `_compute_compatibility_score` pass (currently 0 test coverage on this formula).
6. No regression on existing integration tests.

## Dependencies

- Task 1 (Staff nodes must exist in data/roadmaps + RoadmapIndex for scoring to work at Staff level)
- Task 2 (embedding similarity fallback improves coverage of matched_nodes → better score accuracy)