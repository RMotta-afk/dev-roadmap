"""Roadmap selection node: prioritize gaps by focus areas and target context."""

from agent.state import AgentState, MatchedNode
from roadmap.index import RoadmapIndex


def _prioritize_gaps(
    gap_matches: list[MatchedNode],
    index: RoadmapIndex,
    focus_areas: list[str],
) -> list[str]:
    """Sort gap node IDs by token-aware focus area match, alias matching, then importance."""
    if not focus_areas:
        scored = []
        for match in gap_matches:
            node = index.by_id(match.id)
            if node:
                scored.append((node.importance if node.importance else 50, match.id))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [sid for _, sid in scored]

    focus_phrases_lower = [f.lower().strip() for f in focus_areas]
    focus_tokens: set[str] = set()
    for phrase in focus_phrases_lower:
        for token in phrase.split():
            focus_tokens.add(token)

    scored_gaps = []
    for match in gap_matches:
        node = index.by_id(match.id)
        if not node:
            continue

        score = 0

        searchable = [
            node.name.lower(),
            node.category.lower(),
        ]
        searchable.extend(a.lower() for a in node.aliases)

        # Priority 1: Exact phrase match in name or category (highest)
        for phrase in focus_phrases_lower:
            for s in searchable[:2]:
                if phrase == s:
                    score += 1000
                    break

        # Priority 2: Token-level matches (medium boost, per token)
        token_count = 0
        for s in searchable:
            for token in focus_tokens:
                if token in s.split():
                    token_count += 1
        score += min(token_count * 300, 900)

        # Priority 3: Substring match in any searchable field (lower than token)
        for phrase in focus_phrases_lower:
            for s in searchable:
                if phrase in s:
                    score += 200
                    break

        # Priority 4: Importance as tiebreaker
        score += node.importance if node.importance else 50

        scored_gaps.append((score, match.id))

    scored_gaps.sort(reverse=True, key=lambda x: x[0])
    return [gap_id for _, gap_id in scored_gaps]


def roadmap_select_node(index: RoadmapIndex):
    """Returns a LangGraph node function with the roadmap index injected."""

    def _node(state: AgentState) -> AgentState:
        """Select personalized roadmap from gaps, prioritizing focus areas and importance."""
        matched = state.matched_nodes or []
        
        # Filter to gaps only
        gap_matches = [m for m in matched if m.status == "gap"]
        
        # Get focus areas from career frame
        focus_areas = []
        if state.career_frame:
            focus_areas = state.career_frame.focus_areas
        
        # Prioritize gaps
        prioritized_ids = _prioritize_gaps(gap_matches, index, focus_areas)
        
        # Build personalized roadmap from prioritized gap nodes
        roadmap = []
        for nid in prioritized_ids[:35]:  # cap at 35 items
            node = index.by_id(nid)
            if node:
                roadmap.append(node.model_dump())

        # STRICT-SUBSET GUARDRAIL (ADR-008)
        node_ids = [n["id"] for n in roadmap]
        if not index.is_valid_subset(node_ids):
            # Re-plan once: filter out any invalid ids
            valid_ids = [nid for nid in node_ids if index.by_id(nid) is not None]
            roadmap = [n for n in roadmap if n["id"] in valid_ids]
            # If still invalid after re-plan, hard error
            final_ids = [n["id"] for n in roadmap]
            if not index.is_valid_subset(final_ids):
                state.errors.append("Guardrail violation: roadmap contains hallucinated items")
                state.personalized_roadmap = []
                return state

        state.personalized_roadmap = roadmap
        return state

    return _node
