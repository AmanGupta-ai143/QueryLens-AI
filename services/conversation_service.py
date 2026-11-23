"""Stores and reads chatbot conversations."""
import pandas as pd

from config import local_tz
from database.db_manager import Database, like_pattern, utc_now_str
from errors import NotFoundError

_SELECT = """
SELECT c.id, c.session_id, c.user_question, c.bot_response, c.matched_faq_id,
       c.similarity_score, c.predicted_category, c.timestamp,
       f.question AS matched_question,
       fb.rating AS feedback_rating, fb.feedback_comment
FROM conversations c
LEFT JOIN faqs f ON f.id = c.matched_faq_id
LEFT JOIN feedback fb ON fb.conversation_id = c.id
"""


class ConversationService:
    def __init__(self, db: Database):
        self.db = db

    def log(self, session_id: str, question: str, response: str, matched_faq_id,
            score: float, predicted_category=None) -> int:
        return self.db.execute(
            "INSERT INTO conversations (session_id, user_question, bot_response, matched_faq_id, "
            "similarity_score, predicted_category, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, question, response, matched_faq_id, round(float(score), 4),
             predicted_category, utc_now_str()),
        ).lastrowid

    def get(self, conversation_id: int) -> dict | None:
        return self.db.query_one(_SELECT + " WHERE c.id = ?", (conversation_id,))

    def list(self, search: str = "", limit: int = 200, status: str = "all") -> list[dict]:
        """status: all | answered | unanswered | helpful | not_helpful | no_feedback"""
        sql, params = _SELECT + " WHERE 1=1", []
        search = (search or "").strip()
        if search:
            pat = like_pattern(search)
            sql += (" AND (c.user_question LIKE ? ESCAPE '\\' OR c.bot_response LIKE ? ESCAPE '\\' "
                    "OR f.question LIKE ? ESCAPE '\\')")
            params += [pat, pat, pat]
        sql += {
            "answered": " AND c.matched_faq_id IS NOT NULL",
            "unanswered": " AND c.matched_faq_id IS NULL",
            "helpful": " AND fb.rating = 'helpful'",
            "not_helpful": " AND fb.rating = 'not_helpful'",
            "no_feedback": " AND fb.id IS NULL",
        }.get(status, "")
        return self.db.query_all(sql + " ORDER BY c.id DESC LIMIT ?", params + [int(limit)])

    def delete(self, conversation_id: int) -> bool:
        return self.db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,)).rowcount > 0

    def delete_all(self) -> int:
        return self.db.execute("DELETE FROM conversations").rowcount

    def count(self) -> int:
        return self.db.query_one("SELECT COUNT(*) AS n FROM conversations")["n"]

    def dataframe(self) -> pd.DataFrame:
        """All conversations as a DataFrame (local-time timestamps) for analytics."""
        rows = self.db.query_all(_SELECT + " ORDER BY c.id")
        cols = ["id", "session_id", "user_question", "bot_response", "matched_faq_id",
                "similarity_score", "predicted_category", "timestamp", "matched_question",
                "feedback_rating", "feedback_comment"]
        df = pd.DataFrame(rows, columns=cols)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(local_tz())
        df["answered"] = df["matched_faq_id"].notna()
        df["similarity_score"] = pd.to_numeric(df["similarity_score"], errors="coerce")
        return df

    def require(self, conversation_id: int) -> dict:
        row = self.get(conversation_id)
        if not row:
            raise NotFoundError(f"Conversation #{conversation_id} does not exist.")
        return row
