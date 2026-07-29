"""Analyze router: POST /analyze and SSE stream endpoint."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import Response, StreamingResponse

from agent.graph import stream_analysis
from agent.pdf_parser import extract_cv_text
from app.auth import require_auth
from app.pdf.pdf_export import build_pdf
from app.schemas import AgentProgressEvent, AnalyzeResponse
from app.storage.analyses import create_analysis, get_analysis, update_analysis
from roadmap.index import RoadmapIndex
from roadmap.loader import flatten_nodes, load_all_roadmaps

router = APIRouter(tags=["analyze"])

logger = logging.getLogger("api.analyze")


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

    # Ingest the CV: extract rendered text from PDF bytes (or decode text files).
    # The raw bytes are discarded after extraction — CV files are ephemeral.
    cv_content = extract_cv_text(await cv.read(), cv.filename)

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
    user_name: str | None = None,
) -> AsyncIterator[str]:
    """Run the LangGraph pipeline and yield SSE formatted events."""
    index = _get_roadmap_index()

    result_payload: dict | None = None

    async for event in stream_analysis(
        index=index,
        user_id=user_id,
        raw_cv_text=raw_cv_text,
        raw_description=raw_description,
        user_name=user_name,
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
    user_name = request_dict.get("user_name")

    return StreamingResponse(
        _sse_stream(
            analysis_id=analysis_id,
            user_id=user["user_id"],
            raw_cv_text=raw_cv_text,
            raw_description=raw_description,
            user_name=user_name,
        ),
        media_type="text/event-stream",
    )


@router.get("/analyze/{analysis_id}/pdf")
async def download_pdf(
    analysis_id: str,
    user: dict = Depends(require_auth),
) -> Response:
    """Download analysis results as a PDF roadmap (Portuguese)."""
    analysis = await get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    if str(analysis["user_id"]) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    if analysis.get("status") != "done":
        raise HTTPException(
            status_code=400,
            detail="Análise ainda não concluída",
        )

    result_dict = analysis.get("result") or {}
    request_dict = analysis.get("request") or {}
    user_name = request_dict.get("user_name", "Usuario")

    pdf_bytes: bytes | None = None
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            pdf_bytes = build_pdf(result_dict, user_name)
            break
        except Exception as exc:
            last_error = exc
            logger.warning(
                f"PDF generation attempt {attempt + 1} failed for analysis {analysis_id}: {exc}"
            )
            if attempt < 2:
                await asyncio.sleep(0.5)

    if pdf_bytes is None:
        logger.error(
            f"PDF generation failed after 3 attempts for analysis {analysis_id}: {last_error}",
            exc_info=last_error,
        )
        raise HTTPException(
            status_code=500,
            detail="Falha ao gerar PDF após 3 tentativas",
        )

    safe_name = user_name.strip().replace(" ", "_")
    filename = f"{safe_name}_roadmap.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
