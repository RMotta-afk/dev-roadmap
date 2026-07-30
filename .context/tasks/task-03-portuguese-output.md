# Task 3 — Force Portuguese-Only Analysis Output (API Scope)

## Goal Reference

- **Goal:** G10 (Portuguese-only output)
- **Depends on:** None (independent; can run in parallel with any other task)
- **Depended on by:** None (standalone content fix)

## Problem

The analysis output is inconsistently bilingual — roadmap nodes and source data are Portuguese, but the LLM-generated narrative (summary, strengths, weaknesses), hardcoded reason strings, and fallback text are in English. This is especially problematic when the CV input (e.g., an English LinkedIn export) triggers English-language output from the LLM, which contradicts the user's expectation that the entire analysis is in Portuguese.

## Current State

### What's already Portuguese
- Roadmap source data (`docs/archives/*.md`, `data/roadmaps/*`) — Portuguese ✓
- PDF export (`apps/api/src/app/pdf/pdf_export.py`) — fully Portuguese with `_translate_level()` dict and Portuguese section headers ✓
- Roadmap node names/categories in `data/roadmaps/*` — Portuguese ✓

### What's still in English

1. **`apps/api/src/agent/nodes/level_guess.py` lines 14-25** — `_LEVEL_RESUME_SYSTEM_PROMPT` is English:
   - `"You are a career development advisor."`
   - `"Return ONLY a JSON object with these exact keys"`
   - `"based on the user's career context, current skills, and gaps toward their target role/level"`
   - `"Be specific, actionable, and encouraging."`

2. **`apps/api/src/agent/nodes/level_guess.py` lines 128-171** — `_generate_level_resume_template()` fallback:
   - `"Currently assessed as {current_level} {current_role}"`
   - `"Target: {target_level} {target_role}"`
   - `"Continue building expertise in identified gap areas to reach your target level."`

3. **`apps/api/src/agent/nodes/compare.py` lines 115-125** — hardcoded reason strings:
   - `"Explicitly listed in skills/technologies"` (line 116)
   - `"Demonstrated through work experience"` (line 124)

4. **`apps/api/src/agent/nodes/analyze.py` lines 288** — fallback `career_summary`:
   - `f"{current_level.title()} {current_role.replace('_', ' ').title()} with {years_of_experience} years of experience"`

5. **`apps/api/src/agent/nodes/analyze.py` lines 14-79** — `_ANALYZE_SYSTEM_PROMPT` — the LLM prompt is English. While this is the prompt that drives the LLM's extraction logic, the output (extracted JSON values like `summary`, `strong_points`, `weak_points`) should be forced to Portuguese regardless of prompt language. However, the prompt itself is an internal orchestration tool and changing it to Portuguese could reduce LLM extraction accuracy (prompts in English tend to produce better-structured JSON from models trained primarily on English). The fix here is to add a Portuguese output constraint to the prompt instead of translating the whole prompt.

## Affected Files

- `apps/api/src/agent/nodes/level_guess.py` — translate system prompt + template fallback to Portuguese
- `apps/api/src/agent/nodes/compare.py` — translate reason strings to Portuguese
- `apps/api/src/agent/nodes/analyze.py` — translate fallback `career_summary` template to Portuguese + add Portuguese output instruction to LLM prompt (not translate the prompt itself)

## Approach

### Step 1 — Translate `_LEVEL_RESUME_SYSTEM_PROMPT` (level_guess.py:14-25) to Portuguese

```python
_LEVEL_RESUME_SYSTEM_PROMPT = """\
Você é um consultor de desenvolvimento de carreira. Com base no contexto
profissional do usuário, habilidades atuais e lacunas até o cargo/nível
alvo, forneça uma avaliação concisa.

Retorne SOMENTE um objeto JSON com estas chaves exatas:
{
  "summary": "resumo de 2-3 frases: trajetória atual, prontidão para o alvo,
             no que focar a seguir",
  "strong_points": ["3-5 pontos fortes demonstrados com evidências"],
  "weak_points": ["3-5 maiores lacunas rumo ao nível/cargo alvo"]
}

Seja específico, prático e encorajador. Foque no que importa para
alcançar o objetivo.
Não inclua formatação markdown, explicações ou texto extra fora do JSON."""
```

### Step 2 — Translate `_generate_level_resume_template` fallback (level_guess.py:128-171) to Portuguese

Key translations:
- `"Currently assessed as"` → `"Avaliado atualmente como"`
- `"Target:"` → `"Alvo:"`
- `"Continue building expertise in identified gap areas to reach your target level."` → `"Continue desenvolvendo expertise nas lacunas identificadas para alcançar seu nível alvo."`

### Step 3 — Translate hardcoded reason strings in compare.py

- Line 116: `"Explicitly listed in skills/technologies"` → `"Listado explicitamente em habilidades/tecnologias"`
- Line 124: `"Demonstrated through work experience"` → `"Demonstrado por meio de experiência profissional"`

### Step 4 — Translate fallback career_summary in analyze.py (line 288)

- `f"{current_level.title()} {current_role.replace('_', ' ').title()} with {years_of_experience} years of experience"`
- → `f"{current_level.title()} {current_role.replace('_', ' ').title()} com {years_of_experience} anos de experiência"`

### Step 5 — Add Portuguese output constraint to analyze.py LLM prompt

In `_ANALYZE_SYSTEM_PROMPT` (analyze.py:14-79), **do NOT translate the prompt to Portuguese** (keeping it in English preserves extraction quality). Instead, add a Portuguese output constraint at the end:

```
RULES for output language:
- All string values in the JSON response must be in Portuguese (Brazilian),
  including summary, known_competencies names, inferred_entailments names,
  career_summary, and project descriptions.
```

This ensures that:
1. LLM extraction quality stays high (English prompt for structured output)
2. All user-facing output content is forced to Portuguese regardless of CV language

## Acceptance Criteria

1. Running the full analysis pipeline with an English CV (e.g., LinkedIn export) produces Portuguese `level_resume.summary`, `level_resume.strong_points`, and `level_resume.weak_points`.
2. The fallback template (`_generate_level_resume_template`) outputs Portuguese text without LLM call (verifiable by running with `settings.llm_api_key = ""`).
3. All `matched_nodes[].reason` fields are in Portuguese (e.g., `"Listado explicitamente em habilidades/tecnologias"`, `"Demonstrado por meio de experiência profissional"`).
4. The mock extraction fallback `career_summary` is in Portuguese.
5. Existing tests pass after changes.
6. The LLM system prompt is NOT translated to Portuguese (preserves extraction quality); only output values and fallback text are translated.

## Dependencies

None — independent of all other tasks.