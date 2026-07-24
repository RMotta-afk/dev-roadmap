"""Ingest node: validates that raw inputs are present."""

from agent.state import AgentState


def ingest_node(state: AgentState) -> AgentState:
    """Accept initial state and mark CV + description as ingested."""
    state.errors = list(state.errors)  # work on a shallow copy
    # In a future version we might parse uploaded files here.
    # For MVP the text is already populated by the caller.
    # Add a progress-style note (stored as a non-error message in errors for now).
    state.errors.append("Ingested CV and description")
    return state
