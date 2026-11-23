import pandas as pd
import streamlit as st

from components import charts
from components.compat import empty_state, show_chart, show_table
from components.dashboard_cards import hero, pct, render_cards, section
from components.state import get_ctx, init_session
from services import analytics

init_session()
ctx = get_ctx()
df = ctx.conversations.dataframe()
stats = analytics.overview(df, ctx.faqs.count())

hero("Feedback Analytics", "How helpful are the answers? Find FAQs that need a human review.",
     badge="📈 Feedback")

render_cards([
    ("👍", "Helpful", stats["helpful"], ""),
    ("👎", "Not helpful", stats["not_helpful"], ""),
    ("😊", "Satisfaction", pct(stats["satisfaction"]), "helpful ÷ rated responses"),
    ("💤", "No feedback", analytics.feedback_split(df).get("No feedback", 0) if not df.empty else 0, ""),
])

if df.empty:
    empty_state("No conversations yet, so there is no feedback to analyse.", "📈")
    st.stop()

show_chart(charts.feedback_bar(df), key="chart_feedback")

section("FAQs that may need improvement")
st.caption("These FAQs received 'Not helpful' votes. Feedback is **never** used to change answers "
           "automatically - an administrator reviews it first (Knowledge Base → Edit).")
review = ctx.feedback.faqs_needing_review()
if review:
    frame = pd.DataFrame(review)
    frame["Not-helpful rate"] = (frame["not_helpful"] / frame["votes"]).map(lambda x: f"{x:.0%}")
    show_table(frame.rename(columns={"faq_id": "FAQ ID", "question": "Question", "category": "Category",
                                     "helpful": "Helpful", "not_helpful": "Not helpful", "votes": "Votes"}))
else:
    empty_state("No FAQ has received a 'Not helpful' vote.", "🎉")

section("Recent comments")
comments = ctx.feedback.recent_comments(20)
if comments:
    for c in comments:
        icon = "👍" if c["rating"] == "helpful" else "👎"
        st.markdown(f"{icon} {c['feedback_comment']}")
        st.caption(f"on “{c['user_question'][:80]}” · {c['created_at']} UTC")
else:
    empty_state("No written comments yet.", "💬")
