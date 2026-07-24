from __future__ import annotations

import streamlit as st

from ui.api.models import AnalyzeResult


def render_results() -> None:
    raw = st.session_state.get("result")
    if not raw:
        st.session_state.page = "home"
        st.rerun()
        return

    result = AnalyzeResult.model_validate(raw)
    resume = result.level_resume

    st.markdown("## Analysis Results")
    st.caption("Here is what we found based on your CV and description.")

    if st.button("New analysis"):
        st.session_state.page = "home"
        st.session_state.pop("analysis_id", None)
        st.session_state.pop("events", None)
        st.session_state.pop("result", None)
        st.session_state.pop("analysis_error", None)
        st.session_state.pop("_stream_done", None)
        st.rerun()

    st.markdown("### Level Resume")
    st.write(resume.summary)

    col_s, col_w = st.columns(2)
    with col_s:
        st.markdown("**Strong points**")
        if resume.strong_points:
            for pt in resume.strong_points:
                st.markdown(f"- {pt}")
        else:
            st.caption("None listed")
    with col_w:
        st.markdown("**Weak points**")
        if resume.weak_points:
            for pt in resume.weak_points:
                st.markdown(f"- {pt}")
        else:
            st.caption("None listed")

    st.markdown(f"**Estimated level:** `{resume.estimated_level or 'unknown'}`")

    st.markdown("### Compatibility Score")
    score = max(0, min(100, result.compatibility_score))
    st.metric("Score", f"{score} / 100")
    st.progress(score / 100)

    st.markdown("### Personalized Roadmap")
    if not result.personalized_roadmap:
        st.info("No roadmap nodes were returned.")
        return

    cols = st.columns(2)
    for i, node in enumerate(result.personalized_roadmap):
        with cols[i % 2], st.container(border=True):
            st.markdown(f"**{node.name}**")
            st.caption(node.description or "No description available.")
            st.markdown(
                f"`{node.category or '—'}` · `{node.level or '—'}` · importance **{node.importance}**"
            )

    if result.errors:
        st.warning("Pipeline reported errors:\n\n" + "\n".join(f"- {e}" for e in result.errors))
