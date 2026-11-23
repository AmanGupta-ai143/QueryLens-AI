import streamlit as st

from components.compat import empty_state
from components.dashboard_cards import hero, render_cards
from components.state import get_ctx, init_session
from config import CATEGORIES
from errors import DatabaseError, NotFoundError, ValidationError

init_session()
ctx = get_ctx()

hero("Unanswered Questions", "Questions the chatbot could not answer confidently - review them and grow the knowledge base.",
     badge="🧭 Admin review")

counts = ctx.unanswered.counts()
render_cards([
    ("📬", "Open", counts["open"], "waiting for review"),
    ("✅", "Resolved", counts["resolved"], ""),
    ("🔁", "Total asks", counts["total_asks"], "including repeats"),
    ("🧩", "Distinct questions", counts["distinct_questions"], ""),
])

st.caption("How it works: open a question → write the answer → click “Create FAQ”. The chatbot can answer it immediately.")
c1, c2 = st.columns([3, 1.3])
search = c1.text_input("Search", placeholder="Search unanswered questions…", key="un_search")
status = c2.selectbox("Status", ["open", "resolved", "all"], key="un_status")
rows = ctx.unanswered.list(status, search)

if not rows:
    empty_state("Nothing here. Questions below the similarity threshold will appear in this list.", "🎉")

for item in rows:
    badge = "🟢 resolved" if item["status"] == "resolved" else "🟠 open"
    with st.expander(f"{badge} · asked {item['frequency']}× · {item['question'][:80]}"):
        st.markdown(f"**Question:** {item['question']}")
        st.caption(f"First seen {item['created_at']} UTC")

        with st.form(f"create_faq_{item['id']}"):
            st.markdown("**Create a new FAQ from this question**")
            q = st.text_input("FAQ question", value=item["question"], key=f"un_q_{item['id']}")
            a = st.text_area("Answer (written by the administrator)", key=f"un_a_{item['id']}", height=100)
            cat = st.selectbox("Category", CATEGORIES, key=f"un_c_{item['id']}")
            kw = st.text_input("Keywords (comma separated)", key=f"un_k_{item['id']}")
            if st.form_submit_button("Create FAQ and mark resolved"):
                try:
                    faq_id = ctx.create_faq_from_unanswered(item["id"], q, a, cat, kw)
                    st.success(f"FAQ #{faq_id} created and the question was marked resolved.")
                    st.rerun()
                except (ValidationError, NotFoundError, DatabaseError) as exc:
                    st.error(str(exc))

        b1, b2, b3 = st.columns(3)
        try:
            if item["status"] == "open":
                if b1.button("✅ Mark resolved", key=f"un_res_{item['id']}"):
                    ctx.unanswered.mark_resolved(item["id"])
                    st.rerun()
            elif b1.button("↩️ Re-open", key=f"un_open_{item['id']}"):
                ctx.unanswered.set_status(item["id"], "open")
                st.rerun()
            if b2.button("🗑️ Delete", key=f"un_del_{item['id']}"):
                ctx.unanswered.delete(item["id"])
                st.rerun()
        except (NotFoundError, DatabaseError) as exc:
            st.error(str(exc))
