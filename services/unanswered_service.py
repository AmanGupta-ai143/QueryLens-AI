"""Questions the chatbot could not answer confidently."""
from database.db_manager import Database, like_pattern, utc_now_str
from errors import NotFoundError, ValidationError
from nlp.preprocessing import clean_text, validate_question


class UnansweredService:
    def __init__(self, db: Database):
        self.db = db

    def record(self, question: str) -> int:
        """Store a question; repeated (normalised) questions increase the frequency."""
        question = validate_question(question)
        key = clean_text(question)
        existing = self.db.query_one(
            "SELECT id FROM unanswered_questions WHERE normalized_question = ?", (key,))
        if existing:
            # Asked again -> count it and re-open it if it had been resolved.
            self.db.execute(
                "UPDATE unanswered_questions SET frequency = frequency + 1, status = 'open' WHERE id = ?",
                (existing["id"],))
            return existing["id"]
        return self.db.execute(
            "INSERT INTO unanswered_questions (question, normalized_question, frequency, status, created_at) "
            "VALUES (?, ?, 1, 'open', ?)", (question, key, utc_now_str()),
        ).lastrowid

    def get(self, uid: int) -> dict | None:
        return self.db.query_one("SELECT * FROM unanswered_questions WHERE id = ?", (uid,))

    def list(self, status: str = "all", search: str = "") -> list[dict]:
        sql, params = "SELECT * FROM unanswered_questions WHERE 1=1", []
        if status in ("open", "resolved"):
            sql += " AND status = ?"
            params.append(status)
        if (search or "").strip():
            sql += " AND question LIKE ? ESCAPE '\\'"
            params.append(like_pattern(search.strip()))
        return self.db.query_all(sql + " ORDER BY frequency DESC, id DESC", params)

    def set_status(self, uid: int, status: str) -> None:
        if status not in ("open", "resolved"):
            raise ValidationError("Status must be 'open' or 'resolved'.")
        if self.db.execute("UPDATE unanswered_questions SET status = ? WHERE id = ?", (status, uid)).rowcount == 0:
            raise NotFoundError("That unanswered question no longer exists.")

    def mark_resolved(self, uid: int) -> None:
        self.set_status(uid, "resolved")

    def delete(self, uid: int) -> bool:
        return self.db.execute("DELETE FROM unanswered_questions WHERE id = ?", (uid,)).rowcount > 0

    def counts(self) -> dict:
        row = self.db.query_one(
            "SELECT COALESCE(SUM(status='open'),0) AS open, COALESCE(SUM(status='resolved'),0) AS resolved, "
            "COALESCE(SUM(frequency),0) AS total_asks, COUNT(*) AS distinct_questions FROM unanswered_questions")
        return row
