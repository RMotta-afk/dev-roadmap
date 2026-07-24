"""Analyze router: POST /analyze and SSE stream endpoint."""

from __future__ import annotations

import uuid
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, Form, UploadFile, status
from fastapi.responses import StreamingResponse

from agent.graph import stream_analysis
from app.auth import require_auth
from app.schemas import AgentProgressEvent, AnalyzeResponse
from app.storage.analyses import create_analysis, get_analysis, update_analysis
from roadmap.index import RoadmapIndex
from roadmap.loader import flatten_nodes, load_all_roadmaps

router = APIRouter(tags=["analyze"])


# Module-level singleton — loaded on first use
_roadmap_index: RoadmapIndex | None = None


def _get_roadmap_index() -> RoadmapIndex:
    """Lazy-load the global RoadmapIndex."""
    global _roadmap_index
    if _roadmap_index is None:
        roadmaps = load_all_roadmaps()
        nodes = flatten_nodes(roadmaps)
        _roadmap_index = RoadmapIndex(nodes)
    return _roadmap_index


@router.post("/analyze", status_code=status.HTTP_201_CREATED, response_model=AnalyzeResponse)
async def analyze(
    user_name: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    email: Annotated[str, Form()],
    description: Annotated[str, Form()],
    cv: UploadFile,
    user: dict = Depends(require_auth),
) -> AnalyzeResponse:
    """Accept a CV + form data and kick off an analysis."""
    analysis_id = str(uuid.uuid4())
    user_id = user["user_id"]

    # Read CV content as text (MVP)
    cv_content = (await cv.read()).decode("utf-8", errors="replace")

    request_dict = {
        "user_name": user_name,
        "phone": phone,
        "email": email,
        "description": description,
        "cv_filename": cv.filename,
        "cv_content": cv_content,
    }

    await create_analysis(analysis_id, user_id, request_dict)

    return AnalyzeResponse(analysis_id=analysis_id, status="running")


async def _sse_stream(
    analysis_id: str,
    user_id: str,
    raw_cv_text: str,
    raw_description: str,
) -> AsyncIterator[str]:
    """Run the LangGraph pipeline and yield SSE formatted events."""
    index = _get_roadmap_index()

    result_payload: dict | None = None

    async for event in stream_analysis(
        index=index,
        user_id=user_id,
        raw_cv_text=raw_cv_text,
        raw_description=raw_description,
    ):
        node = event.get("node", "unknown")
        message = event.get("message", f"Node {node} completed")
        payload = event.get("payload")

        progress = AgentProgressEvent(
            node=node,
            status="completed",
            message=message,
            payload=payload,
        )
        yield f"data: {progress.model_dump_json()}\n\n"

        # Capture the final result payload when the node is "result"
        if node == "result":
            result_payload = payload

    # Update DB on completion
    await update_analysis(
        analysis_id=analysis_id,
        result_dict=result_payload,
        status="done",
    )


@router.get("/analyze/{analysis_id}/events")
async def analyze_events(
    analysis_id: str,
    user: dict = Depends(require_auth),
) -> StreamingResponse:
    """SSE stream of agent progress events for a given analysis."""
    analysis = await get_analysis(analysis_id)
    if analysis is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Analysis not found")

    # Ownership check
    if str(analysis["user_id"]) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this analysis")

    request_dict = analysis["request"]
    raw_cv_text = request_dict.get("cv_content", "")
    raw_description = request_dict.get("description", "")

    return StreamingResponse(
        _sse_stream(
            analysis_id=analysis_id,
            user_id=user["user_id"],
            raw_cv_text=raw_cv_text,
            raw_description=raw_description,
        ),
        media_type="text/event-stream",
    )
