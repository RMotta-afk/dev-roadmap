# Task 12 — Harden Description Objective Extraction in Mock Fallback

## Goal Reference

- **Goal:** Ensure the user's stated objective in their free-text description reliably steers the roadmap direction, even when the LLM is unavailable and the mock/fallback extraction path is used. The LLM prompt already handles this correctly; the mock path does not.
- **Depends on:** None
- **Depended on by:** None

## Problem

`apps/api/src/agent/nodes/analyze.py:308-319` (`_mock_extraction`) only detects an explicit target level if the description contains an English verb ("want"/"aim"/"become") adjacent to the level keyword:

```python
desc_lower = raw_description.lower()
if "staff" in desc_lower and ("want" in desc_lower or "aim" in desc_lower or "become" in desc_lower):
    target_level = "staff"
elif "senior" in desc_lower and ("want" in desc_lower or "aim" in desc_lower or "become" in desc_lower):
    target_level = "senior"
elif "mid" in desc_lower and ("want" in desc_lower or "aim" in desc_lower):
    target_level = "mid"

# If no explicit target, go one level up
if not target_level:
    level_progression = {"junior": "mid", "mid": "senior", "senior": "staff", "staff": "staff"}
    target_level = level_progression.get(current_level, "senior")
```

A Portuguese description like `"meu objetivo é chegar a staff com foco em cloud"` is silently ignored because "staff" is found but none of the required English verb triggers are. The target_level falls back to `level_progression[current_level]` (one level up), completely discarding the user's stated objective.

Similarly, `focus_areas` extraction (lines 325-336) is limited to hardcoded technology keywords — it does not pick up domain-level focus phrases or infer focus from the description's stated intent.

## Affected Files

- `apps/api/src/agent/nodes/analyze.py` — `_mock_extraction` function, target-level / focus-area extraction section (lines 303-336)

## Approach

### Step 1 — Replace the English-verb-gated target-level detection with level-first scanning

Check for any occurrence of a level keyword (`staff`, `senior`, `mid`, `pleno`, `sênior`, `especialista`, `júnior`) in the description. If found AND the context suggests it's an aspirational target (containing common goal-indicating words in PT or EN), use it. Otherwise fall back to the current one-level-up heuristic.

Key changes:
- Remove the `("want" in desc_lower or "aim" in desc_lower or "become" in desc_lower)` gate.
- Instead, scan for level keywords directly in the description text.
- Any explicit level mention in the description that differs from `current_level` is treated as the user's target. If it matches `current_level`, check if goal-indicating words are nearby.
- Add PT-BR level keywords: `"pleno"`, `"sênior"`, `"especialista"`, `"júnior"`, `"senior"`, `"staff"`, `"mid"`.

### Step 2 — Broaden focus-area extraction

Add more technology and domain keywords to the focus-area keyword block (lines 325-336), matching what the LLM prompt explicitly asks the LLM to extract. Include at least:
- `"cloud"`, `"devops"`, `"ml"`, `"machine learning"`, `"ia"`, `"inteligência artificial"`, `"data"`, `"frontend"`, `"backend"`, `"fullstack"`, `"full stack"`, `"mobile"`, `"segurança"`, `"security"`, `"infraestrutura"`, `"infrastructure"`, `"database"`, `"banco de dados"`, `"testes"`, `"testing"`, `"arquitetura"`, `"architecture"`

### Step 3 — Ensure target_role extraction from description

The current mock path always sets `target_role = current_role` (line 322). If the description mentions a different role (e.g. "quero migrar para AI Engineer"), detect it and use it as `target_role`.

## Acceptance Criteria

1. Description `"meu objetivo é chegar a staff com foco em cloud"` with current_level `"mid"` produces `target_level="staff"` and `focus_areas=["Cloud"]`.
2. Description `"I want to become a senior AWS engineer"` with current_level `"mid"` produces `target_level="senior"` and `focus_areas=["AWS"]`.
3. Description `"busco me tornar especialista em IA"` with current_level `"senior"` produces `target_level="staff"` and `focus_areas=["IA"]`.
4. Description with no level mention at all (e.g. `"gosto de programar"`) still falls back to one level above current — no regression.
5. The LLM prompt is not modified; Task 12 only touches the mock extraction path.
6. All existing tests continue to pass.
