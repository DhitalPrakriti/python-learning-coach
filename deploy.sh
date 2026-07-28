#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="python-learning-coach"
REGION="northamerica-northeast2"
VERTEX_LOCATION="${VERTEX_LOCATION:-northamerica-northeast1}"

# You can optionally export GOOGLE_CLOUD_PROJECT, otherwise it uses gcloud config
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"

# Artifact Registry repo name (create once)
AR_REPO="python-learning-coach"

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
  echo "ERROR: Set your project first:"
  echo "  gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

# Artifact Registry image URL (NOT gcr.io)
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${SERVICE_NAME}"

echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Vertex: ${VERTEX_LOCATION}"
echo "Repo:   ${AR_REPO}"
echo "Image:  ${IMAGE_NAME}:latest"

echo "Enabling required services..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  --project "${PROJECT_ID}"

echo "Ensuring Artifact Registry repo exists..."
# If it already exists, this will fail — we ignore that.
gcloud artifacts repositories create "${AR_REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Docker images for ${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  2>/dev/null || echo "Repo '${AR_REPO}' already exists."

echo "Building image with Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}:latest" --project "${PROJECT_ID}" .

echo "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}:latest" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --timeout 300 \
  --project "${PROJECT_ID}" \
  --set-env-vars "FIRESTORE_ENABLED=1,GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${VERTEX_LOCATION}"

echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)"
