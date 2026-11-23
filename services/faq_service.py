"""FAQ knowledge-base CRUD, search, seeding and safe CSV import."""
import csv
import io
import json
from pathlib import Path

from config import (CATEGORIES, MAX_FAQ_ANSWER_LENGTH, MAX_FAQ_QUESTION_LENGTH,
                    MAX_IMPORT_BYTES, MAX_IMPORT_ROWS)
from database.db_manager import Database, like_pattern, utc_now_str
from errors import NotFoundError, ValidationError


def normalize_keywords(keywords) -> str:
    """'Fee, FEE ,fees' -> 'fee, fees' (lower-case, de-duplicated, comma separated)."""
    if isinstance(keywords, (list, tuple)):
        keywords = ",".join(keywords)
    seen, out = set(), []
    for k in str(keywords or "").split(","):
        k = " ".join(k.split()).lower()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return ", ".join(out)


class FAQService:
    def __init__(self, db: Database):
        self.db = db

    # -------------------------------------------------------------- validation
    def _validate(self, question, answer, category, keywords, faq_id=None) -> tuple:
        question = " ".join(str(question or "").split())
        answer = str(answer or "").strip()
        category = str(category or "").strip()
        if len(question) < 5:
            raise ValidationError("The question must be at least 5 characters long.")
        if len(question) > MAX_FAQ_QUESTION_LENGTH:
            raise ValidationError(f"The question must be under {MAX_FAQ_QUESTION_LENGTH} characters.")
        if len(answer) < 5:
            raise ValidationError("The answer must be at least 5 characters long.")
        if len(answer) > MAX_FAQ_ANSWER_LENGTH:
            raise ValidationError(f"The answer must be under {MAX_FAQ_ANSWER_LENGTH} characters.")
        if category not in CATEGORIES:
            raise ValidationError(f"Category must be one of: {', '.join(CATEGORIES)}.")
        dup = self.db.query_one(
            "SELECT id FROM faqs WHERE lower(question) = lower(?) AND id != ?",
            (question, faq_id or -1),
        )
        if dup:
            raise ValidationError("An FAQ with this question already exists.")
        return question, answer, category, normalize_keywords(keywords)

    # -------------------------------------------------------------------- CRUD
    def add(self, question, answer, category, keywords="") -> int:
        question, answer, category, keywords = self._validate(question, answer, category, keywords)
        now = utc_now_str()
        return self.db.execute(
            "INSERT INTO faqs (question, answer, category, keywords, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (question, answer, category, keywords, now, now),
        ).lastrowid

    def update(self, faq_id: int, question, answer, category, keywords="") -> None:
        if not self.get(faq_id):
            raise NotFoundError(f"FAQ #{faq_id} does not exist.")
        question, answer, category, keywords = self._validate(question, answer, category, keywords, faq_id)
        self.db.execute(
            "UPDATE faqs SET question=?, answer=?, category=?, keywords=?, updated_at=? WHERE id=?",
            (question, answer, category, keywords, utc_now_str(), faq_id),
        )

    def delete(self, faq_id: int) -> bool:
        return self.db.execute("DELETE FROM faqs WHERE id = ?", (faq_id,)).rowcount > 0

    def get(self, faq_id: int) -> dict | None:
        return self.db.query_one("SELECT * FROM faqs WHERE id = ?", (faq_id,))

    def list(self, search: str = "", category: str | None = None) -> list[dict]:
        sql, params = "SELECT * FROM faqs WHERE 1=1", []
        search = (search or "").strip()
        if search:
            pat = like_pattern(search)
            sql += (" AND (question LIKE ? ESCAPE '\\' OR answer LIKE ? ESCAPE '\\' "
                    "OR keywords LIKE ? ESCAPE '\\')")
            params += [pat, pat, pat]
        if category and category != "All":
            sql += " AND category = ?"
            params.append(category)
        return self.db.query_all(sql + " ORDER BY id", params)

    def count(self) -> int:
        return self.db.query_one("SELECT COUNT(*) AS n FROM faqs")["n"]

    def category_counts(self) -> dict:
        rows = self.db.query_all("SELECT category, COUNT(*) AS n FROM faqs GROUP BY category ORDER BY n DESC")
        return {r["category"]: r["n"] for r in rows}

    # ----------------------------------------------------------------- seeding
    def seed_from_json(self, path) -> int:
        """Load the sample dataset, but only into an empty knowledge base."""
        path = Path(path)
        if self.count() > 0 or not path.exists():
            return 0
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Could not read the sample FAQ file: {exc}") from exc
        added = 0
        for row in rows:
            try:
                self.add(row["question"], row["answer"], row["category"], row.get("keywords", ""))
                added += 1
            except (ValidationError, KeyError):
                continue
        return added

    # -------------------------------------------------------------- CSV import
    def import_csv(self, data: bytes, filename: str = "upload.csv") -> dict:
        """Safely import FAQs from a CSV (columns: question, answer, category[, keywords])."""
        if not str(filename).lower().endswith(".csv"):
            raise ValidationError("Only .csv files can be imported.")
        if len(data) > MAX_IMPORT_BYTES:
            raise ValidationError(f"The file is too large (limit {MAX_IMPORT_BYTES // 1000} KB).")
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValidationError("The file must be UTF-8 encoded text.")
        reader = csv.DictReader(io.StringIO(text))
        headers = {h.strip().lower() for h in (reader.fieldnames or [])}
        if not {"question", "answer", "category"} <= headers:
            raise ValidationError("The CSV needs the columns: question, answer, category (keywords optional).")

        report = {"added": 0, "skipped": 0, "errors": []}
        for n, raw in enumerate(reader, start=2):
            if n - 1 > MAX_IMPORT_ROWS:
                report["errors"].append(f"Stopped after {MAX_IMPORT_ROWS} rows (import limit).")
                break
            row = {(k or "").strip().lower(): (v or "") for k, v in raw.items()}
            try:
                self.add(row.get("question"), row.get("answer"), row.get("category", "").strip(),
                         row.get("keywords", ""))
                report["added"] += 1
            except ValidationError as exc:
                report["skipped"] += 1
                report["errors"].append(f"Row {n}: {exc}")
        return report
