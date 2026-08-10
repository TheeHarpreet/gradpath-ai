#!/usr/bin/env bash
set -euo pipefail

# Run once in Google Cloud Shell after setting PROJECT_ID and GITHUB_REPOSITORY.
: "${PROJECT_ID:?Set PROJECT_ID to the target Google Cloud project ID}"
: "${GITHUB_REPOSITORY:?Set GITHUB_REPOSITORY, for example TheeHarpreet/gradpath-ai}"

REGION="${REGION:-europe-west1}"
AR_REPOSITORY="${AR_REPOSITORY:-gradpath}"
POOL_ID="${POOL_ID:-github-actions}"
PROVIDER_ID="${PROVIDER_ID:-gradpath-github}"
DEPLOY_SA_NAME="${DEPLOY_SA_NAME:-gradpath-deployer}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-gradpath-runtime}"

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
DEPLOY_SA="${DEPLOY_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SA="${RUNTIME_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com sts.googleapis.com

gcloud artifacts repositories describe "$AR_REPOSITORY" --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "$AR_REPOSITORY" --repository-format docker --location "$REGION" --description "GradPath AI containers"

for account in "$DEPLOY_SA_NAME" "$RUNTIME_SA_NAME"; do
  gcloud iam service-accounts describe "${account}@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1 || \
    gcloud iam service-accounts create "$account" --display-name "$account"
done

for secret in gradpath-openai-api-key gradpath-demo-access-token; do
  gcloud secrets describe "$secret" >/dev/null 2>&1 || gcloud secrets create "$secret" --replication-policy automatic
  gcloud secrets add-iam-policy-binding "$secret" \
    --member "serviceAccount:${RUNTIME_SA}" \
    --role roles/secretmanager.secretAccessor >/dev/null
done

for role in roles/run.developer roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:${DEPLOY_SA}" --role "$role" --condition=None >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member "serviceAccount:${DEPLOY_SA}" --role roles/iam.serviceAccountUser >/dev/null

gcloud iam workload-identity-pools describe "$POOL_ID" --location global >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools create "$POOL_ID" --location global --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" --workload-identity-pool "$POOL_ID" --location global >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
    --workload-identity-pool "$POOL_ID" --location global \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition "assertion.repository=='${GITHUB_REPOSITORY}'"

gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_REPOSITORY}" >/dev/null

cat <<EOF

Create these GitHub Environment variables under the staging environment:
GCP_PROJECT_ID=${PROJECT_ID}
GCP_REGION=${REGION}
GCP_ARTIFACT_REPOSITORY=${AR_REPOSITORY}
GCP_WORKLOAD_IDENTITY_PROVIDER=projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}
GCP_DEPLOY_SERVICE_ACCOUNT=${DEPLOY_SA}
GCP_RUNTIME_SERVICE_ACCOUNT=${RUNTIME_SA}

The secret containers exist, but no secret values were created. Add each value
securely in Secret Manager before running the deployment workflow.
EOF
