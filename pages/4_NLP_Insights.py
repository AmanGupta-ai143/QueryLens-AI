import pandas as pd
import streamlit as st

from components import charts
from components.compat import show_chart, show_table
from components.dashboard_cards import hero, section
from components.state import get_ctx, init_session
from errors import ValidationError
from nlp.chatbot_engine import METHOD_NAME
from nlp.preprocessing import STOPWORDS

init_session()
ctx = get_ctx()
engine = ctx.engine
threshold = st.session_state.threshold

hero("NLP Insights", "See exactly how a question becomes an answer, step by step, with real numbers.",
     badge="🔬 How it works")

question = st.text_input("✍️ Type any question to analyse", value="I want to know the admission application process.",
                         key="nlp_question", max_chars=500)

try:
    result = engine.answer(question, threshold)
except ValidationError as exc:
    st.warning(str(exc))
    st.stop()

if result.status == "empty_kb":
    st.warning("The knowledge base is empty. Add FAQs first.")
    st.stop()

if result.answered:
    st.success(f"✅ **Answered.** The closest FAQ is “{result.best.question}” with a similarity of "
               f"**{result.score:.0%}**, which is above the threshold of {threshold:.0%}.")
else:
    st.warning(f"❓ **Not answered.** The best similarity was only **{result.score:.0%}**, below the "
               f"threshold of {threshold:.0%}, so the bot refuses to guess.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Similarity score", f"{result.score:.3f}")
c2.metric("Threshold", f"{threshold:.2f}")
c3.metric("Result", "Answered" if result.answered else "Fallback")
c4.metric("Predicted category", result.predicted_category or "—")

tab_steps, tab_scores, tab_method = st.tabs(["🪜 Step by step", "📊 Scores & answer", "📖 About the method"])

with tab_steps:
    st.caption("Pipeline: Cleaning → Tokenization → Stop-word removal → Stemming → TF-IDF → Cosine similarity")
    left, right = st.columns(2)
    with left:
        st.markdown("**1 · Cleaned text**")
        st.code(result.cleaned or "(empty)", language=None)
        st.markdown("**2 · Tokens**")
        st.code(", ".join(result.tokens) or "(none)", language=None)
        st.markdown("**3 · After stop-word removal**")
        st.code(", ".join(result.tokens_no_stopwords) or "(none)", language=None)
        st.markdown("**4 · Stems**")
        st.code(", ".join(result.stems) or "(none)", language=None)
    with right:
        st.markdown("**5 · TF-IDF weight of each query word**")
        st.caption("Rare, meaningful words get a higher weight than common ones.")
        if result.term_weights:
            show_table(pd.DataFrame(result.term_weights, columns=["Term", "TF-IDF weight"]).round(4))
        else:
            st.caption("None of the query words exist in the FAQ vocabulary.")

with tab_scores:
    if result.candidates:
        show_chart(charts.candidate_bar(result.candidates), key="chart_candidates")
        show_table(pd.DataFrame([{
            "FAQ ID": c.faq_id, "Question": c.question, "Category": c.category,
            "Word score": c.word_score, "Char score": c.char_score, "Final score": c.score}
            for c in result.candidates]))
    section("Result")
    if result.answered:
        st.markdown(f"**Matched FAQ:** {result.best.question}")
        st.markdown(f"**Retrieved answer:** {result.response}")
    else:
        st.markdown(f"**Fallback response:** {result.response}")
    if result.category_scores:
        st.caption("Intent scores (best candidate per category): " +
                   ", ".join(f"{k}: {v:.2f}" for k, v in result.category_scores.items()))
    section("Keyword matching vs similarity matching")
    st.markdown(
        f"* **Exact string match:** {'found the FAQ ✅' if result.exact_match else 'finds nothing ❌ (the wording is not identical)'}\n"
        f"* **TF-IDF + cosine similarity:** "
        f"{'retrieved **' + result.best.question + '** ✅' if result.answered else 'no confident match ❓'}")

with tab_method:
    st.markdown(f"""
**Method:** {METHOD_NAME}

1. **Cleaning**: lower-case, remove URLs, punctuation and special characters, collapse spaces.
2. **Tokenization**: split into words with NLTK's `RegexpTokenizer`.
3. **Stop-words**: remove {len(STOPWORDS)} common words (*the, how, can, I…*); negations are kept.
4. **Stemming**: group word forms (*fees → fee, applying → appli*).
5. **TF-IDF**: every FAQ (question + keywords) and the query become weighted vectors, at **word level** and
   **character 3-5-gram level** (so small spelling mistakes still match).
6. **Cosine similarity**: the angle between the query and each FAQ, from 0 (nothing shared) to 1 (identical).
   Final score = `max(0.6·word + 0.4·char, 0.85·char)`.
7. **Threshold**: below it, the bot shows a fallback and saves the question for the admin.
8. **Intent**: the category of the best match.
""")
    with st.expander("⚠️ Honest limitations (lexical vs semantic)"):
        st.markdown(
            "TF-IDF and cosine similarity compare **words and characters, not meaning**. "
            "*“I want to know the admission application process”* matches *“How can I apply for admission?”* "
            "because they share *admission/application* vocabulary. A paraphrase with different words "
            "(*“How do I enrol?”*) may be missed.\n\n"
            "The engine lives in `nlp/chatbot_engine.py`, so **sentence embeddings** or an LLM can be plugged in "
            "later without touching the UI.")
    st.caption(f"Index: {len(engine.faqs)} FAQs · {engine.vectorizer.vocabulary_size} word-level terms")
