from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: Literal["running", "done", "failed"]


class RoadmapNode(BaseModel):
    id: str
    name: str
    type: str = ""
    category: str = ""
    level: str = ""
    importance: int = 0
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    content_guidance: dict[str, Any] | None = Field(default_factory=dict)


class LevelResume(BaseModel):
    summary: str = ""
    strong_points: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    estimated_level: str = ""


class AgentProgressEvent(BaseModel):
    node: str
    status: Literal["started", "completed", "failed"]
    message: str | None = None
    payload: dict[str, Any] | None = None


class AnalyzeResult(BaseModel):
    level_resume: LevelResume
    compatibility_score: int = 0
    personalized_roadmap: list[RoadmapNode] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def normalize_result_payload(payload: dict[str, Any]) -> AnalyzeResult:
    """Normalize API final payload (level_estimate or level_resume) to AnalyzeResult."""
    if "level_resume" in payload and isinstance(payload["level_resume"], dict):
        resume = LevelResume.model_validate(payload["level_resume"])
    else:
        level = payload.get("level_estimate") or ""
        if isinstance(level, dict):
            resume = LevelResume.model_validate(level)
        else:
            resume = LevelResume(
                summary=f"Estimated level: {level}" if level else "Analysis complete.",
                estimated_level=str(level) if level else "unknown",
            )

    roadmap_raw = payload.get("personalized_roadmap") or []
    roadmap: list[RoadmapNode] = []
    for item in roadmap_raw:
        if isinstance(item, dict):
            item = {**item, "content_guidance": item.get("content_guidance") or {}}
            roadmap.append(RoadmapNode.model_validate(item))

    score = payload.get("compatibility_score") or 0
    try:
        score_int = int(score)
    except (TypeError, ValueError):
        score_int = 0

    errors = payload.get("errors") or []
    if not isinstance(errors, list):
        errors = []

    return AnalyzeResult(
        level_resume=resume,
        compatibility_score=max(0, min(100, score_int)),
        personalized_roadmap=roadmap,
        errors=[str(e) for e in errors],
    )
