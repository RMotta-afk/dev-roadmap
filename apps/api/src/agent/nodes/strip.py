"""Strip node: turn raw CV text into a structured LinkedInProfile.

The CV bytes are already extracted to text by :mod:`agent.pdf_parser` at
ingestion. This node parses that text (a LinkedIn 'Save to PDF' export) into a
structured profile carried on the agent state for downstream nodes.
"""

from agent.linkedin_parser import parse_linkedin_profile
from agent.state import AgentState


def strip_node(state: AgentState) -> AgentState:
    """Parse ``raw_cv_text`` into ``state.profile`` (a LinkedInProfile)."""
    state.errors = list(state.errors)  # work on a shallow copy

    if not state.raw_cv_text.strip():
        state.errors.append("raw_cv_text is empty after stripping")
        return state

    try:
        profile = parse_linkedin_profile(state.raw_cv_text, known_name=state.user_name)
        state.profile = profile.model_dump()
    except Exception as exc:  # pragma: no cover - defensive
        state.errors.append(f"Profile parsing failed ({type(exc).__name__})")

    return state
