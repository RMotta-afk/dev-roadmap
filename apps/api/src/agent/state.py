"""LangGraph agent state schema."""

from pydantic import BaseModel


class AgentState(BaseModel):
    """Shared state object carried through the LangGraph agent nodes."""

    user_id: str
    raw_cv_text: str
    raw_description: str
    extracted_skills: dict | None = None
    matched_nodes: list[dict] | None = None
    level_estimate: str | None = None
    compatibility_score: int | None = None
    personalized_roadmap: list[dict] | None = None
    errors: list[str] = []
