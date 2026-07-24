"""Strip node: validate raw text and pass through."""

from agent.state import AgentState


def strip_node(state: AgentState) -> AgentState:
    """Validate that raw_cv_text is non-empty.

    In the future this node would parse PDF/DOCX/TXT into plain text.
    For the MVP the text is already extracted, so we just validate.
    """
    state.errors = list(state.errors)  # work on a shallow copy
    if not state.raw_cv_text.strip():
        state.errors.append("raw_cv_text is empty after stripping")
    return state
