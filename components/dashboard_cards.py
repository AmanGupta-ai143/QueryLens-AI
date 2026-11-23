"""Hero banner and statistic cards."""
import html

import streamlit as st


def hero(title: str, subtitle: str, badge: str = "✨ QueryLens AI") -> None:
    st.markdown(
        f'<div class="hero"><span class="badge">{html.escape(badge)}</span>'
        f"<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)


def stat_card(icon: str, label: str, value, hint: str = "") -> str:
    hint_html = f'<div class="hint">{html.escape(hint)}</div>' if hint else ""
    return (f'<div class="stat-card"><div class="icon">{icon}</div>'
            f'<div class="value">{html.escape(str(value))}</div>'
            f'<div class="label">{html.escape(label)}</div>{hint_html}</div>')


def render_cards(cards: list[tuple], per_row: int = 4) -> None:
    """cards = [(icon, label, value, hint), ...]"""
    for start in range(0, len(cards), per_row):
        cols = st.columns(per_row)
        for col, card in zip(cols, cards[start:start + per_row]):
            col.markdown(stat_card(*card), unsafe_allow_html=True)
        st.write("")


def pct(value) -> str:
    return "—" if value is None else f"{value * 100:.0f}%"


def score_fmt(value) -> str:
    return "—" if value is None else f"{value:.2f}"
