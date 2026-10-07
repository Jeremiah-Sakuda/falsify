"""FastAPI entrypoint.

The landing page at / is deliberate: a judge who clicks the submitted Cloud
Run URL sees the one rule, a link to the ledger, and the API docs.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response

from app import __version__
from app.apply import (
    DuplicateApplication,
    UnknownScholarship,
    create_application,
)
from app.auth import require_token
from app.db import cursor, init_db
from app.eligibility import InvalidGpa, evaluate
from app.export import applications_csv_bytes
from app.list import list_scholarships, list_with_eligibility
from app.models import (
    Application,
    ApplicationIn,
    Eligibility,
    Page,
    ScholarshipIn,
)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Falsify demo API",
    description=(
        "Scholarship eligibility and deadlines. Scenery for Falsify — an AI "
        "code reviewer that cannot call something a defect unless it produces "
        "a reproducible failing test."
    ),
    version=__version__,
)

REPO_URL = "https://github.com/Jeremiah-Sakuda/falsify"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing() -> str:
    return f"""<!doctype html>
<meta charset="utf-8">
<title>Falsify</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 16px/1.6 system-ui, sans-serif; max-width: 42rem;
          margin: 4rem auto; padding: 0 1.5rem; }}
  .rule {{ font-size: 1.6rem; font-weight: 650; margin: 0 0 .25rem; }}
  .sub {{ opacity: .7; margin: 0 0 2rem; }}
  ol {{ padding-left: 1.2rem; }}
  code {{ background: rgba(127,127,127,.18); padding: .1em .35em;
          border-radius: 3px; }}
  footer {{ margin-top: 2.5rem; font-size: .9rem; opacity: .7; }}
</style>
<p class="rule">No red test, no accusation.</p>
<p class="sub">Falsify · v{__version__} · the demo API behind the hackathon entry</p>

<p>Falsify may only make a functional defect claim through a reproducible
failing experiment:</p>
<ol>
  <li><strong>FAIL</strong> on the merge request head — an assertion failed,
      not an import error</li>
  <li>The same FAIL <strong>reproduces on a second run</strong></li>
  <li><strong>PASS</strong> on the merge base</li>
</ol>

<p>Everything else it says is explicitly not a defect claim. It does not claim
false positives are impossible — you can reject its reading of the spec, and
the strike count is published.</p>

<p><a href="/docs">API docs</a> ·
   <a href="{REPO_URL}/blob/main/LEDGER.md">the ledger</a> ·
   <a href="{REPO_URL}">source</a></p>

<footer>Path A · Assisted tier · GitLab Duo Agent Platform · Google Cloud Run</footer>
"""


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post(
    "/scholarships",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_token)],
)
def create_scholarship(payload: ScholarshipIn) -> dict[str, int]:
    now = datetime.now(timezone.utc).isoformat()
    with cursor() as cur:
        cur.execute(
            """
            INSERT INTO scholarships
                (name, amount_minor, currency, gpa_minimum, country,
                 deadline_utc, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.amount_minor,
                payload.currency,
                payload.gpa_minimum,
                payload.country,
                payload.deadline_utc.isoformat(),
                now,
            ),
        )
        return {"id": int(cur.lastrowid or 0)}


@app.get("/scholarships", response_model=Page)
def get_scholarships(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page:
    return Page(**list_scholarships(page=page, size=size))


@app.get("/scholarships/eligible")
def get_scholarships_with_eligibility(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    gpa: float | None = Query(default=None),
    country: str = Query(default="US", min_length=2, max_length=2),
    tz: str | None = Query(default=None),
) -> dict:
    try:
        return list_with_eligibility(
            page=page, size=size, gpa=gpa, country=country, tz=tz
        )
    except (InvalidGpa, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@app.get("/scholarships/{scholarship_id}/eligible", response_model=Eligibility)
def get_eligibility(
    scholarship_id: int,
    gpa: float | None = Query(default=None),
    country: str = Query(default="US", min_length=2, max_length=2),
    tz: str | None = Query(default=None),
) -> Eligibility:
    with cursor() as cur:
        row = cur.execute(
            "SELECT id, gpa_minimum, deadline_utc FROM scholarships WHERE id = ?",
            (scholarship_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such scholarship")

    try:
        eligible, reasons = evaluate(
            scholarship_id=scholarship_id,
            gpa=gpa,
            country=country,
            deadline_utc=datetime.fromisoformat(row["deadline_utc"]),
            gpa_minimum=row["gpa_minimum"],
            tz=tz,
        )
    except (InvalidGpa, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return Eligibility(
        scholarship_id=scholarship_id, eligible=eligible, reasons=reasons
    )


@app.post(
    "/applications",
    status_code=status.HTTP_201_CREATED,
    response_model=Application,
    dependencies=[Depends(require_token)],
)
def post_application(payload: ApplicationIn) -> Application:
    try:
        return Application(
            **create_application(
                scholarship_id=payload.scholarship_id,
                applicant_id=payload.applicant_id,
                applicant_name=payload.applicant_name,
                gpa=payload.gpa,
                country=payload.country,
            )
        )
    except UnknownScholarship as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except DuplicateApplication as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@app.get("/export.csv", dependencies=[Depends(require_token)])
def export_csv() -> Response:
    return Response(
        content=applications_csv_bytes(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="applications.csv"'},
    )
