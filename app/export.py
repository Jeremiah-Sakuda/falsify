"""CSV export.

Encoding rule: the output is UTF-8 and survives non-ASCII applicant names.
`newline=""` on the writer, explicit utf-8 on the response. A name like
"Nguyễn Thị Hoa" or "Łukasz Żółć" must round-trip.
"""
from __future__ import annotations

import csv
import io

from app.apply import list_applications

COLUMNS = (
    "id",
    "scholarship_id",
    "scholarship_name",
    "applicant_id",
    "applicant_name",
    "gpa",
    "country",
    "created_utc",
)


def applications_csv() -> str:
    # newline="" so csv controls line endings; no \r\n doubling on any platform.
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in list_applications():
        writer.writerow(row)
    return buf.getvalue()


def applications_csv_bytes() -> bytes:
    """Explicit UTF-8 encoding. Never the platform default."""
    return applications_csv().encode("utf-8")
