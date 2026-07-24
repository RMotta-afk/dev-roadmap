"""Compare node: retriever-backed gap analysis."""

from agent.state import AgentState
from rag.retriever import create_retriever
from roadmap.models import RoadmapNode


async def compare_node(state: AgentState) -> AgentState:
    """Retrieve roadmap nodes for extracted skills and classify as covered or gap.

    Steps:
        1. Flatten ``extracted_skills`` (skills / technologies / domain_areas) into
           search queries.
        2. Call the ``RoadmapRetriever`` for each query.
        3. Deduplicate results by node id.
        4. Classify each unique node as *covered* when its name (case-insensitive)
           appears in the user's extracted skills; otherwise mark as *gap*.
        5. Store the list of ``{"id": ..., "status": ...}`` dicts in
           ``state.matched_nodes``.
    """
    if state.extracted_skills is None:
        state.matched_nodes = []
        return state

    # Build a case-insensitive set of every skill/tech/domain the user has
    user_skills: set[str] = set()
    for category in ("skills", "technologies", "domain_areas"):
        for item in state.extracted_skills.get(category, []):
            if isinstance(item, str):
                user_skills.add(item.lower())

    retriever = create_retriever()
    seen_ids: set[str] = set()
    matched_nodes: list[dict] = []

    for category in ("skills", "technologies", "domain_areas"):
        for item in state.extracted_skills.get(category, []):
            if not isinstance(item, str):
                continue

            results: list[RoadmapNode] = await retriever.retrieve(item, top_k=5)
            for node in results:
                if node.id in seen_ids:
                    continue
                seen_ids.add(node.id)

                status = (
                    "covered"
                    if node.name.lower() in user_skills
                    else "gap"
                )
                matched_nodes.append({"id": node.id, "status": status})

    state.matched_nodes = matched_nodes
    return state
