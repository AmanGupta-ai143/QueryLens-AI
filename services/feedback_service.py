"""Helpful / Not-helpful feedback. Feedback never edits FAQ answers automatically."""
from config import MAX_COMMENT_LENGTH
from database.db_manager import Database, utc_now_str
from errors import NotFoundError, ValidationError

RATINGS = ("helpful", "not_helpful")


class FeedbackService:
    def __init__(self, db: Database):
        self.db = db

    def submit(self, conversation_id: int, rating: str, comment: str = "") -> None:
        if rating not in RATINGS:
            raise ValidationError("Rating must be 'helpful' or 'not_helpful'.")
        comment = " ".join((comment or "").split())
        if len(comment) > MAX_COMMENT_LENGTH:
            raise ValidationError(f"Comments must be under {MAX_COMMENT_LENGTH} characters.")
        if not self.db.query_one("SELECT id FROM conversations WHERE id = ?", (conversation_id,)):
            raise NotFoundError("That conversation no longer exists.")
        # One rating per conversation; submitting again replaces the earlier one.
        self.db.execute(
            "INSERT INTO feedback (conversation_id, rating, feedback_comment, created_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(conversation_id) DO UPDATE SET "
            "rating = excluded.rating, feedback_comment = excluded.feedback_comment, "
            "created_at = excluded.created_at",
            (conversation_id, rating, comment or None, utc_now_str()),
        )

    def get(self, conversation_id: int) -> dict | None:
        return self.db.query_one("SELECT * FROM feedback WHERE conversation_id = ?", (conversation_id,))

    def summary(self) -> dict:
        row = self.db.query_one(
            "SELECT "
            "(SELECT COUNT(*) FROM feedback WHERE rating='helpful') AS helpful, "
            "(SELECT COUNT(*) FROM feedback WHERE rating='not_helpful') AS not_helpful, "
            "(SELECT COUNT(*) FROM conversations) AS total"
        )
        row["no_feedback"] = row["total"] - row["helpful"] - row["not_helpful"]
        return row

    def faqs_needing_review(self) -> list[dict]:
        """FAQs that received 'not helpful' votes (for a human to review)."""
        return self.db.query_all(
            "SELECT f.id AS faq_id, f.question, f.category, "
            "SUM(CASE WHEN fb.rating='helpful' THEN 1 ELSE 0 END) AS helpful, "
            "SUM(CASE WHEN fb.rating='not_helpful' THEN 1 ELSE 0 END) AS not_helpful, "
            "COUNT(fb.id) AS votes "
            "FROM conversations c "
            "JOIN feedback fb ON fb.conversation_id = c.id "
            "JOIN faqs f ON f.id = c.matched_faq_id "
            "GROUP BY f.id HAVING not_helpful > 0 "
            "ORDER BY (not_helpful * 1.0 / votes) DESC, not_helpful DESC"
        )

    def recent_comments(self, limit: int = 20) -> list[dict]:
        return self.db.query_all(
            "SELECT fb.rating, fb.feedback_comment, fb.created_at, c.user_question "
            "FROM feedback fb JOIN conversations c ON c.id = fb.conversation_id "
            "WHERE fb.feedback_comment IS NOT NULL AND fb.feedback_comment != '' "
            "ORDER BY fb.id DESC LIMIT ?", (int(limit),)
        )
