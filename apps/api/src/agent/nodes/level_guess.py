"""Level guess node: estimate seniority and compute compatibility score."""

from __future__ import annotations

from typing import Any

from agent.state import AgentState
from app.config import settings

# Mapping of seniority labels ordered from lowest to highest.
_LEVEL_ORDER = ["junior", "mid", "senior", "staff"]


def _estimate_level_heuristic(skills: dict[str, Any]) -> str:
    """Estimate seniority using simple heuristics."""
    years = int(skills.get("years_of_experience", 0))
    skill_count = len(skills.get("skills", []))
    tech_count = len(skills.get("technologies", []))

    if years >= 8 and skill_count >= 6 and tech_count >= 4:
        return "staff"
    if years >= 5 and skill_count >= 4 and tech_count >= 3:
        return "senior"
    if years >= 2 and skill_count >= 2 and tech_count >= 2:
        return "mid"
    return "junior"


def _compute_compatibility(matched_nodes: list[dict], level: str) -> int:
    """Compute a 0-100 compatibility score based on coverage ratio.

    Heuristic: count matched nodes vs a rough target count for the level.
    """
    level_targets = {
        "junior": 3,
        "mid": 5,
        "senior": 7,
        "staff": 9,
    }
    target = level_targets.get(level, 5)
    matched = len(matched_nodes or [])

    # Clamp score between 0 and 100.
    score = min(100, max(0, int((matched / target) * 100)))
    return score


def level_guess_node(state: AgentState) -> AgentState:
    """Estimate the user's level and compute a compatibility score.

    Uses extracted_skills and matched_nodes already present in the state.
    When an LLM is unavailable the estimate is derived heuristically.
    """
    state.errors = list(state.errors)

    extracted = state.extracted_skills or {}
    matched = state.matched_nodes or []

    level = _estimate_level_heuristic(extracted)
    score = _compute_compatibility(matched, level)

    state.level_estimate = level
    state.compatibility_score = score

    return state
