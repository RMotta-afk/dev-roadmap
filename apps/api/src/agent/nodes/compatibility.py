"""Compatibility agent node: LLM-calibrated readiness score vs current+next level standards.

Moves scoring out of the level_guess node. Computes two mechanical coverage ratios
(current-level standard nodes vs next-level standard nodes), then asks a dedicated
LLM to calibrate a single blended 0-100 compatibility_score against qualitative
signals (foundational gaps, demonstrated strengths). Falls back deterministically."""
from __future__ import annotations

from typing import Any

from agent.state import AgentState
from app.config import settings
from llm.client import get_llm_client
from roadmap.index import RoadmapIndex
from roadmap.models import LEVEL_ORDER, CareerLevel

_CURRENT_WEIGHT = 0.4
_NEXT_WEIGHT = 0.6

_COMPAT_SYSTEM_PROMPT = """\
Você é um consultor de carreira sênior. Dado o nível exigido padrão para o cargo
atual e o nível alvo, produza uma pontuação de prontidão (0-100) que reflita
fidelidade real aos padrões desses níveis.

Você receberá:
- A pontuação mecânica base (0-100) calculada pela cobertura ponderada dos
  tópicos exigidos nos padrões do nível atual e do nível alvo.
- Resumo das lacunas e pontos fortes.

Ajuste a pontuação mecânica (em até +-15 pontos) com base em sinais qualitativos:
- Penalize fortemente a ausência de itens fundamentais do nível atual.
- Recompense cobertura sólida dos itens do nível alvo.
- Considere a profundidade demonstrada das competências.
Retorne a pontuação final limitada ao intervalo 0-100.

Retorne SOMENTE um objeto JSON com:
{"score": 0-100, "rationale": "1-2 frases curtas em português"}"""


def _compute_compatibility_score(covered_weight: float, total_weight: float) -> int:
    """Compute a 0-100 compatibility score from weighted readiness."""
    if total_weight == 0:
        return 0
    readiness_ratio = covered_weight / total_weight
    score = int(readiness_ratio * 100)
    return max(0, min(100, score))


def _level_index(level: CareerLevel | None) -> int:
    try:
        return LEVEL_ORDER.index(level)
    except (ValueError, AttributeError):
        return 0


def _bucket_ratio(
    matches: list[Any], index: RoadmapIndex, predicate
) -> tuple[float, float] | None:
    """Return (covered_weight, total_weight) for matches whose node passes predicate."""
    covered = 0.0
    total = 0.0
    for m in matches:
        node = index.by_id(m.id)
        if not node or not predicate(node):
            continue
        weight = float(node.importance) if node.importance else 50.0
        total += weight
        if m.status in ("covered", "known_via_experience"):
            covered += weight
    if total == 0:
        return None
    return covered, total


def _mechanical_score(state: AgentState, index: RoadmapIndex) -> tuple[int, str]:
    """Compute deterministic blended score from current vs next standard buckets."""
    current_level = state.career_frame.current_level or "junior"
    cur_idx = _level_index(current_level)

    current_bucket = _bucket_ratio(
        state.matched_nodes, index, lambda n: _level_index(n.level) <= cur_idx
    )
    next_bucket = _bucket_ratio(
        state.matched_nodes, index, lambda n: _level_index(n.level) > cur_idx
    )

    if next_bucket is None and current_bucket is None:
        return 0, "Sem tópicos suficientes para avaliar a prontidão."

    if next_bucket is None:
        current_ratio = _compute_compatibility_score(
            current_bucket[0], current_bucket[1]
        )
        return current_ratio, "Prontidão calculada pelo padrão do nível atual."

    if current_bucket is None:
        next_ratio = _compute_compatibility_score(next_bucket[0], next_bucket[1])
        return next_ratio, "Prontidão calculada pelo padrão do nível alvo."

    current_ratio = _compute_compatibility_score(current_bucket[0], current_bucket[1])
    next_ratio = _compute_compatibility_score(next_bucket[0], next_bucket[1])
    blended = round(_CURRENT_WEIGHT * current_ratio + _NEXT_WEIGHT * next_ratio)
    return blended, (
        f"Nível atual: {current_ratio}/100, Nível alvo: {next_ratio}/100 "
        f"(média ponderada {_CURRENT_WEIGHT}/{_NEXT_WEIGHT})."
    )


def _audit_summary(state: AgentState, index: RoadmapIndex) -> str:
    """Compact text summary of strengths and gaps for LLM context."""
    strengths = []
    gaps = []
    for m in state.matched_nodes:
        node = index.by_id(m.id)
        if not node:
            continue
        if m.status in ("covered", "known_via_experience"):
            strengths.append(f"{node.name} ({node.level.value})")
        else:
            gaps.append(f"{node.name} ({node.level.value})")
    summary = "Pontos fortes demonstrados:\n"
    summary += "\n".join(f"- {s}" for s in strengths[:12]) or "- (base em formação)"
    summary += "\n\nLacunas rumo ao alvo:\n"
    summary += "\n".join(f"- {g}" for g in gaps[:15]) or "- (bem preparado!)"
    summary += "\n\nCompetências conhecidas (nome/profundidade):\n"
    summary += "\n".join(
        f"- {c.name} ({c.depth}, {c.source})" for c in state.known_competencies[:15]
    ) or "- (nenhuma extraída)"
    return summary


async def _calibrate(base_score: int, rationale: str, state: AgentState, index: RoadmapIndex) -> tuple[int, str]:
    """Ask the LLM to refine the mechanical base score. Falls back to base on failure."""
    if not settings.llm_api_key:
        return base_score, rationale

    cf = state.career_frame
    context = (
        f"Cargo atual: {cf.current_level} {cf.current_role}\n"
        f"Cargo alvo: {cf.target_level} {cf.target_role}\n"
        f"Pontuação mecânica base: {base_score}/100 ({rationale})"
    )
    user = f"{context}\n\n---\n{_audit_summary(state, index)}"
    try:
        client = get_llm_client()
        result = await client.chat_json(
            [
                {"role": "system", "content": _COMPAT_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ]
        )
        score = int(result.get("score", base_score))
        score = max(0, min(100, score))
        return score, str(result.get("rationale", rationale))
    except Exception:
        return base_score, rationale


def compatibility_node(index: RoadmapIndex):
    """Returns a LangGraph node function with the roadmap index injected.

    Computes a single blended compatibility_score grounded in current-level and
    next-level standard buckets, optionally calibrated by an LLM.
    """

    async def _node(state: AgentState) -> AgentState:
        state.errors = list(state.errors)

        if not state.career_frame or not state.matched_nodes:
            state.compatibility_score = 0
            state.compatibility_rationale = "Dados insuficientes para avaliar prontidão."
            return state

        base_score, rationale = _mechanical_score(state, index)
        score, rationale = await _calibrate(base_score, rationale, state, index)
        state.compatibility_score = score
        state.compatibility_rationale = rationale
        return state

    return _node