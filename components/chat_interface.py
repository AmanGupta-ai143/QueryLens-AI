"""Chat bubbles, typing indicator, feedback form and NLP-details expander."""
import html
from datetime import datetime

import streamlit as st

from config import local_tz
from errors import DatabaseError, NotFoundError, ValidationError


def now_label() -> str:
    return datetime.now(local_tz()).strftime("%I:%M %p").lstrip("0")


def _safe(text: str) -> str:
    """Escape user/admin text before putting it inside our own HTML."""
    return html.escape(str(text)).replace("\n", "<br>")


def render_user(msg: dict) -> None:
    st.markdown(
        f'<div class="msg-row user"><div class="bubble user">{_safe(msg["content"])}'
        f'<div class="ts">{html.escape(msg["time"])}</div></div></div>',
        unsafe_allow_html=True,
    )


def confidence_label(score: float) -> str:
    """Plain-language label for a similarity score (the exact number is in NLP details)."""
    if score >= 0.55:
        return "High"
    if score >= 0.35:
        return "Good"
    return "Low"


def render_bot(msg: dict) -> None:
    chips = []
    if msg.get("answered"):
        chips.append(f'<span class="pill ok">✅ Answer to: {_safe(msg.get("matched_question", ""))}</span>')
        chips.append(f'<span class="pill">Confidence: {confidence_label(msg.get("score", 0))} '
                     f'({msg.get("score", 0):.0%})</span>')
    else:
        chips.append('<span class="pill warn">❓ No confident match found</span>')
    if msg.get("category") and msg.get("answered"):
        chips.append(f'<span class="pill">Topic: {_safe(msg["category"])}</span>')
    st.markdown(
        f'<div class="msg-row bot"><div class="avatar">✨</div><div class="bubble bot">'
        f'{_safe(msg["content"])}<div class="chips">{"".join(chips)}</div>'
        f'<div class="ts">{html.escape(msg["time"])}</div></div></div>',
        unsafe_allow_html=True,
    )


def render_typing() -> None:
    st.markdown(
        '<div class="msg-row bot"><div class="avatar">✨</div><div class="bubble bot">'
        '<div class="typing"><span></span><span></span><span></span></div></div></div>',
        unsafe_allow_html=True,
    )


def render_nlp_details(msg: dict) -> None:
    details = msg.get("details")
    if not details:
        return
    with st.expander("🔬 NLP details", expanded=False):
        st.markdown(f"**Cleaned text:** `{details['cleaned'] or '—'}`")
        st.markdown(f"**Tokens (stop-words removed):** `{', '.join(details['tokens']) or '—'}`")
        st.markdown("**Top matches (cosine similarity):**")
        for rank, (question, score) in enumerate(details["candidates"], start=1):
            st.markdown(f"{rank}. {question} — `{score:.3f}`")
        st.caption(f"Method: {details['method']} · threshold {details['threshold']:.2f}")


def render_feedback(ctx, msg: dict) -> None:
    """Helpful / Not helpful buttons with an optional comment, stored in SQLite."""
    cid = msg.get("conversation_id")
    if cid is None:
        return
    if msg.get("feedback"):
        label = "👍 helpful" if msg["feedback"] == "helpful" else "👎 not helpful"
        st.caption(f"Thanks for your feedback — marked as {label}.")
        return
    with st.form(key=f"feedback_form_{cid}", border=False):
        c_comment, c_up, c_down = st.columns([5, 1.4, 1.8])
        comment = c_comment.text_input(
            "Optional comment", key=f"feedback_comment_{cid}", max_chars=500,
            placeholder="Optional: tell us what was good or missing…", label_visibility="collapsed")
        up = c_up.form_submit_button("👍 Helpful")
        down = c_down.form_submit_button("👎 Not helpful")
    if up or down:
        rating = "helpful" if up else "not_helpful"
        try:
            ctx.feedback.submit(cid, rating, comment)
            msg["feedback"] = rating
            st.rerun()
        except (ValidationError, NotFoundError, DatabaseError) as exc:
            st.error(str(exc))


def build_bot_message(turn) -> dict:
    r = turn.result
    return {
        "role": "assistant", "content": r.response, "time": now_label(),
        "conversation_id": turn.conversation_id, "answered": r.answered, "score": r.score,
        "matched_question": r.best.question if r.best else "", "category": r.predicted_category,
        "alternatives": [c.question for c in r.candidates if not r.answered and c.score >= 0.15][:2],
        "feedback": None, "storage_error": turn.storage_error,
        "details": {
            "cleaned": r.cleaned, "tokens": r.tokens_no_stopwords,
            "candidates": [(c.question, c.score) for c in r.candidates],
            "method": r.method, "threshold": r.threshold,
        },
    }
