#!/usr/bin/env bash
# Control 2, layer 3: refuse any scratch branch whose diff touches a file
# outside .falsify/.
#
# This is the layer that holds regardless of whether the flow framework
# supports a fixed branch parameter on the write tool (Oct 9 question Q2).
#
# The realistic attack: a prompt-injected MR talks the Falsifier into editing
# .gitlab-ci.yml on its own scratch branch.
#
# Usage: check_scratch_scope.sh <scratch-branch> <merge-base>
set -euo pipefail

BRANCH="${1:?usage: check_scratch_scope.sh <scratch-branch> <merge-base>}"
BASE="${2:?usage: check_scratch_scope.sh <scratch-branch> <merge-base>}"

echo "Control 2: verifying ${BRANCH} touches nothing outside .falsify/"

CHANGED="$(git diff --name-only "${BASE}...${BRANCH}")"

if [ -z "${CHANGED}" ]; then
  echo "  no changes on the scratch branch"
  exit 0
fi

VIOLATIONS="$(printf '%s\n' "${CHANGED}" | grep -v '^\.falsify/' || true)"

if [ -n "${VIOLATIONS}" ]; then
  echo
  echo "REFUSED: branch-scope violation. These files are outside .falsify/:"
  printf '  %s\n' ${VIOLATIONS}
  echo
  echo "No experiment was run. The scratch branch may only contain files"
  echo "under .falsify/. See docs/controls.md, Control 2."
  exit 1
fi

echo "  ok — $(printf '%s\n' "${CHANGED}" | wc -l | tr -d ' ') file(s), all under .falsify/"
