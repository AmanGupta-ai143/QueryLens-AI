"""Pure-pandas aggregations behind the dashboard (no Streamlit, no fake data).

Definitions
-----------
* answered   = the best FAQ score reached the similarity threshold that was
               active when the question was asked (``matched_faq_id`` is set).
* unanswered = below that threshold (``matched_faq_id`` is NULL).
"""
import pandas as pd

_FREQ = {"Daily": "D", "Weekly": "W", "Monthly": "M"}


def overview(df: pd.DataFrame, faq_count: int) -> dict:
    total = len(df)
    answered = int(df["answered"].sum()) if total else 0
    rated = df["feedback_rating"].dropna()
    helpful = int((rated == "helpful").sum())
    not_helpful = int((rated == "not_helpful").sum())
    votes = helpful + not_helpful
    return {
        "total_questions": total,
        "faq_count": faq_count,
        "answered": answered,
        "unanswered": total - answered,
        "avg_similarity": float(df["similarity_score"].mean()) if total else None,
        "helpful": helpful,
        "not_helpful": not_helpful,
        "satisfaction": (helpful / votes) if votes else None,
        "feedback_votes": votes,
    }


def activity_series(df: pd.DataFrame, period: str = "Daily") -> pd.Series:
    """Number of questions per day/week/month (missing periods filled with 0)."""
    if df.empty:
        return pd.Series(dtype=int)
    freq = _FREQ.get(period, "D")
    periods = df["timestamp"].dt.tz_localize(None).dt.to_period(freq)
    counts = periods.value_counts().sort_index()
    full = pd.period_range(counts.index.min(), counts.index.max(), freq=freq)
    counts = counts.reindex(full, fill_value=0)
    counts.index = counts.index.to_timestamp()
    return counts


def category_distribution(df: pd.DataFrame) -> pd.Series:
    """Answered questions per matched-FAQ category."""
    ans = df[df["answered"] & df["predicted_category"].notna()]
    return ans["predicted_category"].value_counts()


def detected_category_counts(df: pd.DataFrame) -> pd.Series:
    """All questions per detected intent (including low-confidence guesses)."""
    return df["predicted_category"].fillna("Unclassified").value_counts()


def top_faqs(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    ans = df[df["answered"]].copy()
    if ans.empty:
        return pd.DataFrame(columns=["question", "times_matched"])
    ans["question"] = ans["matched_question"].fillna("(deleted FAQ)")
    out = ans.groupby("question").size().sort_values(ascending=False).head(n)
    return out.rename("times_matched").reset_index()


def success_split(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=int)
    n = int(df["answered"].sum())
    return pd.Series({"Answered": n, "Unanswered": len(df) - n})


def feedback_split(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=int)
    r = df["feedback_rating"]
    return pd.Series({
        "Helpful": int((r == "helpful").sum()),
        "Not helpful": int((r == "not_helpful").sum()),
        "No feedback": int(r.isna().sum()),
    })
