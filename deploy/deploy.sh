#!/usr/bin/env bash
# Deploy by image DIGEST, never by tag. The tag is mutable; the digest is not,
# and the digest is what prod-watch verifies against events.md.
set -euo pipefail

ENVIRONMENT="${1:?usage: deploy.sh <staging|production> <image-digest>}"
DIGEST="${2:?usage: deploy.sh <staging|production> <image-digest>}"
REGION="${REGION:-us-east1}"

case "${ENVIRONMENT}" in
  staging)    SERVICE="falsify-staging"; MIN=0; MAX=1 ;;
  production) SERVICE="falsify-prod";    MIN=1; MAX=1 ;;
  *) echo "unknown environment ${ENVIRONMENT}" >&2; exit 1 ;;
esac

IMAGE="${ARTIFACT_REGISTRY}/falsify@${DIGEST}"
echo "deploying ${IMAGE} to ${SERVICE} (${REGION})"

gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances="${MIN}" \
  --max-instances="${MAX}" \
  --port=8080 \
  --cpu=1 --memory=512Mi \
  --set-env-vars="FALSIFY_ENV=${ENVIRONMENT}" \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(status.url)')"
REVISION="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(status.latestReadyRevisionName)')"

echo "${URL}" > "${ENVIRONMENT}.url"
echo
echo "url      ${URL}"
echo "revision ${REVISION}"
echo "digest   ${DIGEST}"
