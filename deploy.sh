#!/bin/bash

# Configuration
PROJECT_ID="python-learning-coach-ai"
REGION="us-central1"
SERVICE_NAME="python-learning-coach"
DEPLOYMENT_DIR="python_learning_coach_deploy"

echo "🚀 Deploying Python Learning Coach to Cloud Run"
echo "=============================================="

# 1. Set the project
gcloud config set project ${PROJECT_ID}

# 2. Build and push Docker image
echo "📦 Building Docker image..."
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
cd ${DEPLOYMENT_DIR}
docker build -t ${IMAGE_NAME}:latest .
docker push ${IMAGE_NAME}:latest

# 3. Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeour 300 \
    --min-instances 0 \
    --max-instances 2 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars "GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=1" \
    --set-env-vars "ADK_MODEL=gemini-1.5-flash-001"

# 4. Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format "value(status.url)")

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "📋 Test Endpoints:"
echo "   Health: ${SERVICE_URL}/health"
echo "   Chat: ${SERVICE_URL}/chat"
echo "   Curriculum: ${SERVICE_URL}/curriculum"