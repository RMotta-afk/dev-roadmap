from __future__ import annotations

import streamlit as st

from ui.api.client import ApiError, fetch_pdf
from ui.api.models import AnalyzeResult


def _parse_name_for_filename(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "Usuario"
    parts = full_name.strip().split()
    return "_".join(parts)


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

    st.markdown("---")
    st.markdown("### 📄 Exportar Roadmap")

    analysis_id = st.session_state.get("analysis_id")
    token = st.session_state.get("token")
    user_name = st.session_state.get("user_name", "")

    if not analysis_id or not token:
        st.info("Informações da sessão não disponíveis para exportação.")
    else:
        if st.button("📥 Baixar PDF do Roadmap", type="primary", use_container_width=True):
            try:
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = fetch_pdf(analysis_id, token)

                filename = f"{_parse_name_for_filename(user_name)}_roadmap.pdf"
                st.download_button(
                    label="Clique aqui para salvar o PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    type="secondary",
                    use_container_width=True
                )
                st.success("PDF pronto! Clique no botão acima para baixar.")

            except ApiError as e:
                st.error(f"Erro ao gerar PDF: {e}")
