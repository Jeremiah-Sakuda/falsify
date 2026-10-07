"""Applications.

One application per applicant per scholarship. The constraint lives in the
schema (UNIQUE on (scholarship_id, applicant_id)), not in a check-then-act in
Python — a SELECT-then-INSERT is a race, and two concurrent requests will both
pass the SELECT.

The concurrency defect is tested within one instance, and the write-up says
so: Cloud Run production runs at max instances 1 for the demo.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.db import cursor


class DuplicateApplication(Exception):
    """The applicant already has an application for this scholarship."""


class UnknownScholarship(Exception):
    """No scholarship with that id."""


def create_application(
    *,
    scholarship_id: int,
    applicant_id: str,
    applicant_name: str,
    gpa: float | None,
    country: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()

    with cursor() as cur:
        exists = cur.execute(
            "SELECT 1 FROM scholarships WHERE id = ?", (scholarship_id,)
        ).fetchone()
        if not exists:
            raise UnknownScholarship(f"no scholarship with id {scholarship_id}")

        try:
            cur.execute(
                """
                INSERT INTO applications
                    (scholarship_id, applicant_id, applicant_name, gpa, country, created_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (scholarship_id, applicant_id, applicant_name, gpa, country, now),
            )
        except sqlite3.IntegrityError as exc:
            # The constraint did the work. Do not retry, do not upsert.
            raise DuplicateApplication(
                f"applicant {applicant_id!r} already applied to scholarship "
                f"{scholarship_id}"
            ) from exc

        row = cur.execute(
            """
            SELECT id, scholarship_id, applicant_id, applicant_name, gpa, country
            FROM applications WHERE id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()

    return dict(row)


def list_applications() -> list[dict[str, Any]]:
    with cursor() as cur:
        rows = cur.execute(
            """
            SELECT a.id, a.scholarship_id, s.name AS scholarship_name,
                   a.applicant_id, a.applicant_name, a.gpa, a.country, a.created_utc
            FROM applications a
            JOIN scholarships s ON s.id = a.scholarship_id
            ORDER BY a.id
            """
        ).fetchall()
    return [dict(r) for r in rows]
