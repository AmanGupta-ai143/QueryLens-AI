"""Central configuration for QueryLens AI.

Every value can be overridden with an environment variable, so nothing is
hard-coded to a local machine and no secrets live in the source code.
"""
import os
from datetime import timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
SAMPLE_FAQ_PATH = DATA_DIR / "sample_faqs.json"

# SQLite file location (override with QUERYLENS_DB_PATH for another location).
DB_PATH = Path(os.getenv("QUERYLENS_DB_PATH", str(DATA_DIR / "querylens.db")))

APP_NAME = "QueryLens AI"
APP_TAGLINE = "Smart Question Answering Assistant"

# ---- NLP settings ---------------------------------------------------------
DEFAULT_THRESHOLD = float(os.getenv("QUERYLENS_THRESHOLD", "0.35"))
WORD_WEIGHT = 0.6   # weight of the word-level TF-IDF cosine score
CHAR_WEIGHT = 0.4   # weight of the character n-gram TF-IDF cosine score
TOP_K = 3           # candidates kept for explainability

# ---- Validation limits ----------------------------------------------------
MAX_QUESTION_LENGTH = 500
MAX_FAQ_QUESTION_LENGTH = 300
MAX_FAQ_ANSWER_LENGTH = 2000
MAX_COMMENT_LENGTH = 500
MAX_IMPORT_BYTES = 1_000_000
MAX_IMPORT_ROWS = 500

CATEGORIES = [
    "Admissions", "Courses", "Fees", "Examinations", "Attendance",
    "Scholarships", "Placements", "Hostel", "Library", "Technical Support",
]

CATEGORY_ICONS = {
    "Admissions": "🎓", "Courses": "📘", "Fees": "💳", "Examinations": "📝", "Attendance": "🗓️",
    "Scholarships": "🏅", "Placements": "💼", "Hostel": "🏠", "Library": "📚", "Technical Support": "🛠️",
}

TIMEZONE = os.getenv("QUERYLENS_TIMEZONE", "Asia/Kolkata")


def local_tz():
    """Timezone used for *displaying* timestamps (storage is always UTC)."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(TIMEZONE)
    except Exception:  # tzdata missing or bad name -> fall back to UTC
        return timezone.utc
