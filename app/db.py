"""SQLite access.

Cloud Run's filesystem is instance-local and ephemeral, and the production
service runs at max instances 1. The demo state is disposable and reset by a
job. The write-up says so.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS scholarships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    amount_minor    INTEGER NOT NULL,   -- smallest currency unit, integer only
    currency        TEXT    NOT NULL DEFAULT 'USD',
    gpa_minimum     REAL    NOT NULL,
    country         TEXT    NOT NULL,
    deadline_utc    TEXT    NOT NULL,   -- ISO 8601, always UTC in storage
    created_utc     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scholarship_id  INTEGER NOT NULL REFERENCES scholarships(id),
    applicant_id    TEXT    NOT NULL,
    applicant_name  TEXT    NOT NULL,
    gpa             REAL,
    country         TEXT    NOT NULL,
    created_utc     TEXT    NOT NULL,
    -- One application per applicant per scholarship, enforced here rather
    -- than in application code. A check-then-act in Python is a race.
    UNIQUE (scholarship_id, applicant_id)
);

CREATE INDEX IF NOT EXISTS idx_app_scholarship ON applications(scholarship_id);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_url, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    conn = connect()
    try:
        cur = conn.cursor()
        yield cur
    finally:
        conn.close()


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def reset_db() -> None:
    """Used by the demo reset job and by tests. Destructive."""
    conn = connect()
    try:
        conn.executescript(
            "DROP TABLE IF EXISTS applications; DROP TABLE IF EXISTS scholarships;"
        )
        conn.executescript(SCHEMA)
    finally:
        conn.close()
