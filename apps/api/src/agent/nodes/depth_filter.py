"""Depth filter node: LLM adjudication of ambiguous topic matches.

Takes ``MatchedNode`` entries flagged as ``depth_candidate`` by the compare node
and classifies each as SAME_OR_LOWER_DEPTH (user already masters the topic at or
above the roadmap requirement -> reclassify as known) or MORE_ADVANCED (the
roadmap item demands more than the user's demonstrated level -> stays a gap).
"""

from __future__ import annotations

from typing import Any

from agent.state import AgentState
from app.config import settings
from llm.client import get_llm_client
from roadmap.index import RoadmapIndex

_MAX_CANDIDATES = 40

_DEPTH_FILTER_SYSTEM_PROMPT = """\
Você é um avaliador técnico de currículos. Para cada tópico, compare a
profundidade exigida pelo roadmap (nível/cargo alvo) com a evidência de
experiência do usuário e decida se o usuário JÁ DOMINA o tópico no mesmo nível
ou mais profundo, ou se o tópico é um tema avançado que ele ainda não domina.

Um tópico deve ser marcado como DOMINADO (same_or_lower) quando a experiência
do usuário cobre o tema na mesma profundidade ou mais profunda que a exigida.
Deve ser marcado como FALTA (more_advanced) quando a evidência mostra apenas
exposição superficial, uso indireto, ou conhecimento prévio que não atinge o
nível exigido pelo roadmap.

Retorne SOMENTE um objeto JSON com esta forma exata:
{
  "verdicts": [
    {"id": "<candidate id>", "verdict": "same_or_lower|more_advanced",
     "reason": "1 frase curta em português"}
  ]
}

Inclua UM objeto para CADA id recebido. Não inclua texto fora do JSON."""


def _build_candidate_context(state: AgentState, index: RoadmapIndex) -> list[dict[str, Any]]:
    """Collect depth candidates with their node context and user evidence."""
    candidates = [m for m in state.matched_nodes if m.depth_candidate]
    # Bound the batch, preferring the strongest similarity matches first.
    candidates.sort(key=lambda m: m.confidence if m.confidence is not None else 0.0, reverse=True)
    out: list[dict[str, Any]] = []
    for match in candidates[:_MAX_CANDIDATES]:
        node = index.by_id(match.id)
        if not node:
            continue
        out.append(
            {
                "id": match.id,
                "name": node.name,
                "category": node.category,
                "level": node.level.value,
                "evidence": match.evidence or "",
            }
        )
    return out


async def _adjudicate(candidates: list[dict[str, Any]], state: AgentState) -> dict[str, Any] | None:
    """Run the batched LLM adjudication over the candidate list."""
    if not settings.llm_api_key or not candidates:
        return None

    cf = state.career_frame
    target_context = (
        f"Nível atual: {cf.current_level} / Nível alvo: {cf.target_level}"
        if cf
        else "Nível atual/alvo não informado"
    )
    items = "\n".join(
        f"- id: {c['id']} | tópico: {c['name']} | categoria: {c['category']} | "
        f"nível roadmap: {c['level']} | evidência do usuário: {c['evidence']}"
        for c in candidates
    )
    user = (
        f"{target_context}\n\n"
        f"Contexto das competências conhecidas do usuário:\n"
        + "\n".join(
            f"- {c.name} (profundidade: {c.depth}, fonte: {c.source})"
            for c in state.known_competencies[:20]
        )
        + "\n\nCandidatos a avaliar:\n"
        + items
    )
    try:
        client = get_llm_client()
        return await client.chat_json(
            [
                {"role": "system", "content": _DEPTH_FILTER_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ]
        )
    except Exception:
        return None


def _apply_verdicts(state: AgentState, verdicts: list[dict[str, Any]]) -> None:
    """Apply LLM verdicts back onto matched nodes, clearing the candidate flag."""
    verdict_map: dict[str, dict[str, Any]] = {}
    for v in verdicts:
        vid = v.get("id")
        if vid:
            verdict_map[str(vid)] = v

    for match in state.matched_nodes:
        if not match.depth_candidate:
            continue
        verdict = verdict_map.get(match.id)
        if not verdict:
            # Unknown id: reset to a plain gap (today's behavior).
            match.depth_candidate = False
            continue
        verdict_str = str(verdict.get("verdict", "")).strip().lower()
        if verdict_str in ("same_or_lower", "same_or_lower_depth"):
            match.status = "known_via_experience"
            match.reason = (
                "Experiência demonstra domínio no nível exigido pelo roadmap"
                f" ({verdict.get('reason', '')})".strip()
            )
        else:
            match.reason = (
                "Requer profundidade mais avançada que a demonstrada"
                f" ({verdict.get('reason', '')})".strip()
            )
        match.depth_candidate = False


def depth_filter_node(index: RoadmapIndex):
    """Returns a LangGraph node function with the roadmap index injected.

    Resolves ambiguous (depth_candidate) matches. On failure or missing LLM key,
    candidates degrade to plain gaps, preserving prior behavior.
    """

    async def _node(state: AgentState) -> AgentState:
        state.errors = list(state.errors)
        candidates = _build_candidate_context(state, index)
        if not candidates:
            # Nothing to adjudicate; clear any stale flags.
            for match in state.matched_nodes:
                match.depth_candidate = False
            return state

        result = await _adjudicate(candidates, state)
        if not result:
            for match in state.matched_nodes:
                match.depth_candidate = False
            return state

        _apply_verdicts(state, result.get("verdicts", []))
        return state

    return _node
