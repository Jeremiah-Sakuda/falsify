"""The base suite. Deliberately thin.

Falsify is not a replacement for the base test suite, and the base suite is
deliberately not exhaustive — the point of the project is that experiments
find what this does not cover, and that accepted findings get promoted in
here permanently.

Promoted regression tests land in this directory with a `promoted` marker and
the experiment id in the docstring.
"""
from __future__ import annotations

from datetime import timedelta

from tests.conftest import make_scholarship


def test_landing_page_states_the_one_rule(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "No red test, no accusation" in r.text


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_create_and_read_a_scholarship(client):
    sid = make_scholarship(client, name="Deadline Filter Grant")
    page = client.get("/scholarships").json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == sid
    assert page["items"][0]["name"] == "Deadline Filter Grant"


def test_write_endpoints_require_a_token(client):
    r = client.post("/scholarships", json={})
    assert r.status_code == 401


def test_amount_is_an_integer_in_the_smallest_unit(client):
    sid = make_scholarship(client, amount_minor=250_000)
    item = client.get("/scholarships").json()["items"][0]
    assert item["id"] == sid
    assert isinstance(item["amount_minor"], int)
    assert item["amount_minor"] == 250_000


def test_application_round_trips(client, auth):
    sid = make_scholarship(client)
    r = client.post(
        "/applications",
        json={
            "scholarship_id": sid,
            "applicant_id": "a-1",
            "applicant_name": "Ada Lovelace",
            "gpa": 3.6,
            "country": "US",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["applicant_id"] == "a-1"


def test_duplicate_application_is_a_conflict(client, auth):
    sid = make_scholarship(client)
    body = {
        "scholarship_id": sid,
        "applicant_id": "a-1",
        "applicant_name": "Ada Lovelace",
        "gpa": 3.6,
        "country": "US",
    }
    assert client.post("/applications", json=body, headers=auth).status_code == 201
    assert client.post("/applications", json=body, headers=auth).status_code == 409


def test_eligibility_responds(client, now):
    sid = make_scholarship(
        client, gpa_minimum=2.5, deadline=now + timedelta(days=10)
    )
    r = client.get(f"/scholarships/{sid}/eligible?gpa=3.0&country=US&tz=UTC")
    assert r.status_code == 200
    assert r.json()["scholarship_id"] == sid


def test_csv_export_has_a_header(client, auth):
    r = client.get("/export.csv", headers=auth)
    assert r.status_code == 200
    assert r.text.splitlines()[0].startswith("id,scholarship_id")
