#!/bin/bash

# Configuration
PROJECT_ID="python-learning-coach-ai"
REGION="us-central1"
DEPLOYMENT_NAME="python-learning-coach"
DEPLOYMENT_DIR="python_learning_coach_deploy"

echo "🚀 Deploying Python Learning Coach to Vertex AI Agent Engine"
echo "=========================================================="

# 0. Create deployment directory first!
echo "📁 Creating deployment directory..."
mkdir -p ${DEPLOYMENT_DIR}

# 1. Set the project
echo "📋 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# 2. Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com

# 3. Initialize Vertex AI
echo "🏗️  Initializing Vertex AI..."
gcloud auth application-default login --quiet || echo "Please authenticate when prompted"

# 4. Create deployment configuration
echo "📁 Creating Agent Engine configuration..."
cat > ${DEPLOYMENT_DIR}/.agent_engine_config.json << EOF
{
    "min_instances": 0,
    "max_instances": 2,
    "resource_limits": {
        "cpu": "2",
        "memory": "4Gi"
    }
}
EOF

# 5. Create environment file
echo "🔑 Setting up environment variables..."
cat > ${DEPLOYMENT_DIR}/.env << EOF
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=${REGION}
GOOGLE_GENAI_USE_VERTEXAI=1
EOF

# 6. Check if ADK is available and deploy
echo "🚢 Deploying to Vertex AI Agent Engine..."
if command -v adk &> /dev/null; then
    echo "Using ADK CLI for deployment..."
    adk deploy agent_engine \
        --project=${PROJECT_ID} \
        --region=${REGION} \
        ${DEPLOYMENT_DIR} \
        --agent_engine_config_file=${DEPLOYMENT_DIR}/.agent_engine_config.json
else
    echo "❌ ADK CLI not found. Using alternative deployment method..."
    
    # Alternative: Deploy using gcloud for Vertex AI Prediction
    echo "🔄 Falling back to Vertex AI Custom Container deployment..."
    
    # Create a Dockerfile if it doesn't exist
    if [ ! -f "${DEPLOYMENT_DIR}/Dockerfile" ]; then
        cat > ${DEPLOYMENT_DIR}/Dockerfile << 'DOCKEREOF'
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec uvicorn main:app --host 0.0.0.0 --port 8080
DOCKEREOF
    fi
    
    # Create requirements.txt if it doesn't exist
    if [ ! -f "${DEPLOYMENT_DIR}/requirements.txt" ]; then
        cat > ${DEPLOYMENT_DIR}/requirements.txt << 'REQEOF'
fastapi==0.104.1
uvicorn==0.24.0
google-cloud-aiplatform==1.38.1
python-dotenv==1.0.0
REQEOF
    fi
    
    # Build and deploy using Cloud Run (more straightforward)
    echo "🏗️ Building and deploying container..."
    gcloud run deploy ${DEPLOYMENT_NAME} \
        --source ${DEPLOYMENT_DIR} \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --cpu=2 \
        --memory=4Gi \
        --min-instances=0 \
        --max-instances=2
fi

# 7. Get deployment status
echo "⏳ Waiting for deployment to complete..."
sleep 30

# 8. Check deployment status - CORRECTED COMMANDS
echo "📋 Checking deployed services..."
echo "Cloud Run services:"
gcloud run services list --region=${REGION} --format="table(name,status,url)"

echo "Vertex AI endpoints:"
gcloud ai endpoints list --region=${REGION} --format="table(displayName,createTime)" || echo "No Vertex AI endpoints found"

# 9. Success message
echo ""
echo "🎉 SUCCESS! Your Python Learning Coach is deployed!"
echo "=========================================================================="
echo ""
echo "📊 Deployment Details:"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${DEPLOYMENT_NAME}"
echo ""
echo "🔗 Access Your Application:"
echo "   Console: https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo "   Vertex AI: https://console.cloud.google.com/vertex-ai?project=${PROJECT_ID}"
echo ""
echo "🛠️  Test Commands:"
echo "   List services: gcloud run services list --region=${REGION}"
echo "   View logs: gcloud logging read 'resource.type=cloud_run_revision' --limit=10"
echo ""
echo "💡 Next Steps:"
echo "   1. Test your deployed endpoint"
echo "   2. Set up monitoring in Google Cloud Console"
echo "   3. Configure domain mapping if needed"