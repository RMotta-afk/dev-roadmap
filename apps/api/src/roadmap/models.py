"""Pydantic models for Base Roadmap data layer."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RoadmapRole(str, Enum):
    """Supported roadmap roles."""

    software_engineer = "software_engineer"
    ai_engineer = "ai_engineer"
    frontend_engineer = "frontend_engineer"


class CareerLevel(str, Enum):
    """Supported career levels."""

    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff = "staff"


class RequirementsByLevel(BaseModel):
    """Requirement depth for a given career level."""

    required: bool
    expected_depth: int


class InterviewInfo(BaseModel):
    """Interview metadata for a node."""

    priority: int
    asked_frequency: str
    must_know: bool


class ContentGuidance(BaseModel):
    """Guidance for content generation and interview prep."""

    topics: list[str]
    practice_examples: list[str]
    interview_topics: list[str]


class RoadmapNode(BaseModel):
    """Individual node within a roadmap file."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    type: str
    category: str
    description: str
    level: CareerLevel
    importance: int
    estimated_hours: int
    aliases: list[str]
    requirements_by_level: dict[CareerLevel, RequirementsByLevel]
    interview: InterviewInfo
    content_guidance: ContentGuidance


class RoadmapMetadata(BaseModel):
    """File-level metadata."""

    author: str
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[str]


class RoadmapFile(BaseModel):
    """Top-level structure of a roadmap JSON file."""

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    role: RoadmapRole
    version: str
    description: str
    market: list[str] | None = None
    metadata: RoadmapMetadata
    nodes: list[RoadmapNode]
