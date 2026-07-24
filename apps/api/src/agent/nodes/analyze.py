"""Analyze node: extract structured profile data from raw text via LLM."""

from __future__ import annotations

import json
from typing import Any

import httpx

from agent.state import AgentState
from app.config import settings


# Structured prompt that asks the model to return valid JSON.
_ANALYZE_SYSTEM_PROMPT = """\
You are a CV analysis engine. Extract the following fields from the user's CV text and job description.
Return ONLY a JSON object with these exact keys:
- skills: list of professional skills mentioned
- technologies: list of technologies, tools, or frameworks mentioned
- years_of_experience: integer total years of professional experience
- domain_areas: list of domain or industry areas mentioned

Do not include any markdown formatting, explanation, or extra text."""


def _build_messages(raw_cv_text: str, raw_description: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _ANALYZE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"CV:\n{raw_cv_text}\n\nDescription:\n{raw_description}",
        },
    ]


async def _call_llm(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Call OpenAI-compatible chat completions endpoint."""
    if not settings.llm_api_key:
        raise RuntimeError("LLM API key is not configured")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.embedding_model,  # fallback reuse; override with dedicated chat model if desired
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


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
        messages = _build_messages(state.raw_cv_text, state.raw_description)
        extraction = await _call_llm(messages)
    except Exception as exc:
        state.errors.append(f"LLM analysis failed ({type(exc).__name__}), using mock extraction")
        extraction = _mock_extraction(state.raw_cv_text, state.raw_description)

    # Normalize keys so downstream nodes have a predictable shape.
    state.extracted_skills = {
        "skills": extraction.get("skills", []),
        "technologies": extraction.get("technologies", []),
        "years_of_experience": int(extraction.get("years_of_experience", 0)),
        "domain_areas": extraction.get("domain_areas", []),
    }

    return state
