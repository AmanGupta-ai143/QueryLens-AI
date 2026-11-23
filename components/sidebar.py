"""CSS loading and the settings block shown under the page navigation."""
import streamlit as st

from config import ASSETS_DIR


def load_css() -> None:
    css_path = ASSETS_DIR / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


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
        st.caption("🌗 Light / Dark / System: open the ⋮ menu (top right) → Settings → Theme.")
