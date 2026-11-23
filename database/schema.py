"""SQLite schema. Timestamps are stored as UTC text: 'YYYY-MM-DD HH:MM:SS'."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS faqs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question    TEXT NOT NULL UNIQUE COLLATE NOCASE,
    answer      TEXT NOT NULL,
    category    TEXT NOT NULL,
    keywords    TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT NOT NULL,
    user_question      TEXT NOT NULL,
    bot_response       TEXT NOT NULL,
    matched_faq_id     INTEGER,            -- NULL = not answered (below threshold)
    similarity_score   REAL NOT NULL DEFAULT 0,
    predicted_category TEXT,               -- detected intent (may be NULL)
    timestamp          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  INTEGER NOT NULL UNIQUE
                     REFERENCES conversations(id) ON DELETE CASCADE,
    rating           TEXT NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
    feedback_comment TEXT,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unanswered_questions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    question            TEXT NOT NULL,
    normalized_question TEXT NOT NULL UNIQUE,   -- cleaned text used to count repeats
    frequency           INTEGER NOT NULL DEFAULT 1,
    status              TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved')),
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_conv_faq ON conversations(matched_faq_id);
"""
