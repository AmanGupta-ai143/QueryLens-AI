import pandas as pd
import streamlit as st

from components.auth import require_admin
from components.compat import empty_state, show_table
from components.dashboard_cards import hero
from components.state import get_ctx, init_session
from config import CATEGORIES, CATEGORY_ICONS, MAX_FAQ_ANSWER_LENGTH, MAX_FAQ_QUESTION_LENGTH
from errors import DatabaseError, NotFoundError, ValidationError
from services import analytics

init_session()
ctx = get_ctx()

hero("FAQ Knowledge Base", "Add, edit, search and organise the questions the chatbot can answer.",
     badge="📚 Knowledge base")
st.caption("Changes take effect immediately: the chatbot uses a new or edited FAQ straight away. "
           "The sample data is for a fictional 'Nova University'. Replace it with your own FAQs.")
counts = ctx.faqs.category_counts()
st.markdown("".join(f'<span class="pill">{CATEGORY_ICONS.get(c, "📌")} {c}: {n}</span>' for c, n in counts.items()),
            unsafe_allow_html=True)

tab_browse, tab_add, tab_edit, tab_import, tab_top = st.tabs(
    ["📖 Browse & search", "➕ Add FAQ", "✏️ Edit / Delete", "📥 Import CSV", "🔥 Most asked"])

# ------------------------------------------------------------------ browse
with tab_browse:
    c1, c2 = st.columns([3, 1])
    search = c1.text_input("Search FAQs", placeholder="Search questions, answers or keywords…", key="kb_search")
    category = c2.selectbox("Category", ["All"] + CATEGORIES, key="kb_category")
    rows = ctx.faqs.list(search, category)
    st.caption(f"Showing {len(rows)} of {ctx.faqs.count()} FAQs")
    if rows:
        frame = pd.DataFrame(rows).rename(columns={
            "id": "FAQ ID", "question": "Question", "answer": "Answer", "category": "Category",
            "keywords": "Keywords", "created_at": "Created (UTC)"})
        show_table(frame[["FAQ ID", "Question", "Answer", "Category", "Keywords", "Created (UTC)"]])
    else:
        empty_state("No FAQs match your search.", "🔎")

# --------------------------------------------------------------------- add
with tab_add:
    if require_admin("Adding FAQs", "kb_add"):
        with st.form("add_faq_form", clear_on_submit=True):
            q = st.text_input("Question", max_chars=MAX_FAQ_QUESTION_LENGTH)
            a = st.text_area("Answer", max_chars=MAX_FAQ_ANSWER_LENGTH, height=130)
            cat = st.selectbox("Category", CATEGORIES)
            kw = st.text_input("Keywords (comma separated)", placeholder="fee, tuition, payment")
            if st.form_submit_button("Add FAQ"):
                try:
                    new_id = ctx.add_faq(q, a, cat, kw)
                    st.success(f"FAQ #{new_id} added.")
                except (ValidationError, DatabaseError) as exc:
                    st.error(str(exc))

# -------------------------------------------------------------- edit/delete
with tab_edit:
    if require_admin("Editing or deleting FAQs", "kb_edit"):
        all_faqs = ctx.faqs.list()
        if not all_faqs:
            empty_state("The knowledge base is empty.")
        else:
            labels = {f["id"]: f"#{f['id']} · [{f['category']}] {f['question']}" for f in all_faqs}
            faq_id = st.selectbox("Choose an FAQ", list(labels), format_func=labels.get, key="edit_select")
            faq = ctx.faqs.get(faq_id)
            if faq:
                with st.form(f"edit_faq_form_{faq_id}"):
                    q = st.text_input("Question", value=faq["question"], max_chars=MAX_FAQ_QUESTION_LENGTH)
                    a = st.text_area("Answer", value=faq["answer"], max_chars=MAX_FAQ_ANSWER_LENGTH, height=130)
                    cat = st.selectbox("Category", CATEGORIES,
                                       index=CATEGORIES.index(faq["category"]) if faq["category"] in CATEGORIES else 0)
                    kw = st.text_input("Keywords", value=faq["keywords"])
                    if st.form_submit_button("Save changes"):
                        try:
                            ctx.update_faq(faq_id, q, a, cat, kw)
                            st.success("FAQ updated.")
                        except (ValidationError, NotFoundError, DatabaseError) as exc:
                            st.error(str(exc))
                st.caption(f"Created {faq['created_at']} UTC · last updated {faq['updated_at']} UTC")
                st.markdown("**Danger zone**")
                confirm = st.checkbox("I understand this FAQ will be permanently deleted", key=f"confirm_del_{faq_id}")
                if st.button("🗑️ Delete this FAQ", disabled=not confirm, key=f"del_{faq_id}"):
                    try:
                        ctx.delete_faq(faq_id)
                        st.success("FAQ deleted.")
                        st.rerun()
                    except DatabaseError as exc:
                        st.error(str(exc))

# ------------------------------------------------------------------ import
with tab_import:
    if require_admin("Importing FAQs", "kb_import"):
        st.markdown("Upload a **.csv** file (max 1 MB, 500 rows) with the columns "
                    "`question, answer, category` and optionally `keywords`.")
        st.caption("Categories must be: " + ", ".join(CATEGORIES))
        upload = st.file_uploader("CSV file", type=["csv"], key="kb_import")
        if upload is not None and st.button("Import FAQs", key="kb_import_btn"):
            try:
                report = ctx.import_faqs_csv(upload.getvalue(), upload.name)
                st.success(f"Imported {report['added']} FAQ(s); skipped {report['skipped']}.")
                for line in report["errors"][:15]:
                    st.caption("• " + line)
            except (ValidationError, DatabaseError) as exc:
                st.error(str(exc))

# --------------------------------------------------------------- most asked
with tab_top:
    top = analytics.top_faqs(ctx.conversations.dataframe(), 15)
    if top.empty:
        empty_state("No FAQ has been matched yet - ask questions in the Chatbot page first.")
    else:
        show_table(top.rename(columns={"question": "FAQ question", "times_matched": "Times matched"}))
