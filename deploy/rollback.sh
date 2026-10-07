#!/usr/bin/env bash
# Route 100% of traffic to the previous revision. Appends an event via the
# calling job.
set -euo pipefail

ENVIRONMENT="${1:?usage: rollback.sh <staging|production>}"
REGION="${REGION:-us-east1}"

case "${ENVIRONMENT}" in
  staging)    SERVICE="falsify-staging" ;;
  production) SERVICE="falsify-prod" ;;
  *) echo "unknown environment ${ENVIRONMENT}" >&2; exit 1 ;;
esac

mapfile -t REVISIONS < <(
  gcloud run revisions list --service="${SERVICE}" --region="${REGION}" \
    --sort-by="~metadata.creationTimestamp" --format='value(metadata.name)'
)

if [ "${#REVISIONS[@]}" -lt 2 ]; then
  echo "REFUSED: only ${#REVISIONS[@]} revision(s); nothing to roll back to" >&2
  exit 1
fi

PREVIOUS="${REVISIONS[1]}"
echo "rolling ${SERVICE} back from ${REVISIONS[0]} to ${PREVIOUS}"

gcloud run services update-traffic "${SERVICE}" \
  --region="${REGION}" --to-revisions="${PREVIOUS}=100" --quiet

echo "traffic now on ${PREVIOUS}"
