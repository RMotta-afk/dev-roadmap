"""Analyze node: extract structured profile data from raw text via LLM."""

from __future__ import annotations

from typing import Any

from agent.state import AgentState
from app.config import settings
from llm.client import get_llm_client


# Structured prompt that asks the model to return valid JSON.
_ANALYZE_SYSTEM_PROMPT = """\
You are a CV analysis engine. Extract the following fields from the user's CV text and job description.
Return ONLY a JSON object with these exact keys:
- skills: list of professional skills mentioned
- technologies: list of technologies, tools, or frameworks mentioned
- years_of_experience: integer total years of professional experience
- domain_areas: list of domain or industry areas mentioned

Do not include any markdown formatting, explanation, or extra text."""


def _dedupe(items: list[str]) -> list[str]:
    """Preserve order while removing case-insensitive duplicates."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def _profile_hint(profile: dict[str, Any] | None) -> str:
    """Render a compact hint from a structured LinkedInProfile, if present."""
    if not profile:
        return ""
    parts: list[str] = []
    if profile.get("top_skills"):
        parts.append("Top Skills: " + ", ".join(profile["top_skills"]))
    if profile.get("headline"):
        parts.append(f"Headline: {profile['headline']}")
    if profile.get("summary"):
        parts.append(f"Summary: {profile['summary']}")
    return "\n".join(parts)


def _build_messages(
    raw_cv_text: str, raw_description: str, profile: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    hint = _profile_hint(profile)
    user = f"CV:\n{raw_cv_text}\n\nDescription:\n{raw_description}"
    if hint:
        user = f"{user}\n\nStructured profile:\n{hint}"
    return [
        {"role": "system", "content": _ANALYZE_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


async def _call_llm(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Call the LLM via the shared ModelClient."""
    if not settings.llm_api_key:
        raise RuntimeError("LLM API key is not configured")
    client = get_llm_client()
    return await client.chat_json(messages)


def _mock_extraction(raw_cv_text: str, raw_description: str) -> dict[str, Any]:
    """Return a deterministic mock extraction when no LLM is available."""
    text = f"{raw_cv_text} {raw_description}".lower()
    skills: list[str] = []
    technologies: list[str] = []
    domain_areas: list[str] = []

    # Very naive keyword spotting for the MVP fallback.
    if "python" in text:
        skills.append("Python")
        technologies.append("Python")
    if "javascript" in text or "js" in text:
        skills.append("JavaScript")
        technologies.append("JavaScript")
    if "react" in text:
        skills.append("React")
        technologies.append("React")
    if "node" in text or "nodejs" in text:
        skills.append("Node.js")
        technologies.append("Node.js")
    if "aws" in text:
        skills.append("AWS")
        technologies.append("AWS")
    if "docker" in text:
        skills.append("Docker")
        technologies.append("Docker")
    if "sql" in text or "database" in text:
        skills.append("SQL")
    if "agile" in text:
        skills.append("Agile")
    if "team lead" in text or "lead" in text:
        skills.append("Leadership")
    if "frontend" in text or "front-end" in text:
        domain_areas.append("Frontend Development")
    if "backend" in text or "back-end" in text:
        domain_areas.append("Backend Development")
    if "devops" in text:
        domain_areas.append("DevOps")
    if "web" in text:
        domain_areas.append("Web Development")
    if "mobile" in text:
        domain_areas.append("Mobile Development")
    if not domain_areas:
        domain_areas.append("Software Development")

    # Heuristic years of experience from text.
    years_of_experience = 0
    for token in text.split():
        token = token.strip(".,;:+yearsyr")
        if token.isdigit():
            val = int(token)
            if 1 <= val <= 40:
                years_of_experience = max(years_of_experience, val)

    return {
        "skills": skills or ["General Software Engineering"],
        "technologies": technologies or ["Unknown"],
        "years_of_experience": years_of_experience or 1,
        "domain_areas": domain_areas or ["Software Development"],
    }


async def analyze_node(state: AgentState) -> AgentState:
    """Extract structured skills and profile data from raw text.

    Uses an LLM when an API key is available; otherwise falls back to a
    deterministic mock extraction so the graph can still execute end-to-end.
    """
    state.errors = list(state.errors)

    try:
        messages = _build_messages(state.raw_cv_text, state.raw_description, state.profile)
        extraction = await _call_llm(messages)
    except Exception as exc:
        state.errors.append(f"LLM analysis failed ({type(exc).__name__}), using mock extraction")
        extraction = _mock_extraction(state.raw_cv_text, state.raw_description)

    # Seed technologies/skills from the structured profile's Top Skills so the
    # deterministic strip output always contributes to the analysis.
    top_skills = (state.profile or {}).get("top_skills", []) # change top_skills to skills
    technologies = _dedupe(list(extraction.get("technologies", [])) + top_skills)
    skills = _dedupe(list(extraction.get("skills", [])) + top_skills)

    # Normalize keys so downstream nodes have a predictable shape.
    state.extracted_skills = {
        "skills": skills,
        "technologies": technologies,
        "years_of_experience": int(extraction.get("years_of_experience", 0)),
        "domain_areas": extraction.get("domain_areas", []),
    }

    return state
