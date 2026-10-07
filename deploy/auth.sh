#!/usr/bin/env bash
# Exchange the GitLab OIDC ID token for a Google access token.
# No stored cloud secret is involved at any point.
set -euo pipefail

: "${GCP_ID_TOKEN:?no OIDC ID token; this job has no id_tokens block}"
: "${GCP_WIF_PROVIDER:?set GCP_WIF_PROVIDER}"
: "${GCP_DEPLOY_SA:?set GCP_DEPLOY_SA}"

echo "${GCP_ID_TOKEN}" > /tmp/gitlab-oidc.jwt

cat > /tmp/wif-credentials.json <<JSON
{
  "type": "external_account",
  "audience": "//iam.googleapis.com/${GCP_WIF_PROVIDER}",
  "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
  "token_url": "https://sts.googleapis.com/v1/token",
  "credential_source": { "file": "/tmp/gitlab-oidc.jwt" },
  "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${GCP_DEPLOY_SA}:generateAccessToken"
}
JSON

gcloud auth login --cred-file=/tmp/wif-credentials.json --quiet
gcloud config set project "${GCP_PROJECT_ID}" --quiet

echo "authenticated as ${GCP_DEPLOY_SA} via WIF (no stored key)"
