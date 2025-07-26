#!/bin/bash
# setup-gcp.sh - Initial Google Cloud Platform setup for WalleteriumImperium

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up Google Cloud Platform for WalleteriumImperium${NC}"

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

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo "  Gemini Model: $GEMINI_MODEL"
echo "  Repository: $REPOSITORY_NAME"

# Set the project
echo -e "${BLUE}🔧 Setting active project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    firestore.googleapis.com

# Create Artifact Registry repository
echo -e "${BLUE}🗃️ Creating Artifact Registry repository...${NC}"
gcloud artifacts repositories create $REPOSITORY_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="WalleteriumImperium Docker repository" \
    || echo -e "${YELLOW}⚠️ Repository might already exist${NC}"

# Configure Docker authentication
echo -e "${BLUE}🔐 Configuring Docker authentication...${NC}"
gcloud auth configure-docker $REGION-docker.pkg.dev

# Create service account
echo -e "${BLUE}👤 Creating service account...${NC}"
gcloud iam service-accounts create $SERVICE_ACCOUNT \
    --display-name="WalleteriumImperium Service Account" \
    --description="Service account for WalleteriumImperium receipt scanner" \
    || echo -e "${YELLOW}⚠️ Service account might already exist${NC}"

# Grant necessary permissions
echo -e "${BLUE}🔑 Granting permissions...${NC}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

# Vertex AI User role for Gemini access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

# Firestore User role for database access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/datastore.user"

# Cloud Run Invoker (if needed for internal calls)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker"

echo -e "${GREEN}✅ Google Cloud Platform setup complete!${NC}"
echo -e "${BLUE}📝 Next steps:${NC}"
echo "  1. Run: ./deploy/build-and-deploy.sh"
echo "  2. Your service will be available at a Cloud Run URL"

# Export variables for next script
export SERVICE_ACCOUNT_EMAIL
export REPOSITORY_NAME

echo -e "${YELLOW}💾 Environment variables set for deployment${NC}"
