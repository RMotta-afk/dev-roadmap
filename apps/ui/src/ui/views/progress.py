from __future__ import annotations

import streamlit as st

from ui.api.client import ApiError, extract_result, subscribe_to_analysis
from ui.api.models import AgentProgressEvent
from ui.auth import mint_backend_token


def _ensure_token() -> str:
    user = st.session_state.get("user")
    if not user:
        raise RuntimeError("Not authenticated")
    token = mint_backend_token(
        user["id"],
        user["email"],
        is_admin=bool(user.get("is_admin", False)),
    )
    st.session_state.token = token
    return token


def _status_label(status: str) -> str:
    if status == "completed":
        return "✅"
    if status == "failed":
        return "❌"
    return "⏳"


def render_progress() -> None:
    analysis_id = st.session_state.get("analysis_id")
    if not analysis_id:
        st.session_state.page = "home"
        st.rerun()
        return

    st.markdown("## Analyzing…")
    st.caption(f"Analysis ID: `{analysis_id}`")

    if st.session_state.get("result") is not None:
        st.session_state.page = "results"
        st.rerun()
        return

    if st.session_state.get("analysis_error"):
        st.error(st.session_state.analysis_error)
        if st.button("Back to form"):
            st.session_state.page = "home"
            st.rerun()
        return

    events: list[AgentProgressEvent] = list(st.session_state.get("events") or [])
    progress_box = st.empty()
    steps_box = st.empty()
    status_box = st.empty()

    def _render_events(current: list[AgentProgressEvent], current_node: str | None) -> None:
        completed = sum(1 for e in current if e.status == "completed")
        total = max(len(current), 1)
        pct = completed / total
        progress_box.progress(pct, text=f"Progress {int(pct * 100)}%")
        status_box.info(f"Running: {current_node}" if current_node else "Waiting for the analysis to start…")
        lines = []
        for ev in current:
            msg = f" — {ev.message}" if ev.message else ""
            lines.append(f"{_status_label(ev.status)} **{ev.node}**{msg}")
        steps_box.markdown("\n\n".join(lines) if lines else "_Waiting for the analysis to start…_")

    _render_events(events, events[-1].node if events else None)

    if st.session_state.get("_stream_done"):
        return

    try:
        token = _ensure_token()
        current_node: str | None = None
        for event in subscribe_to_analysis(analysis_id, token):
            events.append(event)
            current_node = event.node
            st.session_state.events = events
            _render_events(events, current_node)

            if event.status == "failed":
                st.session_state.analysis_error = event.message or f"Step failed: {event.node}"
                st.session_state._stream_done = True
                st.rerun()
                return

            result = extract_result(event)
            if result is not None:
                st.session_state.result = result.model_dump()
                st.session_state.page = "results"
                st.session_state._stream_done = True
                st.rerun()
                return
    except ApiError as exc:
        st.session_state.analysis_error = str(exc)
        st.session_state._stream_done = True
        st.rerun()
        return
    except Exception as exc:  # noqa: BLE001
        st.session_state.analysis_error = f"Stream failed: {exc}"
        st.session_state._stream_done = True
        st.rerun()
        return

    if st.session_state.get("result") is None and not st.session_state.get("analysis_error"):
        st.session_state.analysis_error = "Analysis stream ended without a final result."
        st.rerun()
