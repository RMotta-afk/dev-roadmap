"""Roadmap selection node: prioritize gaps by focus areas and target context."""

from agent.state import AgentState, MatchedNode
from roadmap.index import RoadmapIndex


def _prioritize_gaps(
    gap_matches: list[MatchedNode],
    index: RoadmapIndex,
    focus_areas: list[str],
) -> list[str]:
    """Sort gap node IDs by focus area match, then importance."""
    focus_lower = {f.lower() for f in focus_areas}
    
    scored_gaps = []
    for match in gap_matches:
        node = index.by_id(match.id)
        if not node:
            continue
        
        score = 0
        
        # Priority 1: Focus area match (category or name)
        if focus_lower:
            if node.category.lower() in focus_lower or node.name.lower() in focus_lower:
                score += 1000
            # Check if any focus keyword appears in node name/category
            for focus in focus_lower:
                if focus in node.name.lower() or focus in node.category.lower():
                    score += 500
        
        # Priority 2: Importance
        score += node.importance if node.importance else 50
        
        scored_gaps.append((score, match.id))
    
    # Sort by score descending
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
        for nid in prioritized_ids[:20]:  # cap at 20 items
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
