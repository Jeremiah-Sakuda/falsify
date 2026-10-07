#!/usr/bin/env python3
"""Seed the demo database. Also the reset used by the demo reset job.

Cloud Run's filesystem is instance-local and ephemeral, so production state is
disposable by design and this script is how it comes back.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db import cursor, reset_db

NOW = datetime.now(timezone.utc)

SCHOLARSHIPS = [
    # name, amount_minor, gpa_minimum, country, deadline offset (days)
    ("Transcend Engineering Grant", 500_000, 3.0, "US", 45),
    ("Nairobi STEM Fellowship", 250_000, 2.5, "KE", 30),
    ("Mumbai Open Source Award", 150_000, 2.75, "IN", 14),
    ("Lagos Builders Bursary", 300_000, 2.5, "NG", 60),
    ("São Paulo Data Prize", 200_000, 3.25, "BR", 7),
    ("Manila Civic Tech Stipend", 100_000, 2.0, "PH", 1),
    ("Midnight Boundary Scholarship", 125_000, 2.5, "US", 0),
]

APPLICANTS = [
    # applicant_id, name (deliberately non-ASCII), gpa, country
    ("app-001", "Ada Lovelace", 3.9, "US"),
    ("app-002", "Nguyễn Thị Hoa", 3.4, "PH"),
    ("app-003", "Łukasz Żółć", 2.8, "US"),
    ("app-004", "Wanjirũ Kamau", 3.1, "KE"),
    ("app-005", "José Müller-Ríos", None, "BR"),
]


def main() -> None:
    reset_db()
    with cursor() as cur:
        for name, amount, gpa_min, country, days in SCHOLARSHIPS:
            deadline = (NOW + timedelta(days=days)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cur.execute(
                """
                INSERT INTO scholarships
                    (name, amount_minor, currency, gpa_minimum, country,
                     deadline_utc, created_utc)
                VALUES (?, ?, 'USD', ?, ?, ?, ?)
                """,
                (name, amount, gpa_min, country, deadline.isoformat(),
                 NOW.isoformat()),
            )

        for aid, aname, gpa, country in APPLICANTS:
            cur.execute(
                """
                INSERT INTO applications
                    (scholarship_id, applicant_id, applicant_name, gpa,
                     country, created_utc)
                VALUES (1, ?, ?, ?, ?, ?)
                """,
                (aid, aname, gpa, country, NOW.isoformat()),
            )

    print(f"seeded {len(SCHOLARSHIPS)} scholarships, {len(APPLICANTS)} applications")
    print("non-ASCII applicant names included on purpose — CSV export must survive them")


if __name__ == "__main__":
    main()
