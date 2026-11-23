import streamlit as st

from components import charts
from components.compat import empty_state, show_chart, show_table
from components.dashboard_cards import hero, pct, render_cards, score_fmt, section
from components.state import get_ctx, init_session
from config import APP_NAME, APP_TAGLINE
from services import analytics

init_session()
ctx = get_ctx()
df = ctx.conversations.dataframe()
stats = analytics.overview(df, ctx.faqs.count())
threshold = st.session_state.threshold

hero(f"{APP_NAME} Dashboard", f"{APP_TAGLINE} · live numbers from real conversations.", badge="📊 Overview")

if stats["total_questions"]:
    rate = stats["answered"] / stats["total_questions"]
    st.markdown(
        f'<div class="glance">📌 <b>At a glance:</b> the bot answered <b>{rate:.0%}</b> of '
        f'<b>{stats["total_questions"]}</b> question(s) and <b>{stats["unanswered"]}</b> need a new FAQ.</div>',
        unsafe_allow_html=True)

render_cards([
    ("💬", "Questions asked", stats["total_questions"], "all conversations"),
    ("✅", "Answered", stats["answered"], f"score ≥ {threshold:.2f}"),
    ("❓", "Unanswered", stats["unanswered"], "below the threshold"),
    ("😊", "User satisfaction", pct(stats["satisfaction"]), f"{stats['feedback_votes']} rated answer(s)"),
])
with st.expander("More numbers"):
    render_cards([
        ("📚", "FAQs available", stats["faq_count"], "in the knowledge base"),
        ("🎯", "Average similarity", score_fmt(stats["avg_similarity"]), "mean cosine score"),
        ("👍", "Helpful votes", stats["helpful"], ""),
        ("👎", "Not helpful votes", stats["not_helpful"], ""),
    ])

if df.empty:
    empty_state("No conversations yet. Ask something in the Chatbot page and the charts will appear here. "
                "Every number on this page comes from real database records.", "💬")
else:
    tab_activity, tab_topics, tab_quality = st.tabs(["📈 Activity", "🧩 Topics", "🎯 Answer quality"])

    with tab_activity:
        period = st.radio("Group by", ["Daily", "Weekly", "Monthly"], horizontal=True, key="dash_period")
        show_chart(charts.activity_line(df, period), key="chart_activity")
        section("Recent questions")
        recent = df.sort_values("id", ascending=False).head(10).copy()
        recent["Time"] = recent["timestamp"].dt.strftime("%d %b, %I:%M %p")
        recent["Status"] = recent["answered"].map({True: "✅ Answered", False: "❓ Unanswered"})
        show_table(recent[["Time", "user_question", "matched_question", "similarity_score", "Status"]].rename(
            columns={"user_question": "Question", "matched_question": "Matched FAQ", "similarity_score": "Score"}))

    with tab_topics:
        left, right = st.columns(2)
        with left:
            fig = charts.category_donut(df)
            show_chart(fig, key="chart_cat_donut") if fig else empty_state("No answered questions yet.")
        with right:
            show_chart(charts.category_bar(df), key="chart_cat_bar")
        fig = charts.top_faqs_bar(df)
        show_chart(fig, key="chart_top_faqs") if fig else empty_state("No FAQ has been matched yet.")

    with tab_quality:
        left, right = st.columns(2)
        with left:
            show_chart(charts.success_donut(df, threshold), key="chart_success")
        with right:
            show_chart(charts.similarity_hist(df, threshold), key="chart_hist")
