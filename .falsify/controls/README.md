# Negative tests — each control, failing closed

Enforcement is the claim, so each security control in `docs/controls.md` has a
test that the pipeline must **refuse**. These are run by the `controls` job in
a dedicated pipeline, not as part of a normal MR.

| File | Control | Expected outcome |
| --- | --- | --- |
| `probe_job_token.py` | 1 — no credentials in the experiment child process | `CI_JOB_TOKEN` absent; probe reports it missing |
| `probe_network.py` | 1 — no outbound network | Connection refused / no route |
| `scratch_scope_violation.sh` | 2 — scratch confined to `.falsify/` | `experiments` job fails with a branch-scope violation before any test runs |
| `stale_gate2.sh` | 3 — authorization bound to head + claims version | `certificate` job fails with a stale-authorization error |
| `missing_promotion.sh` | 4 — promotion enforced at the merge gate | `certificate` job fails with a missing-promotion error |

The probes in this directory are **not** experiments and are never promoted
into `tests/`. The `experiments` job skips this directory.
