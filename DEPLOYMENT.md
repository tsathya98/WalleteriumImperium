# 🚀 WalleteriumImperium - Cloud Run Deployment Guide

Deploy your intelligent receipt scanner with **Gemini 2.5 Flash** to Google Cloud Run using Google SDK.

## 📋 **Prerequisites**

### ✅ **Required Tools**
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Active Google Cloud Project with billing enabled

### ✅ **Required APIs**
The deployment script will automatically enable these, but verify they're available:
- Cloud Run API
- Artifact Registry API
- Vertex AI API
- Firestore API
- Cloud Build API

---

## 🔧 **Quick Deployment** [[memory:4426346]]

### **For Windows Users:**

1. **Set Environment Variables:**
```cmd
set PROJECT_ID=your-project-id
set REGION=us-central1
```

2. **Run Deployment:**
```cmd
.\deploy\deploy-windows.bat
```

### **For Linux/Mac Users:**

1. **Set Environment Variables:**
```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
```

2. **Run Setup:**
```bash
chmod +x deploy/setup-gcp.sh
chmod +x deploy/build-and-deploy.sh
./deploy/setup-gcp.sh
```

3. **Build and Deploy:**
```bash
./deploy/build-and-deploy.sh
```

---

## 🎯 **Detailed Step-by-Step Deployment**

### **Step 1: Authenticate with Google Cloud**

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable application default credentials for local development
gcloud auth application-default login
```

### **Step 2: Set Environment Variables**

**Windows (cmd):**
```cmd
set PROJECT_ID=your-google-cloud-project-id
set REGION=us-central1
set SERVICE_NAME=walleterium-receipt-scanner
set GEMINI_MODEL=gemini-2.5-flash
```

**Linux/Mac/PowerShell:**
```bash
export PROJECT_ID=your-google-cloud-project-id
export REGION=us-central1
export SERVICE_NAME=walleterium-receipt-scanner
export GEMINI_MODEL=gemini-2.5-flash
```

### **Step 3: Manual Deployment (Alternative)**

If you prefer manual control:

```bash
# 1. Enable APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    firestore.googleapis.com

# 2. Create Artifact Registry repository
gcloud artifacts repositories create walleterium-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="WalleteriumImperium Docker repository"

# 3. Configure Docker authentication
gcloud auth configure-docker $REGION-docker.pkg.dev

# 4. Create service account
gcloud iam service-accounts create walleterium-sa \
    --display-name="WalleteriumImperium Service Account"

# 5. Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:walleterium-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:walleterium-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# 6. Build and push Docker image
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/walleterium-repo/walleterium-receipt-scanner:latest"

docker build --platform linux/amd64 -t $IMAGE_NAME .
docker push $IMAGE_NAME

# 7. Deploy to Cloud Run
gcloud run deploy walleterium-receipt-scanner \
    --image=$IMAGE_NAME \
    --platform=managed \
    --region=$REGION \
    --service-account="walleterium-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --allow-unauthenticated \
    --memory="2Gi" \
    --cpu="1" \
    --timeout="300" \
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,VERTEX_AI_LOCATION=$REGION,VERTEX_AI_MODEL=gemini-2.5-flash,PORT=8080" \
    --port="8080"
```

---

## 🧪 **Testing Your Deployment**

Once deployed, you'll get a Cloud Run URL. Test these endpoints:

### **Health Check**
```bash
curl https://your-service-url/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "firestore": "healthy",
    "vertex_ai": "healthy",
    "enhanced_agent": "healthy"
  }
}
```

### **API Documentation**
Visit: `https://your-service-url/docs`

### **Receipt Upload Test**
```bash
curl -X POST "https://your-service-url/api/v1/receipts/upload" \
  -F "file=@test-receipt.jpg" \
  -F "user_id=test-user"
```

---

## 📊 **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   Cloud Run     │───▶│  Gemini 2.5     │
│                 │    │  FastAPI        │    │  Flash          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Firestore     │
                       │   Database      │
                       └─────────────────┘
```

**Key Components:**
- **FastAPI**: High-performance Python web framework
- **Gemini 2.5 Flash**: Google's latest multimodal AI via Vertex AI
- **Cloud Run**: Serverless container platform
- **Firestore**: NoSQL document database for results
- **Artifact Registry**: Container image storage

---

## 🔍 **Monitoring & Debugging**

### **View Logs**
```bash
# Real-time logs
gcloud logs tail projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout \
    --log-filter='resource.labels.service_name="walleterium-receipt-scanner"'

# Historical logs
gcloud logs read projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout \
    --log-filter='resource.labels.service_name="walleterium-receipt-scanner"' \
    --limit=100
```

### **Cloud Console**
- **Cloud Run**: https://console.cloud.google.com/run
- **Logs**: https://console.cloud.google.com/logs
- **Vertex AI**: https://console.cloud.google.com/vertex-ai

---

## ⚙️ **Configuration Options**

### **Environment Variables**
The deployment sets these automatically:

| Variable | Value | Description |
|----------|-------|-------------|
| `ENVIRONMENT` | `production` | Runtime environment |
| `GOOGLE_CLOUD_PROJECT_ID` | Your project ID | GCP project identifier |
| `VERTEX_AI_LOCATION` | `us-central1` | Vertex AI region |
| `VERTEX_AI_MODEL` | `gemini-2.5-flash` | AI model to use |
| `PORT` | `8080` | Container port |

### **Resource Limits**
- **Memory**: 2 GiB
- **CPU**: 1 vCPU
- **Timeout**: 300 seconds
- **Concurrency**: 10 requests per instance
- **Max Instances**: 10

---

## 🔧 **Troubleshooting**

### **Common Issues**

**1. "Permission denied" errors:**
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID
```

**2. "API not enabled" errors:**
```bash
# Enable all required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com firestore.googleapis.com
```

**3. Docker build failures:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with verbose output
docker build --no-cache --progress=plain -t test-image .
```

**4. Vertex AI timeout errors:**
```bash
# Check Vertex AI quota
gcloud ai endpoints list --region=$REGION

# Verify model availability
gcloud ai models list --region=$REGION
```

### **Health Check Debugging**
```bash
# Test individual components
curl https://your-service-url/api/v1/health/firestore
curl https://your-service-url/api/v1/health/vertex-ai
```

---

## 🚀 **Next Steps**

1. **Custom Domain**: Set up a custom domain for your service
2. **Authentication**: Add Firebase Auth or Identity-Aware Proxy
3. **Monitoring**: Set up Cloud Monitoring alerts
4. **CI/CD**: Automate deployments with Cloud Build
5. **Scaling**: Configure auto-scaling based on usage

---

## 💰 **Cost Optimization**

- **Vertex AI**: Gemini 2.5 Flash is cost-effective (~$0.005 per request)
- **Cloud Run**: Pay only for actual usage, scales to zero
- **Firestore**: Document-based pricing
- **Storage**: Minimal storage costs for processing tokens

**Estimated Monthly Cost (1000 receipts):**
- Vertex AI: ~$5
- Cloud Run: ~$2
- Firestore: ~$1
- **Total**: ~$8/month

---

**🎉 Your intelligent receipt scanner with Gemini 2.5 Flash is now live on Cloud Run!**

For support or questions, check the logs or create an issue in the repository.
