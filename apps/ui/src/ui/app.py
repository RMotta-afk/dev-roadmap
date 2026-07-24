from __future__ import annotations

import sys
from pathlib import Path

# Allow `streamlit run src/ui/app.py` without installing the package first.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from ui.views.analyze_form import render_analyze_form
from ui.views.progress import render_progress
from ui.views.results import render_results
from ui.views.sign_in import render_sign_in


def _init_state() -> None:
    st.session_state.setdefault("page", "sign_in")
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("token", None)


def _sign_out() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def _header() -> None:
    left, right = st.columns([4, 1])
    with left:
        st.markdown("### DevRoadmap")
    with right:
        user = st.session_state.get("user")
        if user:
            st.caption(user.get("email", ""))
            if st.button("Sign out", use_container_width=True):
                _sign_out()


def main() -> None:
    st.set_page_config(
        page_title="DevRoadmap",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _init_state()
    _header()
    st.divider()

    user = st.session_state.get("user")
    page = st.session_state.get("page", "sign_in")

    if not user:
        render_sign_in()
        st.divider()
        st.caption("© DevRoadmap. Internal use only.")
        return

    if page == "home":
        render_analyze_form()
    elif page == "progress":
        render_progress()
    elif page == "results":
        render_results()
    else:
        st.session_state.page = "home"
        st.rerun()

    st.divider()
    st.caption("© DevRoadmap. Internal use only.")


if __name__ == "__main__":
    main()
