# .falsify/

Everything the agents are prompted with and bounded by. Frozen at the Oct 22
tag along with the model and configuration.

| Path | What it is |
| --- | --- |
| `thresholds.yaml` | Committed numbers: timeouts, rate limits, watch thresholds |
| `prompts/` | The Falsifier, Advocate, Planner, and Monitor prompts |
| `templates/` | Comment and incident templates, so output shape is not left to the model |
| `experiments/` | Where the Falsifier writes, on the scratch branch only |
| `controls/` | Negative tests that prove each security control fails closed |

## The scratch branch rule

`.falsify/experiments/` is written **only** on `falsify/mr-<iid>`, never on an
MR branch and never on `main`. The `experiments` job refuses any scratch
branch whose diff touches a file outside `.falsify/`.

Experiments are copied into the MR head checkout before pytest runs, so they
execute against MR code without ever living on the MR branch.

The directory is empty on `main` by design — `.gitkeep` only.

## Promotion

A promoted experiment is copied **byte-for-byte** into `tests/` by the
human-run `promote` job, and its hash is recorded in the certificate. The copy
in `tests/` is the permanent one; the scratch branch is deleted after merge.
