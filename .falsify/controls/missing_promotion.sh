#!/usr/bin/env bash
# Control 4 negative test: a remedy-accepted finding with no promoted file
# must block merge.
#
# Usage: ./missing_promotion.sh
# Expected: the certificate job exits non-zero with a missing-promotion error.
set -euo pipefail

cat <<'STEPS'
Control 4 — promotion enforced at the merge gate

  1. Let an experiment produce a functional refutation (FAIL/FAIL head, PASS base).
  2. Apply the Advocate's suggestion so the remedy is accepted.
  3. Let the rerun go green.
  4. Do NOT run the promote job.
  5. Re-run the certificate job.

EXPECTED
  The certificate job fails with:
    "X<N>: remedy accepted but no promoted file at head <sha>"

  A remedy-accepted refutation resolves only when BOTH hold: the rerun is
  green, AND the promoted file is present at the MR head with the hash
  recorded at promotion time. A sustained contest resolves without promotion.

  The original failing evidence stays in the record either way. It is never
  overwritten by the later PASS.
STEPS
