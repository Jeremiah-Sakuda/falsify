"""Shared fixtures.

Experiments are copied into the MR head checkout and run against this same
conftest, so anything an experiment may rely on must live here. The
experiments job runs pytest in a child process with a scrubbed environment —
there is no network, no credentials, and no reliable wall clock. Tests that
care about time must pass their own instant.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest

# Set before any app module imports, so config.load_settings() sees it.
os.environ.setdefault("FALSIFY_ENV", "dev")

_tmpdir = tempfile.mkdtemp(prefix="falsify-test-")
os.environ["FALSIFY_DB"] = os.path.join(_tmpdir, "test.db")

from app.config import DEV_TOKEN  # noqa: E402
from app.db import reset_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

AUTH = {"Authorization": f"Bearer {DEV_TOKEN}"}

# A fixed instant, so nothing depends on the wall clock.
NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _clean_db() -> Iterator[None]:
    reset_db()
    yield


@pytest.fixture
def client() -> Iterator["TestClient"]:  # noqa: F821
    from fastapi.testclient import TestClient

    with TestClient(fastapi_app) as c:
        yield c


@pytest.fixture
def auth() -> dict[str, str]:
    return dict(AUTH)


@pytest.fixture
def now() -> datetime:
    return NOW


def make_scholarship(
    client,
    *,
    name: str = "Test Scholarship",
    amount_minor: int = 250_000,
    gpa_minimum: float = 2.5,
    country: str = "US",
    deadline: datetime | None = None,
) -> int:
    """Create a scholarship and return its id. Deadline defaults to open."""
    deadline = deadline or (NOW + timedelta(days=30))
    r = client.post(
        "/scholarships",
        json={
            "name": name,
            "amount_minor": amount_minor,
            "currency": "USD",
            "gpa_minimum": gpa_minimum,
            "country": country,
            "deadline_utc": deadline.isoformat(),
        },
        headers=AUTH,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]
