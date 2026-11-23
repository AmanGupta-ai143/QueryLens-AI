"""Shared Streamlit state: one AppContext for the whole server, per-user session."""
import uuid

import streamlit as st

from config import DEFAULT_THRESHOLD
from services.app_context import AppContext


@st.cache_resource(show_spinner="Starting QueryLens AI...")
def get_ctx() -> AppContext:
    return AppContext()


def init_session() -> None:
    st.session_state.setdefault("session_id", uuid.uuid4().hex)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("threshold", DEFAULT_THRESHOLD)
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("topic", None)
