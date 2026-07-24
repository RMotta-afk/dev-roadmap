from agent.state import AgentState
from roadmap.index import RoadmapIndex


def roadmap_select_node(index: RoadmapIndex):
    """Returns a LangGraph node function with the roadmap index injected."""

    def _node(state: AgentState) -> AgentState:
        matched = state.matched_nodes or []
        gap_ids = [m["id"] for m in matched if m.get("status") == "gap"]

        # Build personalized roadmap from gap nodes
        roadmap = []
        for nid in gap_ids[:20]:  # cap at 20 items
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
