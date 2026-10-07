# Falsifier — write phase

The human authorized specific conjectures by id. Write one pytest file per
authorized id. Write nothing for a struck id.

## Where

`.falsify/experiments/<id>_test.py` on `falsify/mr-<iid>`.

One file per experiment. The filename is the record — the certificate
identifies experiments by content digest, so the file must be byte-stable:
no timestamps, no random seeds without pinning, no absolute paths.

## What a good experiment file looks like

```python
"""X2: pagination drops the last record when total % size == 0.

Targets C1 / app/list.py:18.
FAILS on head if the off-by-one is present. PASSES on base.
"""
from fastapi.testclient import TestClient
from app.main import app


def test_full_final_page_is_not_dropped():
    client = TestClient(app)
    # 10 records, page size 5 -> exactly two full pages, nothing dropped.
    for i in range(10):
        client.post("/scholarships", json={...}, headers=AUTH)

    seen = []
    for page in (1, 2):
        r = client.get(f"/scholarships?page={page}&size=5")
        seen.extend(item["id"] for item in r.json()["items"])

    assert len(seen) == 10, f"expected 10 records across 2 full pages, got {len(seen)}"
```

## Hard requirements

- **Assert, do not error.** An import error, a fixture error, a timeout, or a
  collection error is recorded as `ERROR` and is **not a finding of any
  kind**. You get exactly one rewrite per error, then the experiment is
  discarded. Import only what exists; check the diff.
- **Deterministic.** The same file must produce the same result on two
  consecutive runs on the same head. A flaky experiment is worse than none.
- **Runs on the base too.** The harness runs your file against the merge base.
  If the file cannot import on the base because it targets new code, that is
  fine and is recorded as `n/a` — but say so in the docstring.
- **Self-contained.** No network, no credentials, no environment variables
  beyond what `conftest.py` provides. The job runs with a scrubbed
  environment and no job token.
- **Under 30 seconds.** Per-test timeout is enforced.
- **A message on every assert.** The failure text is what a human reads at
  Gate 3. `assert x == y` with no message is a bad experiment.

## The docstring is part of the evidence

First line: the experiment id and the conjecture in one sentence.
Then: what it targets, and what the expected head/base behavior is.
This text appears in the certificate. Write it for the human who will rule.
