"""Analyze node: extract structured profile data from raw text via LLM."""

from __future__ import annotations

from typing import Any
import json

from agent.state import AgentState, CareerFrame, KnownCompetency
from app.config import settings
from llm.client import get_llm_client


# Comprehensive prompt that extracts career context, skills, and competencies from experience
_ANALYZE_SYSTEM_PROMPT = """\
You are an expert CV analysis engine. Analyze the user's CV and description to understand their career context, skills, and goals.

CRITICAL: The user's description often contains their TARGET LEVEL and FOCUS AREAS for development. Pay close attention to phrases like:
- "want to become [level]"
- "aiming for [role]"
- "need to focus on [technology]"
- "preparing for [level] position"

Return ONLY a JSON object with these exact keys:

{
  "current_role": "ai_engineer|software_engineer|frontend_engineer or null",
  "current_level": "junior|mid|senior|staff",
  "target_role": "ai_engineer|software_engineer|frontend_engineer or null (from description goals)",
  "target_level": "junior|mid|senior|staff (from description or one level above current)",
  "focus_areas": ["list of specific technologies or domains they want to focus on from description"],
  "career_summary": "brief trajectory: progression, key transitions",
  "years_of_experience": 0,
  "skills": ["explicit skills mentioned"],
  "technologies": ["technologies, tools, frameworks explicitly mentioned"],
  "domain_areas": ["industry domains or specializations"],
  "projects": [
    {
      "summary": "brief description of significant project or achievement",
      "technologies": ["techs used in this project"],
      "outcomes": ["measurable impacts or results"]
    }
  ],
  "known_competencies": [
    {
      "name": "competency or skill name",
      "evidence": "specific bullet point, project, or achievement that proves it",
      "source": "skill|tech|experience|entailed",
      "confidence": 0.0-1.0
    }
  ],
  "inferred_entailments": [
    {
      "name": "skill/knowledge implied by their work",
      "because": "explanation: they did X so they must know Y"
    }
  ]
}

RULES for known_competencies:
- Extract competencies from EXPERIENCE BULLETS and project highlights, not just skills lists
- Mark source as "experience" when proven through project work
- Mark source as "entailed" when logically required (e.g., "deployed k8s production" → must know Docker, cloud, CI/CD)
- Include high confidence (0.8-1.0) for directly evidenced work
- Include medium confidence (0.5-0.7) for entailed knowledge

RULES for roles:
- ai_engineer: ML, AI, data science, deep learning focus
- software_engineer: general backend, full-stack, systems
- frontend_engineer: UI, web, mobile frontend focus

RULES for levels:
- junior: 0-2 years, learning, guided work
- mid: 2-5 years, independent delivery, some mentoring
- senior: 5-8 years, technical leadership, architecture decisions
- staff: 8+ years, organizational impact, strategic technical vision

If target is not explicitly stated in description, default target_level to ONE level above current_level (staff stays staff).

Do not include any markdown formatting, explanation, or extra text outside the JSON."""


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


def _build_experience_context(profile: dict[str, Any] | None) -> str:
    """Render full experience section with highlights for deep analysis."""
    if not profile:
        return ""
    
    parts: list[str] = []
    
    # Add profile header info
    if profile.get("headline"):
        parts.append(f"Professional Headline: {profile['headline']}")
    if profile.get("summary"):
        parts.append(f"\nSummary: {profile['summary']}")
    if profile.get("top_skills"):
        parts.append(f"\nTop Skills: {', '.join(profile['top_skills'])}")
    
    # Add detailed experiences with highlights (this is the key addition)
    experiences = profile.get("experiences", [])
    if experiences:
        parts.append("\n\nWork Experience:")
        for exp in experiences:
            exp_lines = []
            company = exp.get("company", "Unknown")
            title = exp.get("title", "")
            date_range = exp.get("date_range", "")
            duration = exp.get("duration", "")
            
            header = f"\n• {title} at {company}" if title else f"\n• {company}"
            if date_range:
                header += f" ({date_range})"
            if duration:
                header += f" - {duration}"
            exp_lines.append(header)
            
            highlights = exp.get("highlights", [])
            if highlights:
                for highlight in highlights:
                    exp_lines.append(f"  - {highlight}")
            
            parts.append("\n".join(exp_lines))
    
    return "\n".join(parts)


def _build_messages(
    raw_cv_text: str, raw_description: str, profile: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    experience_context = _build_experience_context(profile)
    user = f"CV:\n{raw_cv_text}\n\nDescription (contains goals and focus):\n{raw_description}"
    if experience_context:
        user = f"{user}\n\nStructured Experience Profile:\n{experience_context}"
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


def _mock_extraction(raw_cv_text: str, raw_description: str, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic mock extraction when no LLM is available."""
    text = f"{raw_cv_text} {raw_description}".lower()
    
    skills: list[str] = []
    technologies: list[str] = []
    domain_areas: list[str] = []
    projects: list[dict] = []
    known_competencies: list[dict] = []
    inferred_entailments: list[dict] = []

    # Very naive keyword spotting for the MVP fallback.
    if "python" in text:
        skills.append("Python")
        technologies.append("Python")
        known_competencies.append({"name": "Python", "evidence": "mentioned in CV", "source": "tech", "confidence": 0.8})
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
        known_competencies.append({"name": "AWS", "evidence": "AWS experience mentioned", "source": "tech", "confidence": 0.7})
    if "docker" in text:
        skills.append("Docker")
        technologies.append("Docker")
        # Docker implies containerization knowledge
        inferred_entailments.append({"name": "Containerization", "because": "Docker experience implies container concepts"})
    if "kubernetes" in text or "k8s" in text:
        skills.append("Kubernetes")
        technologies.append("Kubernetes")
        inferred_entailments.append({"name": "Docker", "because": "Kubernetes requires Docker knowledge"})
        inferred_entailments.append({"name": "Cloud Infrastructure", "because": "K8s deployment requires cloud knowledge"})
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
    if "machine learning" in text or "ml" in text or " ai " in text:
        domain_areas.append("Machine Learning")
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
    
    # Infer role from domain and keywords
    current_role = None
    if "machine learning" in text or "ml engineer" in text or "ai engineer" in text or "data scien" in text:
        current_role = "ai_engineer"
    elif "frontend" in text or "react" in text or "ui" in text:
        current_role = "frontend_engineer"
    else:
        current_role = "software_engineer"
    
    # Infer current level from title keywords and years
    current_level = "junior"
    title_text = ""
    if profile and profile.get("experiences"):
        # Get the most recent title
        first_exp = profile["experiences"][0]
        title_text = (first_exp.get("title", "") or "").lower()
    
    if "staff" in title_text or "principal" in title_text:
        current_level = "staff"
    elif "senior" in title_text or "lead" in title_text or years_of_experience >= 5:
        current_level = "senior"
    elif "mid" in title_text or years_of_experience >= 2:
        current_level = "mid"
    else:
        current_level = "junior"
    
    # Infer target from description
    target_role = None
    target_level = None
    focus_areas = []
    
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
    
    # Infer target role (default to current)
    target_role = current_role
    
    # Extract focus areas from description
    if "aws" in desc_lower or "amazon" in desc_lower:
        focus_areas.append("AWS")
    if "azure" in desc_lower:
        focus_areas.append("Azure")
    if "gcp" in desc_lower or "google cloud" in desc_lower:
        focus_areas.append("GCP")
    if "kubernetes" in desc_lower or "k8s" in desc_lower:
        focus_areas.append("Kubernetes")
    if "react" in desc_lower:
        focus_areas.append("React")
    if "python" in desc_lower:
        focus_areas.append("Python")

    career_summary = f"{current_level.title()} {current_role.replace('_', ' ').title()} with {years_of_experience} years of experience"

    return {
        "current_role": current_role,
        "current_level": current_level,
        "target_role": target_role,
        "target_level": target_level,
        "focus_areas": focus_areas,
        "career_summary": career_summary,
        "skills": skills or ["General Software Engineering"],
        "technologies": technologies or ["Unknown"],
        "years_of_experience": years_of_experience or 1,
        "domain_areas": domain_areas or ["Software Development"],
        "projects": projects,
        "known_competencies": known_competencies,
        "inferred_entailments": inferred_entailments,
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
        extraction = _mock_extraction(state.raw_cv_text, state.raw_description, state.profile)

    # Seed technologies/skills from the structured profile's Top Skills so the
    # deterministic strip output always contributes to the analysis.
    top_skills = (state.profile or {}).get("top_skills", [])
    technologies = _dedupe(list(extraction.get("technologies", [])) + top_skills)
    skills = _dedupe(list(extraction.get("skills", [])) + top_skills)

    # Populate CareerFrame
    state.career_frame = CareerFrame(
        current_role=extraction.get("current_role"),
        current_level=extraction.get("current_level"),
        target_role=extraction.get("target_role"),
        target_level=extraction.get("target_level"),
        focus_areas=extraction.get("focus_areas", []),
        career_summary=extraction.get("career_summary"),
    )

    # Populate known_competencies
    state.known_competencies = []
    for comp in extraction.get("known_competencies", []):
        state.known_competencies.append(
            KnownCompetency(
                name=comp["name"],
                evidence=comp["evidence"],
                source=comp["source"],
                confidence=comp.get("confidence", 1.0),
            )
        )
    
    # Add entailments as competencies
    for entail in extraction.get("inferred_entailments", []):
        state.known_competencies.append(
            KnownCompetency(
                name=entail["name"],
                evidence=entail["because"],
                source="entailed",
                confidence=0.6,  # Medium confidence for inferred knowledge
            )
        )

    # Normalize keys so downstream nodes have a predictable shape.
    state.extracted_skills = {
        "skills": skills,
        "technologies": technologies,
        "years_of_experience": int(extraction.get("years_of_experience", 0)),
        "domain_areas": extraction.get("domain_areas", []),
        "projects": extraction.get("projects", []),
    }
    
    # Keep backward compatibility
    state.level_estimate = state.career_frame.current_level

    return state
