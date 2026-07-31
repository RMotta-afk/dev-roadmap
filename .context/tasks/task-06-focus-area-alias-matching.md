# Task 6 — Improve Focus-Area-Driven Roadmap Prioritization with Alias-Aware Token Matching

## Goal Reference

- **Goal:** Make the mentor's description (direction/goal) actually drive roadmap ordering — when description says "focus on AWS Cloud", the roadmap should surface Cloud-related gaps first, not just when the literal string "AWS Cloud" appears in a node name.
- **Depends on:** Task 5 (full-level-range gap set must be in `state.matched_nodes` for prioritization to span the whole journey)
- **Depended on by:** Task 9 (tests)

## Problem

The current `_prioritize_gaps` in `roadmap_select.py` matches focus phrases **as literal substrings** against `node.name` and `node.category`. This has two bugs:

### Bug 1 — Multi-word focus phrases fail to match single-concept nodes

If the LLM extracts `focus_areas = ["AWS Cloud"]`, the code checks whether the full lowercase phrase `"aws cloud"` is a substring of `node.name.lower()` or `node.category.lower()`. A node named `"AWS"` (category: `"Cloud"`) does NOT match because `"aws cloud"` is not a substring of either field individually. The compound phrase only matches nodes where both words happen to appear contiguously.

### Bug 2 — Node aliases are never checked

`RoadmapNode` has an `aliases: list[str]` field (e.g., `"K8s"` as alias for `"Kubernetes"`, `"OPex"` for `"Otimização de custo vs performance"`), but `_prioritize_gaps` never consults them. If a user says "need to focus on container orchestration" but the node is named "Kubernetes" with no category match, the phrase matches nothing even though `"container orchestration"` could match via an alias.

### Current scoring is too rigid

- Exact match on name/category: +1000
- Substring match on name/category: +500
- Everything else: +0 (only base importance)
- No token-level partial matching, no alias matching, no phrase-decomposition scoring

## Affected Files

- `apps/api/src/agent/nodes/roadmap_select.py` — rewrite `_prioritize_gaps`

## Approach

### Step 1 — Tokenize focus phrases and match against all node fields

Replace the current two-tier (exact then substring) logic with a token-aware scorer:

```python
def _prioritize_gaps(
    gap_matches: list[MatchedNode],
    index: RoadmapIndex,
    focus_areas: list[str],
) -> list[str]:
    if not focus_areas:
        # Base fallback: sort by importance descending
        scored = []
        for match in gap_matches:
            node = index.by_id(match.id)
            if node:
                scored.append((node.importance if node.importance else 50, match.id))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [sid for _, sid in scored]

    # Precompute lowercase versions
    focus_phrases_lower = [f.lower().strip() for f in focus_areas]
    focus_tokens: set[str] = set()
    for phrase in focus_phrases_lower:
        for token in phrase.split():
            focus_tokens.add(token)

    scored_gaps = []
    for match in gap_matches:
        node = index.by_id(match.id)
        if not node:
            continue

        score = 0

        # Collect all searchable strings for this node
        searchable = [
            node.name.lower(),
            node.category.lower(),
        ]
        searchable.extend(a.lower() for a in node.aliases)

        # Priority 1: Exact phrase match in category or name (highest)
        for phrase in focus_phrases_lower:
            for s in searchable[:2]:  # name and category only
                if phrase == s:
                    score += 1000
                    break

        # Priority 2: Token-level matches (medium boost, per token)
        token_count = 0
        for s in searchable:
            for token in focus_tokens:
                if token in s.split():  # whole-word match within searchable string
                    token_count += 1

        score += min(token_count * 300, 900)  # cap at 3 tokens' worth

        # Priority 3: Substring match in any searchable field (lower than token)
        for phrase in focus_phrases_lower:
            for s in searchable:
                if phrase in s:
                    score += 200
                    break

        # Priority 4: Importance as tiebreaker
        score += node.importance if node.importance else 50

        scored_gaps.append((score, match.id))

    scored_gaps.sort(reverse=True, key=lambda x: x[0])
    return [gap_id for _, gap_id in scored_gaps]
```

### Step 2 — Edge cases to handle

- **Empty focus_areas**: Fall back to importance-only sorting (already handled by the early return above).
- **Single focus phrase with single token** (e.g., `"AWS"`): Behave similarly to today but also checks aliases, improving recall.
- **Single focus phrase with multiple tokens** (e.g., `"AWS Cloud"`): Previously matched nothing unless a node literally contained the substring "AWS Cloud". Now matches nodes containing "aws" token OR "cloud" token (each +300), plus substring match on the whole phrase (+200).
- **Multiple focus phrases** (e.g., `["AWS", "React"]`): Each phrase contributes tokens independently; nodes matching multiple focus areas compound their score.

### Step 3 — Verify priority-surfacing in results output

No UI changes required — the roadmap is already displayed in priority order (`state.personalized_roadmap` preserves the insertion order from `prioritized_ids`).

## Acceptance Criteria

1. Focus phrase `"AWS Cloud"` boosts a node named `"AWS"` (category `"Cloud"`) — exact phrase match on category `"Cloud"` (+1000) plus token match for `"aws"` (+300).
2. Focus phrase `"container orchestration"` boosts a node named `"Kubernetes"` whose aliases include `"container orchestration"`.
3. Focus phrase `"container orchestration"` boosts a node whose category is `"Container Orchestration"` via exact match.
4. Nodes matching no focus phrase still appear in the roadmap (sorted by importance), not silently dropped.
5. Empty `focus_areas` returns all gaps sorted by importance descending.
6. Performance: linear scan over gap matches with O(n * k) where k = tokens × searchable fields (small).

## Dependencies

- Task 5 must be complete (ensures gap_matches includes nodes from the full current→target level range).
