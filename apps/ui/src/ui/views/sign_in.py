from __future__ import annotations

import streamlit as st

from ui.auth import authenticate_user, mint_backend_token


def render_sign_in() -> None:
    st.markdown("## Sign in")
    st.caption("Invite-only access. Contact an admin if you need an account.")

    with st.form("sign_in_form", clear_on_submit=False):
        email = st.text_input("Email", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if not submitted:
        return

    if not email.strip() or not password:
        st.error("Email and password are required.")
        return

    user = authenticate_user(email, password)
    if user is None:
        st.error("Invalid email or password.")
        return

    token = mint_backend_token(user.id, user.email, is_admin=user.is_admin)
    st.session_state.user = {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
    }
    st.session_state.token = token
    st.session_state.page = "home"
    st.session_state.pop("analysis_id", None)
    st.session_state.pop("events", None)
    st.session_state.pop("result", None)
    st.session_state.pop("analysis_error", None)
    st.rerun()
