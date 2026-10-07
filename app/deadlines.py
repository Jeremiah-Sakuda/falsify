"""Deadline comparison, in the applicant's time zone.

Two rules that experiments will probe:

  1. The comparison happens in the APPLICANT's zone, not the server's. A
     server in UTC and an applicant in Pacific/Auckland disagree about what
     day it is for most of the day.
  2. A deadline at exactly the current instant is OPEN, not passed. The
     boundary is `>`, not `>=` — you get until the deadline, inclusive.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_zone(tz: str | None) -> ZoneInfo:
    """Resolve an IANA zone name, defaulting to UTC.

    An unknown zone is an error the caller should surface, not a silent
    fallback to server time — a silent fallback is defect D-class behavior.
    """
    if not tz:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown time zone: {tz!r}") from exc


def now_in(tz: str | None, *, _now: datetime | None = None) -> datetime:
    """Current instant expressed in the applicant's zone.

    `_now` is injectable so experiments can control the clock. The experiments
    job has no reliable wall clock to depend on, so any test about deadlines
    must pass its own instant.
    """
    instant = _now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(resolve_zone(tz))


def is_open(
    deadline_utc: datetime,
    tz: str | None = None,
    *,
    _now: datetime | None = None,
) -> bool:
    """True while the deadline has not passed in the applicant's zone.

    A deadline exactly equal to the current instant is OPEN.
    """
    if deadline_utc.tzinfo is None:
        deadline_utc = deadline_utc.replace(tzinfo=timezone.utc)

    zone = resolve_zone(tz)
    deadline_local = deadline_utc.astimezone(zone)
    current_local = now_in(tz, _now=_now)

    # Inclusive of the deadline instant itself.
    return current_local <= deadline_local
