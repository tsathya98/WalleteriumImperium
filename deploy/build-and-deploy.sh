#!/bin/bash
# build-and-deploy.sh - Build and deploy WalleteriumImperium to Cloud Run

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏗️ Building and deploying WalleteriumImperium to Cloud Run${NC}"

# Check if required environment variables are set
if [ -z "$PROJECT_ID" ] || [ -z "$REGION" ]; then
    echo -e "${RED}❌ Please set PROJECT_ID and REGION environment variables${NC}"
    echo "Example:"
    echo "export PROJECT_ID=your-project-id"
    echo "export REGION=us-central1"
    exit 1
fi

# Set default values
SERVICE_NAME=${SERVICE_NAME:-"walleterium-receipt-scanner"}
SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-"walleterium-sa"}
GEMINI_MODEL=${GEMINI_MODEL:-"gemini-2.5-flash"}
REPOSITORY_NAME=${REPOSITORY_NAME:-"walleterium-repo"}

# Generate timestamp for image tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="v${TIMESTAMP}"

# Full image name
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$SERVICE_NAME:$IMAGE_TAG"
IMAGE_LATEST="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$SERVICE_NAME:latest"

echo -e "${YELLOW}📋 Build Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME"
echo "  Service Account: ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

# Navigate to project root
cd "$(dirname "$0")/.."

# Build Docker image
echo -e "${BLUE}🐳 Building Docker image...${NC}"
docker build \
    --platform linux/amd64 \
    -t $IMAGE_NAME \
    -t $IMAGE_LATEST \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Push image to Artifact Registry
echo -e "${BLUE}📤 Pushing image to Artifact Registry...${NC}"
docker push $IMAGE_NAME
docker push $IMAGE_LATEST

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker push failed${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_NAME \
    --platform=managed \
    --region=$REGION \
    --service-account="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --allow-unauthenticated \
    --memory="2Gi" \
    --cpu="1" \
    --timeout="300" \
    --concurrency="10" \
    --min-instances="0" \
    --max-instances="10" \
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,VERTEX_AI_LOCATION=$REGION,VERTEX_AI_MODEL=$GEMINI_MODEL,PORT=8080" \
    --port="8080"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run deployment failed${NC}"
    exit 1
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${BLUE}📝 Deployment Details:${NC}"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME"
echo "  Service URL: $SERVICE_URL"
echo ""
echo -e "${YELLOW}🧪 Test your deployment:${NC}"
echo "  Health Check: curl $SERVICE_URL/api/v1/health"
echo "  API Docs: $SERVICE_URL/docs"
echo "  Receipt Upload: $SERVICE_URL/api/v1/receipts/upload"
echo ""
echo -e "${BLUE}🔍 Monitoring:${NC}"
echo "  Cloud Run Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo "  Logs: gcloud logs tail projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout --log-filter='resource.labels.service_name=\"$SERVICE_NAME\"'"

# Test health endpoint
echo -e "${BLUE}🏥 Testing health endpoint...${NC}"
sleep 10  # Wait for service to be ready
curl -s "$SERVICE_URL/api/v1/health" | python3 -m json.tool || echo -e "${YELLOW}⚠️ Health check failed - service might still be starting${NC}"

echo -e "${GREEN}🎉 WalleteriumImperium is now live at: $SERVICE_URL${NC}" 