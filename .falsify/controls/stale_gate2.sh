#!/usr/bin/env bash
# Control 3 negative test: a Gate 2 authorization bound to head A must not
# authorize experiments at head B.
#
# Usage: ./stale_gate2.sh
# Expected: the certificate job exits non-zero with a stale-authorization error.
set -euo pipefail

cat <<'STEPS'
Control 3 — stale Gate 2 authorization

  1. On an MR, let the Trial flow post conjectures at head A.
  2. Authorize them: `falsify: approve all`.
  3. Push an unrelated commit to the MR branch, producing head B.
  4. Re-run the certificate job.

EXPECTED
  The certificate job fails with:
    "no valid Gate 2 authorization for head <B> at claims <version>"

  Per docs/gates.md, a new MR head invalidates Gate 2 and any unpromoted
  Gate 3 rulings. A RE-RUN of the same experiment digests against a new head
  is permitted without a new Gate 2 — this test covers the other case: new
  conjectures or new digests at a new head.
STEPS
