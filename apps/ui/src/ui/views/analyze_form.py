from __future__ import annotations

import streamlit as st

from ui.api.client import ApiError, read_upload_bytes, submit_analysis
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


def render_analyze_form() -> None:
    st.markdown("## Analyze CV")
    st.caption("Submit your CV and a short description to generate a personalized roadmap.")

    with st.form("analyze_form", clear_on_submit=False):
        user_name = st.text_input("Name", placeholder="Your full name")
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input("Phone", placeholder="+1 234 567 890")
        with col2:
            email = st.text_input(
                "Email",
                value=st.session_state.get("user", {}).get("email", ""),
                placeholder="you@example.com",
            )
        description = st.text_area(
            "Description",
            placeholder="Tell us about your experience, goals, and what you are looking for...",
            height=140,
        )
        cv = st.file_uploader(
            "CV / Resume",
            type=["pdf", "doc", "docx", "txt", "md"],
        )
        submitted = st.form_submit_button("Analyze CV", type="primary")

    if not submitted:
        return

    if not all([user_name.strip(), phone.strip(), email.strip(), description.strip(), cv]):
        st.error("All fields are required, including a CV file.")
        return

    try:
        token = _ensure_token()
        cv_name, cv_bytes = read_upload_bytes(cv)
        with st.spinner("Submitting analysis…"):
            res = submit_analysis(
                token=token,
                user_name=user_name.strip(),
                phone=phone.strip(),
                email=email.strip(),
                description=description.strip(),
                cv_name=cv_name,
                cv_bytes=cv_bytes,
            )
    except ApiError as exc:
        st.error(str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        st.error(f"Submission failed: {exc}")
        return

    st.session_state.analysis_id = res.analysis_id
    st.session_state.events = []
    st.session_state.result = None
    st.session_state.analysis_error = None
    st.session_state.page = "progress"
    st.rerun()
