"""Level guess node: estimate seniority and compute target-relative compatibility score."""

from __future__ import annotations

from typing import Any
import json

from agent.state import AgentState, LevelResumeData
from app.config import settings
from llm.client import get_llm_client
from roadmap.index import RoadmapIndex


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


def _compute_compatibility_score(covered_weight: float, total_weight: float) -> int:
    """Compute a 0-100 compatibility score based on weighted readiness."""
    if total_weight == 0:
        return 0
    
    readiness_ratio = covered_weight / total_weight
    score = int(readiness_ratio * 100)
    
    return max(0, min(100, score))


def _build_narrative_prompt(state: AgentState, index: RoadmapIndex) -> str:
    """Build context for LLM narrative generation."""
    cf = state.career_frame
    if not cf:
        return ""
    
    # Get node details for gaps
    gap_nodes = []
    strong_nodes = []
    for match in state.matched_nodes:
        node = index.by_id(match.id)
        if node:
            if match.status == "gap":
                gap_nodes.append(f"- {node.name} ({node.category})")
            elif match.status in ("covered", "known_via_experience"):
                evidence = f": {match.evidence}" if match.evidence else ""
                strong_nodes.append(f"- {node.name}{evidence}")
    
    context = f"""
Career Context:
- Current: {cf.current_level} {cf.current_role}
- Target: {cf.target_level} {cf.target_role}
- Focus Areas: {', '.join(cf.focus_areas) if cf.focus_areas else 'General development'}
- Years of Experience: {state.extracted_skills.get('years_of_experience', 0)}

Demonstrated Strengths (covered or known via experience):
{chr(10).join(strong_nodes[:10]) if strong_nodes else '- (Building foundation)'}

Key Gaps Toward Target:
{chr(10).join(gap_nodes[:10]) if gap_nodes else '- (Well-prepared!)'}

Known Competencies:
{chr(10).join([f"- {c.name}" for c in state.known_competencies[:5]])}
"""
    return context


async def _generate_level_resume_llm(state: AgentState, index: RoadmapIndex) -> dict[str, Any] | None:
    """Generate LevelResume via LLM."""
    if not settings.llm_api_key:
        return None
    
    try:
        context = _build_narrative_prompt(state, index)
        messages = [
            {"role": "system", "content": _LEVEL_RESUME_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ]
        
        client = get_llm_client()
        result = await client.chat_json(messages)
        return result
    except Exception:
        return None


def _generate_level_resume_template(state: AgentState, index: RoadmapIndex) -> dict[str, Any]:
    """Generate LevelResume via template fallback."""
    cf = state.career_frame
    if not cf:
        return {
            "summary": "Unable to assess career level without career context.",
            "strong_points": [],
            "weak_points": [],
        }
    
    # Build summary
    focus_text = f" with focus on {', '.join(cf.focus_areas[:3])}" if cf.focus_areas else ""
    summary = (
        f"Avaliado atualmente como {cf.current_level} {cf.current_role.replace('_', ' ')}. "
        f"Alvo: {cf.target_level} {cf.target_role.replace('_', ' ')}{focus_text}. "
        f"Continue desenvolvendo expertise nas lacunas identificadas para alcançar seu nível alvo."
    )
    
    # Build strong points from covered/known
    strong_points = []
    for match in state.matched_nodes:
        if match.status in ("covered", "known_via_experience"):
            node = index.by_id(match.id)
            if node and len(strong_points) < 5:
                evidence = f" - {match.evidence}" if match.evidence else ""
                strong_points.append(f"{node.name}{evidence}")
    
    # Build weak points from high-importance gaps
    weak_points = []
    gap_matches = [(m, index.by_id(m.id)) for m in state.matched_nodes if m.status == "gap"]
    gap_matches_sorted = sorted(
        [(m, n) for m, n in gap_matches if n],
        key=lambda x: x[1].importance if x[1].importance else 0,
        reverse=True
    )
    
    for match, node in gap_matches_sorted[:5]:
        weak_points.append(f"{node.name} ({node.category})")
    
    return {
        "summary": summary,
        "strong_points": strong_points,
        "weak_points": weak_points,
    }


def level_guess_node(index: RoadmapIndex):
    """Returns a LangGraph node function with the roadmap index injected."""
    
    async def _node(state: AgentState) -> AgentState:
        """Estimate the user's level and compute target-relative compatibility score.
        
        Uses career_frame and matched_nodes from state. Computes readiness against
        TARGET level (not just retrieval count). Generates full LevelResume.
        """
        state.errors = list(state.errors)
        
        if not state.career_frame or not state.matched_nodes:
            state.level_estimate = "junior"
            state.compatibility_score = 0
            state.level_resume = LevelResumeData(
                summary="Insufficient data to assess level.",
                strong_points=[],
                weak_points=[],
                estimated_level="junior",
            )
            return state
        
        # Use current level from career frame (already computed in analyze)
        current_level = state.career_frame.current_level or "junior"
        state.level_estimate = current_level  # backward compat
        
        # Compute target-relative readiness score
        covered_count = sum(1 for m in state.matched_nodes if m.status in ("covered", "known_via_experience"))
        gap_count = sum(1 for m in state.matched_nodes if m.status == "gap")
        
        # Weighted score
        covered_weight = 0.0
        total_weight = 0.0
        for match in state.matched_nodes:
            node = index.by_id(match.id)
            if node:
                weight = float(node.importance) if node.importance else 50.0
                total_weight += weight
                if match.status in ("covered", "known_via_experience"):
                    covered_weight += weight
        
        score = _compute_compatibility_score(covered_weight, total_weight)
        state.compatibility_score = score
        
        # Generate LevelResume (try LLM first, fallback to template)
        resume_data = await _generate_level_resume_llm(state, index)
        if not resume_data:
            resume_data = _generate_level_resume_template(state, index)
        
        state.level_resume = LevelResumeData(
            summary=resume_data.get("summary", ""),
            strong_points=resume_data.get("strong_points", []),
            weak_points=resume_data.get("weak_points", []),
            estimated_level=current_level,
        )
        
        return state
    
    return _node
