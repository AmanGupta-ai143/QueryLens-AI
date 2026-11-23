import time
import uuid

import streamlit as st

from components.chat_interface import (build_bot_message, now_label, render_bot, render_feedback,
                                       render_nlp_details, render_typing, render_user)
from components.dashboard_cards import hero
from components.state import get_ctx, init_session
from config import APP_NAME, CATEGORIES, CATEGORY_ICONS, MAX_QUESTION_LENGTH
from errors import DatabaseError, ValidationError

init_session()
ctx = get_ctx()
state = st.session_state


def _ask(question: str) -> None:
    state.pending_question = question


def _pick_topic(topic: str) -> None:
    state.topic = None if state.get("topic") == topic else topic


def _clear() -> None:
    state.messages = []
    state.session_id = uuid.uuid4().hex


hero(f"{APP_NAME} Assistant", "Ask in your own words. I'll find the best answer in the FAQ knowledge base.",
     badge="💬 Chat")

# ---- topics -> questions -----------------------------------------------------
by_topic: dict[str, list[str]] = {}
for faq in ctx.faqs.list():
    by_topic.setdefault(faq["category"], []).append(faq["question"])
topics = [c for c in CATEGORIES if c in by_topic]

if not state.messages:
    st.markdown(
        '<div class="nova-card"><b>👋 Hi! I\'m your campus FAQ assistant.</b><br>'
        "Type a question below, or pick a topic to see common questions."
        '<div class="tip-row">'
        '<div class="tip">💡 <b>Ask naturally</b><br>“How do I get admission?”</div>'
        '<div class="tip">✍️ <b>Typos are okay</b><br>I can still match them</div>'
        '<div class="tip">🙋 <b>Not sure? I\'ll say so</b><br>Unanswered questions go to the admin</div>'
        "</div></div>", unsafe_allow_html=True)

with st.expander("🧭 Browse by topic", expanded=not state.messages):
    cols = st.columns(5)
    for i, topic in enumerate(topics):
        cols[i % 5].button(f"{CATEGORY_ICONS.get(topic, '📌')} {topic}", key=f"topic_{topic}",
                           on_click=_pick_topic, args=(topic,))
    if state.get("topic") in by_topic:
        st.markdown(f"**Common questions about {state.topic}:**")
        for j, question in enumerate(by_topic[state.topic][:5]):
            st.button(question, key=f"topicq_{j}", on_click=_ask, args=(question,))

if state.messages:
    st.button("🗑️ Start a new conversation", on_click=_clear, key="clear_top")

# ---- conversation ------------------------------------------------------------
last = len(state.messages) - 1
for i, msg in enumerate(state.messages):
    if msg["role"] == "user":
        render_user(msg)
        continue
    render_bot(msg)
    if msg.get("storage_error"):
        st.warning("⚠️ This answer could not be saved to history: " + msg["storage_error"])
    if i == last and msg.get("alternatives"):
        st.caption("Did you mean one of these?")
        for j, alt in enumerate(msg["alternatives"]):
            st.button(alt, key=f"alt_{i}_{j}", on_click=_ask, args=(alt,))
    render_feedback(ctx, msg)
    render_nlp_details(msg)

# ---- input -------------------------------------------------------------------
typed = st.chat_input("Type your question here…", max_chars=MAX_QUESTION_LENGTH)
question = state.pending_question or typed
state.pending_question = None

if question is not None:
    user_msg = {"role": "user", "content": question.strip(), "time": now_label()}
    try:
        if not question.strip():
            raise ValidationError("Please type a question before sending.")
        render_user(user_msg)
        typing = st.empty()
        with typing.container():
            render_typing()
        time.sleep(0.4)  # brief "typing" indicator
        turn = ctx.chat.ask(state.session_id, question, state.threshold)
        typing.empty()
        state.messages.append(user_msg)
        state.messages.append(build_bot_message(turn))
        st.rerun()
    except ValidationError as exc:
        st.warning(str(exc))
    except DatabaseError as exc:
        st.error(f"Something went wrong with the database: {exc}")
