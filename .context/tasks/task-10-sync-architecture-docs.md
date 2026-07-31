# Task 10 — Sync Architecture Documentation

## Goal Reference

- **Goal:** Update `docs/sdd/architecture.md` to reflect the four behavioral changes: level-range scoring, alias-aware focus prioritization, methodology entailment reasoning, and 25-item roadmap cap.
- **Depends on:** Tasks 5, 6, 7, 8 (implementation must be complete to document final behavior)
- **Depended on by:** None

## Problem

The architecture document (`docs/sdd/architecture.md`) describes the agent graph behavior in ways that are now inaccurate after the four fixes:

1. **Section 9, `compare` node description (line 154-155):** Says "call C-RAG retriever for relevant Base Roadmap nodes matching extracted skills; identify gaps." This is misleading — `compare.py` now classifies **all** target role+level nodes using the `RoadmapIndex` directly, falling back to embedding similarity for gap re-classification, not RAG retrieval per se.

2. **Section 9, `level_guess` node description (line 156-157):** Says "compute `compatibility_score` (0-100)" without specifying that the denominator includes all nodes from the user's current level through target level. Should be explicit about the level-range semantics.

3. **Section 9, `roadmap_select` node description (line 158-159):** Says "select subset of nodes addressing gaps/next steps" without mentioning the 25-item cap or the focus-area prioritization algorithm.

4. **No mention of `inferred_entailments` or methodology reasoning** in the `analyze` node description (line 152-153).

## Affected Files

- `docs/sdd/architecture.md` — Sections 9 (Agentic Layer), possibly Section 8 (RAG/compare layer) if it references the compare mechanism

## Approach

### Step 1 — Update Section 9 `analyze` node description

**Current (lines 152-153):**
```
3. `analyze` — LLM tool-call with structured schema: extract skills,
   technologies, years of experience, domain areas.
```

**Updated:**
```
3. `analyze` — LLM tool-call with structured schema: extract skills,
   technologies, years of experience, domain areas, known_competencies
   (evidence-based), and inferred_entailments (methodology/practice
   implications from experience descriptions).
```

### Step 2 — Update Section 9 `compare` node description

**Current (lines 154-155):**
```
4. `compare` — call C-RAG retriever for relevant Base Roadmap nodes
   matching extracted skills; identify gaps.
```

**Updated:**
```
4. `compare` — classify ALL target role+level nodes spanning the
   range from current_level through target_level (inclusive) against
   the user's extracted skills and known competencies. Each node is
   marked as covered / known_via_experience / gap via: (a) exact
   skill/alias intersection, (b) competency name match, (c) embedding
   cosine-similarity fallback (threshold 0.75).
```

### Step 3 — Update Section 9 `level_guess` node description

**Current (lines 156-157):**
```
5. `level_guess` — estimate seniority (junior/mid/senior/staff) +
   trajectory narrative; compute `compatibility_score` (0-100).
```

**Updated:**
```
5. `level_guess` — estimate seniority (junior/mid/senior/staff) +
   trajectory narrative; compute `compatibility_score` (0-100) as
   weighted coverage of all roadmap nodes from current_level through
   target_level (not just the target level alone). Score = sum of
   importance weights for covered+experience nodes ÷ sum of all
   node importance in the level range.
```

### Step 4 — Update Section 9 `roadmap_select` node description

**Current (lines 158-159):**
```
6. `roadmap_select` — select subset of nodes addressing gaps/next steps;
   emit `personalized_roadmap`.
```

**Updated:**
```
6. `roadmap_select` — select up to 25 gap nodes prioritized by:
   (a) tokenized focus-area match against node name, category, and
   aliases (exact phrase gets highest boost, individual tokens get
   per-token boost), then (b) importance as tiebreaker. Passes strict-
   subset validation (ADR-008) before emission.
```

## Acceptance Criteria

1. All four agent node descriptions are accurate after the changes.
2. No paragraph is removed — only text is updated in place.
3. The strict-subset guardrail (ADR-008) description remains unchanged (lines 160-163).
4. No other sections of the document are modified.
