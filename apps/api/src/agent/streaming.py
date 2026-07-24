from typing import AsyncIterator

from agent.state import AgentState


async def map_state_to_sse(
    state_stream: AsyncIterator[AgentState],
) -> AsyncIterator[str]:
    """Maps LangGraph state updates to SSE formatted strings."""

    async for state in state_stream:
        # Format as SSE: data: {...}\n\n
        import json

        payload = {
            "node": getattr(state, "_node", "unknown"),
            "status": "completed",
            "message": "State updated",
        }
        yield f"data: {json.dumps(payload)}\n\n"
