# Task 2 — Make Experience-Derived Competencies Count in Analysis (Embedding Similarity)

## Goal Reference

- **Goal:** G9 (Make experience competencies count via embedding similarity)
- **Depends on:** None (can run independently of Task 1)
- **Depended on by:** G11 (compatibility score needs accurate classification to be meaningful)

## Problem

The analysis pipeline treats CV experience as invisible for roadmap matching. Even when the LLM correctly extracts a competency like "Otimização de custo e performance" (or its English equivalent) from work experience bullets, it never counts as a "known" skill against the roadmap because the matching logic (`compare_node`) requires **exact string equality** between the user's skills/competencies and the roadmap node's `name` or `aliases`.

### Root Cause 1 — Empty aliases

`apps/api/src/roadmap/archive_parser.py:295` hardcodes `"aliases": []` on every generated `RoadmapNode`. The aliases field was meant to capture Portuguese/English synonyms and related terms, but it's never populated, so exact-match matching fails for any non-literal name comparison.

### Root Cause 2 — Exact-match-only classification in `compare_node`

`apps/api/src/agent/nodes/compare.py:113-126`:

```python
# Check 1: Exact match in user's explicit skills
if node_aliases & user_skills:
    status = "covered"
    reason = "Explicitly listed in skills/technologies"
else:
    # Check 2: Match through known competencies (experience-based)
    for alias in node_aliases:
        if alias in competency_map:
            ...
```

`node_aliases` = `{normalized(node.name)} ∪ normalized(aliases)`. Since aliases is always empty, the only way a roadmap node gets classified as `covered` is if the user's CV literally used the exact Portuguese string that appears as the node's `name` (e.g., "Otimização de custo vs performance"). Any English term from an English LinkedIn export ("cost optimization", "performance tuning") will **never** match.

Similarly, `known_competencies` extracted from experience must exactly equal a roadmap node name to trigger `known_via_experience`. Since `competency_map` maps normalized names to evidence, and the keys come from the LLM's extraction (which may produce different phrasing than roadmap names), most experience-derived competencies silently fall through to `status = "gap"`.

### Root Cause 3 — No semantic similarity mechanism

The RAG retriever uses embeddings to find semantically relevant nodes by skill query terms (`compare.py:82-98`), but the **classification** of retrieved nodes into covered/known/gap is purely string-based. The embedding similarity score returned by retrieval is never used for classification — only the retrieved node objects are kept, and classification is exact-match only.

## Affected Files

- `apps/api/src/agent/nodes/compare.py` — add embedding-similarity fallback in classification
- `apps/api/src/roadmap/archive_parser.py` — populate aliases at parse time (optional; improves deterministic matching)
- `apps/api/src/agent/nodes/analyze.py` — improve experience extraction prompt to produce more roadmap-aligned competency names (optional; improves signal quality)
- `apps/api/src/rag/retriever.py` — may need minor adjustment to return similarity scores alongside nodes

## Approach

### Step 1 — Populate aliases in archive_parser.py (deterministic improvement)

During `generate_nested_structure` (archive_parser.py:179-310), for each group's skill items, populate the `aliases` array with:
1. The skill `description` itself (primary name)
2. Any common English translation or synonym (hand-curated mapping for MVP; can be expanded with LLM later)

This is purely a data-fix — it doesn't change the matching architecture, just enriches the available matching surface.

### Step 2 — Add embedding-similarity fallback in compare_node

In `compare_node` (compare.py:21-138), after the exact-match checks (Check 1 and Check 2) fail for a node, add an embedding-similarity check:

```python
# Check 3: Embedding similarity fallback
if not evidence:
    for alias in node_aliases:
        sim = await retriever.similarity(alias, node.name, node_aliases)
        if sim >= 0.75:
            status = "known_via_experience"
            reason = f"Semantically similar to experience evidence"
            evidence = f"Alias: {alias}"
            break
```

Implementation options for the similarity check:
- **Option A**: Use the `EmbeddingService` to embed the candidate alias and compute cosine similarity against the node's existing embedding (stored in the Qdrant payload). This is lightweight — the node already has an embedding from seeding.
- **Option B**: Use the retriever to query with the alias text and check if the node appears in results with a high score. Reuses existing infrastructure.

Option A is cleaner and more precise. Implementation:
1. Add an `embedding` field to `RoadmapNode` payload (already exists in Qdrant, just need to expose it in the model).
2. Embed each alias from the user's competencies at classification time.
3. Compute cosine similarity against the candidate node's stored embedding.
4. If `similarity >= 0.75`, classify as `known_via_experience`.

### Step 3 — Improve analyze.py extraction prompt (optional, improves signal)

In `analyze.py:14` (`_ANALYZE_SYSTEM_PROMPT`), add rules for `known_competencies` extraction that encourage producing competency names that are closer to roadmap node names:
- Map English experience terms to their Portuguese roadmap equivalents where applicable
- Include both the original CV term and a suggested canonical term in the extraction

## Acceptance Criteria

1. Given a CV that mentions "reduced cloud costs by 30%" in experience bullets, the analysis classifies the node "Otimização de custo vs performance" (backend Staff Group 17.4) as `known_via_experience`, not `gap`.
2. Given an English LinkedIn export mentioning "performance tuning", the node "Otimização de custo vs performance" gets `known_via_experience` status.
3. Exact-match behavior is preserved — nodes that match by name still get `covered` (not demoted to `known_via_experience`).
4. The embedding-similarity fallback is **not** triggered for completely unrelated terms (false positives ≤ 5% on a manually curated test set of 20 sample nodes).
5. Existing tests pass after changes.

## Dependencies

- Task 1 (Staff roadmap parsing) — needed for Staff-level nodes to exist in Qdrant and RoadmapIndex so similarity can be measured against them.
- The `EmbeddingService` must already be functional (it is — used in retriever for startup seeding and queries).