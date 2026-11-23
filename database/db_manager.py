"""Thin, safe wrapper around sqlite3.

* A fresh connection per operation (safe with Streamlit's threads).
* Parameterised queries only - never string-formatted SQL with user input.
* Any sqlite3 error becomes a ``DatabaseError`` with a readable message.
"""
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config import DB_PATH
from database.schema import SCHEMA
from errors import DatabaseError


def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class ExecResult:
    lastrowid: int
    rowcount: int


class Database:
    def __init__(self, path=DB_PATH):
        self.path = str(path)
        try:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DatabaseError(f"Cannot create the database folder: {exc}") from exc
        self.init()

    @contextmanager
    def connect(self):
        try:
            conn = sqlite3.connect(self.path, timeout=10)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Cannot open the database: {exc}") from exc
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(f"Database error: {exc}") from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def execute(self, sql: str, params=()) -> ExecResult:
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            return ExecResult(cur.lastrowid, cur.rowcount)

    def query_all(self, sql: str, params=()) -> list[dict]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def query_one(self, sql: str, params=()) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None


def like_pattern(text: str) -> str:
    """Escape LIKE wildcards in user search text (use with ESCAPE '\\')."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
