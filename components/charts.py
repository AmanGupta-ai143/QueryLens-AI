"""Plotly charts built from real database records (None = nothing to plot).

Fonts/axes/grid colours come from Streamlit's own Plotly theme
(``st.plotly_chart(theme="streamlit")``), so every chart follows the app's
light or dark mode. Backgrounds are transparent.
"""
import plotly.graph_objects as go

from services import analytics

PALETTE = ["#7C5CFF", "#4F8BFF", "#22C1A9", "#F5A623", "#FF6B8B",
           "#9B8CFF", "#5ED0FA", "#B0B7FF", "#FFB4D1", "#7DE0B1"]
GOOD, BAD, NEUTRAL = "#22C1A9", "#FF6B8B", "#9AA0B5"


def _style(fig: go.Figure, title: str, x: str | None = None, y: str | None = None,
           height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(size=16)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=40), height=height,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        hoverlabel=dict(font_size=13),
    )
    if x is not None:
        fig.update_xaxes(title_text=x)
    if y is not None:
        fig.update_yaxes(title_text=y)
    return fig


def _donut(labels, values, title, colors=None) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=list(labels), values=list(values), hole=0.55, sort=False,
        marker=dict(colors=colors or PALETTE[: len(labels)]),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    return _style(fig, title)


def activity_line(df, period: str = "Daily"):
    series = analytics.activity_series(df, period)
    if series.empty:
        return None
    fig = go.Figure(go.Scatter(
        x=series.index, y=series.values, mode="lines+markers",
        line=dict(color=PALETTE[0], width=3, shape="spline"), marker=dict(size=8),
        fill="tozeroy", fillcolor="rgba(124,92,255,0.15)",
        hovertemplate="%{x|%d %b %Y}<br>%{y} question(s)<extra></extra>",
    ))
    fig.update_yaxes(rangemode="tozero", dtick=1 if series.max() < 8 else None)
    return _style(fig, f"Chatbot activity over time ({period.lower()})", "Date", "Number of questions")


def category_donut(df):
    s = analytics.category_distribution(df)
    return None if s.empty else _donut(s.index, s.values, "Answered questions by FAQ category")


def top_faqs_bar(df, n: int = 10):
    top = analytics.top_faqs(df, n)
    if top.empty:
        return None
    fig = go.Figure(go.Bar(
        x=top["times_matched"], y=top["question"], orientation="h", marker_color=PALETTE[0],
        hovertemplate="%{y}<br>Matched %{x} time(s)<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(dtick=1 if top["times_matched"].max() < 8 else None)
    return _style(fig, f"Top {len(top)} most frequently matched FAQs", "Times matched", "FAQ question",
                  height=max(320, 60 + 38 * len(top)))


def success_donut(df, threshold: float | None = None):
    s = analytics.success_split(df)
    if s.empty:
        return None
    note = f" (threshold {threshold:.2f})" if threshold is not None else ""
    return _donut(s.index, s.values, f"Answer success rate{note}", [GOOD, BAD])


def similarity_hist(df, threshold: float | None = None):
    scores = df["similarity_score"].dropna()
    if scores.empty:
        return None
    fig = go.Figure(go.Histogram(
        x=scores, xbins=dict(start=0, end=1, size=0.05), marker_color=PALETTE[0],
        hovertemplate="Score %{x}<br>%{y} response(s)<extra></extra>",
    ))
    if threshold is not None:
        fig.add_vline(x=threshold, line_dash="dash", line_color=PALETTE[3],
                      annotation_text=f"current threshold {threshold:.2f}")
    fig.update_xaxes(range=[0, 1])
    return _style(fig, "Similarity score distribution", "Similarity score", "Number of responses")


def feedback_bar(df):
    s = analytics.feedback_split(df)
    if s.empty:
        return None
    fig = go.Figure(go.Bar(
        x=s.index, y=s.values, marker_color=[GOOD, BAD, NEUTRAL],
        text=s.values, textposition="outside",
        hovertemplate="%{x}: %{y} response(s)<extra></extra>",
    ))
    fig.update_yaxes(rangemode="tozero", dtick=1 if s.max() < 8 else None)
    return _style(fig, "User feedback analysis", "Feedback type", "Number of responses")


def category_bar(df):
    s = analytics.detected_category_counts(df)
    if s.empty:
        return None
    fig = go.Figure(go.Bar(
        x=s.index, y=s.values, marker_color=PALETTE[: len(s)],
        hovertemplate="%{x}: %{y} question(s)<extra></extra>",
    ))
    fig.update_yaxes(rangemode="tozero", dtick=1 if s.max() < 8 else None)
    return _style(fig, "Questions by detected category", "Category", "Number of questions")


def candidate_bar(candidates):
    """Word / character / final scores for the top FAQ candidates (NLP Insights)."""
    if not candidates:
        return None
    names = [f"#{c.faq_id} {c.question[:38]}{'…' if len(c.question) > 38 else ''}" for c in candidates]
    fig = go.Figure()
    fig.add_bar(name="Word TF-IDF", x=names, y=[c.word_score for c in candidates], marker_color=PALETTE[1])
    fig.add_bar(name="Character TF-IDF", x=names, y=[c.char_score for c in candidates], marker_color=PALETTE[2])
    fig.add_bar(name="Final score", x=names, y=[c.score for c in candidates], marker_color=PALETTE[0])
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 1])
    return _style(fig, "Top candidate FAQs - cosine similarity", "Candidate FAQ", "Similarity (0-1)", height=360)
