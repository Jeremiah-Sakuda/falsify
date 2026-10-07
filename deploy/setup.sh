#!/usr/bin/env bash
# One-time Google Cloud setup. Run once; everything after this is CI.
#
# Creates: Artifact Registry repo, both Cloud Run services, the Workload
# Identity pool and provider, and the attribute condition that binds deploy
# identity to this project path AND the protected-environment claim.
set -euo pipefail

: "${GCP_PROJECT_ID:?set GCP_PROJECT_ID}"
: "${GITLAB_PROJECT_PATH:?set GITLAB_PROJECT_PATH, e.g. group/falsify}"

REGION="${REGION:-us-east1}"
POOL="falsify-gitlab"
PROVIDER="gitlab-oidc"
SA="falsify-deployer"
REPO="falsify"

echo "==> project ${GCP_PROJECT_ID}, region ${REGION}"
gcloud config set project "${GCP_PROJECT_ID}"

echo "==> enabling services"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  monitoring.googleapis.com

echo "==> Artifact Registry"
gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker --location="${REGION}" \
  --description="Falsify images, tagged <short-sha>-<certificate-hash>" \
  || echo "    exists"

echo "==> deploy service account"
gcloud iam service-accounts create "${SA}" \
  --display-name="Falsify deployer (GitLab OIDC, no stored key)" \
  || echo "    exists"

SA_EMAIL="${SA}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="${ROLE}" --quiet
done

echo "==> Workload Identity pool"
gcloud iam workload-identity-pools create "${POOL}" \
  --location=global --display-name="GitLab CI" || echo "    exists"

# ---------------------------------------------------------------------------
# The load-bearing line. The attribute condition requires BOTH this project
# path AND a protected environment, so no job on a scratch or MR branch can
# obtain a cloud identity even if it holds a valid GitLab ID token.
# ---------------------------------------------------------------------------
echo "==> OIDC provider with the attribute condition"
gcloud iam workload-identity-pools providers create-oidc "${PROVIDER}" \
  --location=global --workload-identity-pool="${POOL}" \
  --issuer-uri="https://gitlab.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.project_path=assertion.project_path,attribute.environment=assertion.environment,attribute.environment_protected=assertion.environment_protected" \
  --attribute-condition="assertion.project_path == '${GITLAB_PROJECT_PATH}' && assertion.environment_protected == 'true' && assertion.environment in ['staging','production']" \
  || echo "    exists"

PROJECT_NUMBER="$(gcloud projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')"
POOL_ID="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}"

gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.project_path/${GITLAB_PROJECT_PATH}" \
  --quiet

echo "==> Cloud Run services"
for ENV in staging prod; do
  gcloud run services replace "deploy/cloudrun.${ENV}.yaml" --region="${REGION}" \
    || echo "    ${ENV}: replace failed (first deploy comes from CI)"
done

cat <<SUMMARY

Done. Set these as GitLab CI/CD variables (none of them is a key):

  GCP_PROJECT_ID     = ${GCP_PROJECT_ID}
  GCP_WIF_PROVIDER   = ${POOL_ID}/providers/${PROVIDER}
  GCP_DEPLOY_SA      = ${SA_EMAIL}
  ARTIFACT_REGISTRY  = ${REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPO}

No service account key was created and none should be. Deploy jobs exchange
GitLab's OIDC ID token; see docs/controls.md Control 5.
SUMMARY
