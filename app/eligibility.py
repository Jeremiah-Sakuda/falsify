"""Eligibility rules.

Three conditions, all of which must hold:

  1. GPA meets the scholarship minimum. A NULL gpa is permitted by the spec
     (not yet reported). A NEGATIVE gpa is not — it is invalid input, and
     these are different requirements. An experiment that conflates them is
     testing the wrong spec, which is what the contest path at Gate 3 exists
     for.
  2. The applicant's country is in the allowlist. The comparison is
     case-insensitive: "ke" and "KE" are the same country.
  3. The deadline has not passed in the applicant's time zone.
"""
from __future__ import annotations

from datetime import datetime

from app.config import settings
from app.deadlines import is_open


class InvalidGpa(ValueError):
    """A GPA outside [0.0, 4.0]. Distinct from an absent GPA."""


def normalize_country(country: str) -> str:
    return country.strip().casefold()


def country_allowed(country: str) -> bool:
    allowed = {normalize_country(c) for c in settings.country_allowlist}
    return normalize_country(country) in allowed


def gpa_meets(gpa: float | None, minimum: float) -> bool:
    """Whether a GPA clears the minimum.

    An absent GPA (None) is permitted by the spec and is not yet reported, so
    it does not clear a positive minimum. A negative GPA is invalid input and
    raises — it is not an eligibility answer.
    """
    if gpa is None:
        return minimum <= 0.0
    if gpa < 0.0 or gpa > 4.0:
        raise InvalidGpa(f"gpa must be within [0.0, 4.0]; got {gpa!r}")
    return gpa >= minimum


def evaluate(
    *,
    scholarship_id: int,
    gpa: float | None,
    country: str,
    deadline_utc: datetime,
    gpa_minimum: float | None = None,
    tz: str | None = None,
    _now: datetime | None = None,
) -> tuple[bool, list[str]]:
    """Return (eligible, reasons). `reasons` lists every failed condition."""
    minimum = settings.gpa_minimum if gpa_minimum is None else gpa_minimum
    reasons: list[str] = []

    if not gpa_meets(gpa, minimum):
        reasons.append(
            f"gpa {gpa!r} does not meet the minimum of {minimum}"
            if gpa is not None
            else f"no gpa on file; minimum is {minimum}"
        )

    if not country_allowed(country):
        reasons.append(f"country {country!r} is not in the allowlist")

    if not is_open(deadline_utc, tz, _now=_now):
        reasons.append(f"deadline passed in time zone {tz or 'UTC'!r}")

    return (not reasons), reasons
