import streamlit as st

from components.dashboard_cards import hero, section
from config import APP_NAME
from nlp.chatbot_engine import METHOD_NAME

hero(f"About {APP_NAME}", "An NLP-based FAQ chatbot built for the AI Internship task “Chatbot for FAQs”.",
     badge="ℹ️ About the project")

section("Introduction & objective")
st.markdown(
    f"**{APP_NAME}** answers questions by comparing them with a knowledge base of FAQs using classic NLP. "
    "It understands differently-worded questions, picks the most relevant FAQ, shows *why* it was chosen "
    "(similarity score, category, tokens) and refuses to guess when confidence is too low.")

section("Internship")
st.markdown(
    "This project was developed as an assignment for the **Artificial Intelligence Internship** "
    "(task: *Chatbot for FAQs*). It is a learning/portfolio project and "
    "carries no official endorsement beyond the internship assignment.")

section("Technologies")
st.markdown("""
| Layer | Technology |
|---|---|
| Language / UI | Python, Streamlit, custom CSS |
| NLP | NLTK tokenizer, scikit-learn TF-IDF, cosine similarity |
| Data | SQLite, Pandas |
| Charts | Plotly |
""")

section("NLP algorithms")
st.markdown(f"""
* Text cleaning → tokenization → stop-word removal → rule-based stemming
* **TF-IDF** (word uni/bi-grams + character 3-5-grams)
* **Cosine similarity**, final score `max(0.6·word + 0.4·char, 0.85·char)`
* Confidence threshold + fallback, category (intent) from the best match
* Method label shown to users: *{METHOD_NAME}*
""")

section("System architecture")
st.graphviz_chart("""
digraph G {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#EDE9FF", color="#7C5CFF", fontname="Helvetica"];
  UI [label="Streamlit UI\\n(pages + components)"];
  CS [label="ChatService"];
  NLP [label="ChatbotEngine\\nclean → tokenize → TF-IDF → cosine"];
  SV [label="Services\\nFAQ · Conversation · Feedback · Unanswered"];
  DB [label="SQLite", shape=cylinder, fillcolor="#DDE7FF"];
  UI -> CS -> NLP;
  CS -> SV -> DB;
  UI -> SV;
  SV -> NLP [label="rebuild index", style=dashed];
}
""")

section("Working methodology")
st.markdown("""
1. The user asks a question → validated (empty / too long / no letters are rejected).
2. The engine cleans and tokenizes it, builds TF-IDF vectors and computes cosine similarity with every FAQ.
3. Score ≥ threshold → the FAQ answer is shown. Otherwise → fallback reply + the question is saved as *unanswered*.
4. The conversation is stored; the user can rate it 👍/👎 with an optional comment.
5. An administrator reviews unanswered questions and feedback, then updates the knowledge base.
""")

section("Limitations & future improvements")
st.markdown("""
* TF-IDF is **lexical**: it does not truly understand meaning, so pure paraphrases may be missed.
* English text only; the sample FAQs are for a fictional university.
* SQLite on free cloud hosts may not persist - use a hosted database for long-term deployments.
* **Future:** sentence embeddings (`sentence-transformers`), optional LLM answer rewriting, admin login,
  multilingual support, voice input.
""")
