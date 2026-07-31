# Task 11 — Remove Pipeline Errors from PDF Output

## Goal Reference

- **Goal:** Stop leaking internal pipeline diagnostics (LLM failure messages, guardrail violations, exception stack traces) into the user-facing downloadable PDF. Pipeline `errors` are operational logs meant for developers, not end users.
- **Depends on:** None
- **Depended on by:** Task 15 (PDF format cleanup touches same file, but logically independent)

## Problem

`apps/api/src/app/pdf/pdf_export.py:272-279` unconditionally renders every string from the `errors` list into the PDF under a section titled "Avisos do pipeline" (Pipeline Warnings):

```python
errors = result.get("errors", [])
if isinstance(errors, list) and errors:
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("<b>Avisos do pipeline</b>", h2_style))
    for err in errors:
        story.append(Paragraph(f"• {err}", bullet_style))
```

These `errors` are internal diagnostic strings populated by the LangGraph pipeline, e.g.:
- `"LLM analysis failed (RuntimeError), using mock extraction"` (`analyze.py:369`)
- `"Guardrail violation: roadmap contains hallucinated items"` (`roadmap_select.py:107`)

Exposing these to the end user is confusing and unprofessional.

## Affected Files

- `apps/api/src/app/pdf/pdf_export.py` — remove lines 272-279

## Approach

Delete the entire `errors` block (lines 272-279). The pipeline errors are already logged server-side via the structured logger; they serve no purpose in the output PDF.

**Before:**
```python
    errors = result.get("errors", [])
    if isinstance(errors, list) and errors:
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("<b>Avisos do pipeline</b>", h2_style))
        for err in errors:
            story.append(Paragraph(f"• {err}", bullet_style))

    doc.build(story)
```

**After:**
```python
    doc.build(story)
```

No other changes needed. The `errors` field in `AgentState` continues to exist for operational logging; it simply is no longer rendered in the PDF.

## Acceptance Criteria

1. A PDF generated from a result with a non-empty `errors` list contains no "Avisos do pipeline" section.
2. A PDF generated from a result with an empty `errors` list is unchanged from before the fix.
3. All existing tests continue to pass.
