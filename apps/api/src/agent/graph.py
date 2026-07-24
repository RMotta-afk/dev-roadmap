import uuid
from typing import AsyncIterator

from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes.ingest import ingest_node
from agent.nodes.strip import strip_node
from agent.nodes.analyze import analyze_node
from agent.nodes.compare import compare_node
from agent.nodes.level_guess import level_guess_node
from agent.nodes.roadmap_select import roadmap_select_node
from roadmap.index import RoadmapIndex


def build_analysis_graph(index: RoadmapIndex) -> StateGraph:
    """Builds the LangGraph for CV analysis with strict-subset guardrails."""

    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("strip", strip_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("compare", compare_node)
    workflow.add_node("level_guess", level_guess_node)
    workflow.add_node("roadmap_select", roadmap_select_node(index))

    # Edges (sequential pipeline)
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "strip")
    workflow.add_edge("strip", "analyze")
    workflow.add_edge("analyze", "compare")
    workflow.add_edge("compare", "level_guess")
    workflow.add_edge("level_guess", "roadmap_select")
    workflow.add_edge("roadmap_select", END)

    return workflow.compile()


async def stream_analysis(
    index: RoadmapIndex,
    user_id: str,
    raw_cv_text: str,
    raw_description: str,
    user_name: str | None = None,
) -> AsyncIterator[dict]:
    """Stream agent progress events and final result."""

    graph = build_analysis_graph(index)

    initial_state = AgentState(
        user_id=user_id,
        raw_cv_text=raw_cv_text,
        raw_description=raw_description,
        user_name=user_name,
    )

    # Stream each node completion
    async for event in graph.astream(initial_state):
        node_name = event.get("node", "unknown")
        yield {
            "node": node_name,
            "status": "completed",
            "message": f"Node {node_name} completed",
            "payload": event,
        }

    # Final result event
    final_state = event  # last event holds final state
    yield {
        "node": "result",
        "status": "completed",
        "message": "Analysis complete",
        "payload": {
            "level_estimate": final_state.level_estimate,
            "compatibility_score": final_state.compatibility_score,
            "personalized_roadmap": final_state.personalized_roadmap,
            "errors": final_state.errors,
        },
    }
