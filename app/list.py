"""Paginated listing.

Two rules experiments will probe:

  1. A total that is an exact multiple of the page size yields exactly
     total/size full pages and drops nothing. Off-by-one here is the classic.
  2. Eligibility expansion is a single joined query, not one query per row.
     N+1 on a listing is a performance defect with a committed threshold in
     .falsify/thresholds.yaml.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.config import settings
from app.db import cursor
from app.eligibility import evaluate


def page_count(total: int, size: int) -> int:
    """Number of pages for `total` records at `size` per page.

    A total that divides evenly must not produce a trailing empty page, and
    must not lose the final full page.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if total <= 0:
        return 0
    return math.ceil(total / size)


def clamp_size(size: int | None) -> int:
    if size is None:
        return settings.default_page_size
    return max(1, min(size, settings.max_page_size))


def list_scholarships(page: int = 1, size: int | None = None) -> dict[str, Any]:
    size = clamp_size(size)
    page = max(1, page)
    offset = (page - 1) * size

    with cursor() as cur:
        total = cur.execute("SELECT COUNT(*) AS n FROM scholarships").fetchone()["n"]
        rows = cur.execute(
            """
            SELECT id, name, amount_minor, currency, gpa_minimum, country, deadline_utc
            FROM scholarships
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (size, offset),
        ).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "page": page,
        "size": size,
        "total": total,
        "pages": page_count(total, size),
    }


def list_with_eligibility(
    *,
    page: int = 1,
    size: int | None = None,
    gpa: float | None = None,
    country: str = "US",
    tz: str | None = None,
    _now: datetime | None = None,
) -> dict[str, Any]:
    """Listing with the eligibility expansion.

    One query for the rows, one for the count. Eligibility is computed in
    process from data already fetched — no per-row query.
    """
    result = list_scholarships(page=page, size=size)

    for item in result["items"]:
        deadline = datetime.fromisoformat(item["deadline_utc"])
        eligible, reasons = evaluate(
            scholarship_id=item["id"],
            gpa=gpa,
            country=country,
            deadline_utc=deadline,
            gpa_minimum=item["gpa_minimum"],
            tz=tz,
            _now=_now,
        )
        item["eligible"] = eligible
        item["reasons"] = reasons

    return result
