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
    workflow.add_node("compare", compare_node(index))
    workflow.add_node("level_guess", level_guess_node(index))
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

    # Emit a pipeline-started event so the frontend gets immediate feedback
    yield {
        "node": "pipeline",
        "status": "started",
        "message": "Analysis pipeline started",
        "payload": {},
    }

    # Stream each node completion (stream_mode="updates" yields {node_name: state_dict})
    final: dict = {}
    async for update in graph.astream(initial_state, stream_mode="updates"):
        for node_name, node_output in update.items():
            output = node_output if isinstance(node_output, dict) else {}
            final.update(output)
            yield {
                "node": node_name,
                "status": "completed",
                "message": f"Node {node_name} completed",
                "payload": output,
            }

    # Final result event built from accumulated state
    career_frame = final.get("career_frame")
    level_resume = final.get("level_resume")
    
    yield {
        "node": "result",
        "status": "completed",
        "message": "Analysis complete",
        "payload": {
            "level_estimate": final.get("level_estimate"),  # backward compat
            "level_resume": level_resume.model_dump() if level_resume else None,
            "target_role": career_frame.target_role if career_frame else None,
            "target_level": career_frame.target_level if career_frame else None,
            "focus_areas": career_frame.focus_areas if career_frame else [],
            "compatibility_score": final.get("compatibility_score"),
            "personalized_roadmap": final.get("personalized_roadmap"),
            "errors": final.get("errors", []),
        },
    }
