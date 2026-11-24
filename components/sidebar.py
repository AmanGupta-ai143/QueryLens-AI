"""CSS loading and the settings block shown under the page navigation."""
import streamlit as st

from components.auth import is_admin, logout
from config import ASSETS_DIR


def load_css() -> None:
    """Base styles always; dark-mode overrides when the 🌙 switch is on."""
    names = ["styles.css"] + (["dark.css"] if st.session_state.get("dark_mode") else [])
    css = "\n".join((ASSETS_DIR / n).read_text(encoding="utf-8") for n in names if (ASSETS_DIR / n).exists())
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_sidebar(ctx) -> None:
    with st.sidebar:
        st.markdown("---")
        st.markdown("**⚙️ Answer strictness**")
        st.slider(
            "Similarity threshold", 0.0, 1.0, step=0.01, key="threshold", label_visibility="collapsed",
            help="The bot answers only when its similarity score reaches this value. "
                 "Higher = stricter (more 'I don't know' replies). Lower = more answers, but more mistakes.",
        )
        st.caption("◀ more answers · stricter ▶  (default 0.35)")
        st.markdown(
            f'<div class="side-box">📚 <b>{ctx.faqs.count()}</b> FAQs in the knowledge base<br>'
            f'💬 <b>{ctx.conversations.count()}</b> conversations stored</div>',
            unsafe_allow_html=True)
        if is_admin():
            st.success("🔓 Admin mode is on")
            st.button("Log out", on_click=logout, key="admin_logout")
