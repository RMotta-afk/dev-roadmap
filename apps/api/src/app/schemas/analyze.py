"""Pydantic DTOs for the analysis domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request payload to start a new analysis."""

    user_name: str = Field(description="User full name")
    phone: str = Field(description="User phone number")
    email: str = Field(description="User email address")
    description: str = Field(description="Free-text description of the user's context")


class AnalyzeResponse(BaseModel):
    """Response returned when an analysis is accepted."""

    analysis_id: str = Field(description="Unique identifier for the analysis")
    status: str = Field(
        description="Current status of the analysis",
        pattern=r"^(running|done|failed)$",
    )


class RoadmapNode(BaseModel):
    """A single node in the personalized roadmap."""

    id: str = Field(description="Stable identifier for the node")
    name: str = Field(description="Human-readable name")
    type: str = Field(description="Node type (e.g., skill, topic, milestone)")
    category: str = Field(description="Category this node belongs to")
    level: str = Field(description="Proficiency level for this node")
    importance: int = Field(description="Importance score", ge=0, le=100)
    description: str | None = Field(default=None, description="Optional detailed description")
    aliases: list[str] = Field(default_factory=list, description="Alternative names")
    content_guidance: dict | None = Field(default_factory=dict, description="Content / study guidance")


class LevelResume(BaseModel):
    """Resume of the user's current level."""

    summary: str = Field(description="Overall summary of the user's level")
    strong_points: list[str] = Field(default_factory=list, description="Identified strong points")
    weak_points: list[str] = Field(default_factory=list, description="Identified weak points")
    estimated_level: str = Field(description="Estimated proficiency level")


class AgentProgressEvent(BaseModel):
    """Event emitted by an agent during analysis."""

    node: str = Field(description="Node / step identifier")
    status: str = Field(
        description="Event status",
        pattern=r"^(started|completed|failed)$",
    )
    message: str | None = Field(default=None, description="Optional human-readable message")
    payload: dict | None = Field(default=None, description="Optional extra data")


class AnalyzeResult(BaseModel):
    """Final result of an analysis."""

    level_resume: LevelResume = Field(description="User level resume")
    compatibility_score: int = Field(
        description="Compatibility score between 0 and 100",
        ge=0,
        le=100,
    )
    personalized_roadmap: list[RoadmapNode] = Field(
        default_factory=list,
        description="Generated personalized roadmap",
    )
