"""QueryLens AI - entry point.  Run with:  streamlit run app.py"""
import streamlit as st

from config import APP_NAME, ASSETS_DIR

st.set_page_config(
    page_title=f"{APP_NAME} – Intelligent FAQ Chatbot",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.sidebar import load_css, render_sidebar  # noqa: E402
from components.state import get_ctx, init_session  # noqa: E402

init_session()
ctx = get_ctx()
load_css()

logo = ASSETS_DIR / "logo.png"
if logo.exists():
    st.logo(str(logo))

navigation = st.navigation([
    st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊", url_path="dashboard"),
    st.Page("pages/2_Chatbot.py", title="Chatbot", icon="💬", default=True),
    st.Page("pages/3_FAQ_Knowledge_Base.py", title="FAQ Knowledge Base", icon="📚", url_path="knowledge-base"),
    st.Page("pages/4_NLP_Insights.py", title="NLP Insights", icon="🔬", url_path="nlp-insights"),
    st.Page("pages/5_Conversation_History.py", title="Conversation History", icon="🕘", url_path="history"),
    st.Page("pages/6_Unanswered_Questions.py", title="Unanswered Questions", icon="❓", url_path="unanswered"),
    st.Page("pages/7_Feedback_Analytics.py", title="Feedback Analytics", icon="📈", url_path="feedback"),
    st.Page("pages/8_About.py", title="About Project", icon="ℹ️", url_path="about"),
])
render_sidebar(ctx)
navigation.run()
