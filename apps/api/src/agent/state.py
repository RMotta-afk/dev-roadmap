"""LangGraph agent state schema."""

from pydantic import BaseModel, Field


class CareerFrame(BaseModel):
    """User's career context: current position and target goals."""
    
    current_role: str | None = Field(default=None, description="Current role: ai_engineer|software_engineer|frontend_engineer")
    current_level: str | None = Field(default=None, description="Current seniority: junior|mid|senior|staff")
    target_role: str | None = Field(default=None, description="Target role to reach")
    target_level: str | None = Field(default=None, description="Target seniority to reach")
    focus_areas: list[str] = Field(default_factory=list, description="Specific technologies or domains to focus on")
    career_summary: str | None = Field(default=None, description="Brief career trajectory summary")


class KnownCompetency(BaseModel):
    """A skill or knowledge area demonstrated through experience."""
    
    name: str = Field(..., description="Competency name")
    evidence: str = Field(..., description="Evidence from CV (project, bullet, achievement)")
    source: str = Field(..., description="Source: skill|tech|experience|entailed")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence level 0-1")
    depth: str = Field(default="intermediario", description="Demonstrated depth: basico|intermediario|avancado")


class MatchedNode(BaseModel):
    """A roadmap node matched during compare, with status and evidence."""
    
    id: str = Field(..., description="Roadmap node ID")
    status: str = Field(..., description="covered|gap|known_via_experience")
    reason: str | None = Field(default=None, description="Explanation for the status")
    evidence: str | None = Field(default=None, description="Supporting evidence from CV")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Matching confidence 0-1")
    depth_candidate: bool = Field(default=False, description="True when depth needs LLM adjudication")


class LevelResumeData(BaseModel):
    """Resume of the user's current level and readiness."""
    
    summary: str = Field(..., description="Overall summary including trajectory and focus")
    strong_points: list[str] = Field(default_factory=list, description="Demonstrated strengths")
    weak_points: list[str] = Field(default_factory=list, description="Gaps toward target")
    estimated_level: str = Field(..., description="Current estimated level")


class AgentState(BaseModel):
    """Shared state object carried through the LangGraph agent nodes."""

    user_id: str
    raw_cv_text: str
    raw_description: str
    user_name: str | None = None
    profile: dict | None = None
    extracted_skills: dict | None = None
    career_frame: CareerFrame | None = None
    known_competencies: list[KnownCompetency] = Field(default_factory=list)
    matched_nodes: list[MatchedNode] = Field(default_factory=list)
    level_estimate: str | None = None  # Keep for backward compatibility
    level_resume: LevelResumeData | None = None
    compatibility_score: int | None = None
    compatibility_rationale: str | None = None
    personalized_roadmap: list[dict] | None = None
    errors: list[str] = []
