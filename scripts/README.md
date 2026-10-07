# scripts/

Nothing here calls a model.

The certificate, the ledger, the ruling parser, and the experiments harness
are the parts of Falsify that must not be a judgment call. They read
structured state — pipeline artifacts, the GitLab API, file hashes — and they
fail closed.

| Script | Run by | What it does |
| --- | --- | --- |
| `run_experiments.py` | `experiments` job | Runs each experiment twice on head, once on base, inside the execution boundary. Writes `experiments.json` |
| `experiments_contract.py` | imported | The single place a result is classified. Keeps the harness, certificate, and ledger from drifting |
| `rulings.py` | imported | Strict parser for the `falsify:` syntax. A near-miss raises rather than silently not authorizing |
| `check_scratch_scope.sh` | `experiments` job | Control 2, layer 3: refuses any scratch branch touching a file outside `.falsify/` |
| `certificate.py` | `certificate` job | The merge gate. Blocks on an unresolved finding, a missing promotion, or a stale Gate 2 |
| `promote.sh` | `promote` job, **manual** | Human-run. Copies an experiment byte-for-byte into `tests/` and records its hash |
| `ledger.py` | `ledger-commit`, `deploy-*`, `prod-watch`, `rollback` on `main` | Writes the immutable certificate and appends events. Regenerates `LEDGER.md` |
| `seed.py` | demo reset job | Seeds the demo database. Non-ASCII applicant names on purpose |

## Status

| Script | State |
| --- | --- |
| `experiments_contract.py` | Implemented, covered by `tests/test_contract.py` |
| `rulings.py` | Implemented, covered by `tests/test_contract.py` |
| `run_experiments.py` | Implemented |
| `check_scratch_scope.sh` | Implemented |
| `ledger.py` | Implemented |
| `seed.py` | Implemented |
| `promote.sh` | Implemented |
| `certificate.py` | Resolution rules and every failure mode implemented; the GitLab API fetching is passed in as `--state` JSON and comes from `gitlab_state.py` |
| `gitlab_state.py` | **Stub** — build block 4 |
| `certificate_verify.py` | **Stub** — build block 4 |
| `live_experiments.py` | **Stub** — build block 6 |
| `prod_watch.py` | **Stub** — build block 6 |

Each stub exits **2** rather than silently succeeding. A govern or monitor job
that cannot do its work must fail the pipeline, not pass it — a certificate
job that passed because its inputs were missing would be exactly the
unsupported assertion this project exists to prevent.
