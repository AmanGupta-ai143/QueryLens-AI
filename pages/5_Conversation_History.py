import pandas as pd
import streamlit as st

from components.auth import require_admin
from components.compat import empty_state
from components.dashboard_cards import hero
from components.state import get_ctx, init_session
from errors import DatabaseError

init_session()
ctx = get_ctx()

hero("Conversation History", "Search, review and delete previous conversations stored in SQLite.",
     badge="🕘 History")

if not require_admin("Conversation history", "hist"):
    st.stop()

st.caption("Click a row to read the full conversation, see the matched FAQ and feedback, or delete it.")
c1, c2, c3 = st.columns([3, 1.4, 1.2])
search = c1.text_input("Search conversations", placeholder="Search questions, answers or FAQs…", key="hist_search")
status = c2.selectbox("Filter", ["all", "answered", "unanswered", "helpful", "not_helpful", "no_feedback"],
                      format_func=lambda s: s.replace("_", " ").title(), key="hist_status")
limit = c3.selectbox("Show", [25, 50, 100, 200], index=1, key="hist_limit")

rows = ctx.conversations.list(search, int(limit), status)
total = ctx.conversations.count()
st.caption(f"Showing {len(rows)} of {total} stored conversation(s)")

if not rows:
    empty_state("No conversations found.", "🕘")
else:
    export = pd.DataFrame(rows)[["id", "timestamp", "user_question", "bot_response", "matched_question",
                                 "similarity_score", "feedback_rating", "feedback_comment"]]
    st.download_button("⬇️ Download shown rows as CSV", export.to_csv(index=False).encode("utf-8"),
                       file_name="querylens_conversations.csv", mime="text/csv")

    for row in rows:
        icon = "✅" if row["matched_faq_id"] is not None else "❓"
        title = f"{icon} #{row['id']} · {row['timestamp']} UTC · {row['user_question'][:70]}"
        with st.expander(title):
            st.markdown(f"**🧑 User:** {row['user_question']}")
            st.markdown(f"**🤖 Chatbot:** {row['bot_response']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Similarity", f"{row['similarity_score']:.2f}")
            m2.markdown("**Matched FAQ**")
            m2.write(row["matched_question"] or ("—" if row["matched_faq_id"] is None else "(deleted FAQ)"))
            rating = {"helpful": "👍 Helpful", "not_helpful": "👎 Not helpful"}.get(row["feedback_rating"], "No feedback")
            m3.markdown("**Feedback**")
            m3.write(rating)
            if row["feedback_comment"]:
                st.caption(f"Comment: {row['feedback_comment']}")
            if st.button("🗑️ Delete this conversation", key=f"del_conv_{row['id']}"):
                try:
                    ctx.conversations.delete(row["id"])
                    st.rerun()
                except DatabaseError as exc:
                    st.error(str(exc))

st.markdown("---")
with st.expander("Delete ALL conversations"):
    st.warning("This permanently removes every stored conversation and its feedback.")
    sure = st.checkbox("Yes, delete everything", key="hist_delete_all_confirm")
    if st.button("Delete all conversations", disabled=not sure, key="hist_delete_all"):
        try:
            n = ctx.conversations.delete_all()
            st.success(f"Deleted {n} conversation(s).")
            st.rerun()
        except DatabaseError as exc:
            st.error(str(exc))
