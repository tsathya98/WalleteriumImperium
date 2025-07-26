# Project Raseed - AI-Powered Receipt Management for Google Wallet

**Team:** Walletarium Imperium
**Event:** Google Cloud Agentic AI Hackathon
**Project:** Real-time AI Receipt Processing System

## 📋 Table of Contents

- [Overview](#overview)
- [Real-time Architecture](#real-time-architecture)
- [Python Backend Stack](#python-backend-stack)
- [API Design](#api-design)
- [Token-Based Processing](#token-based-processing)
- [Database Schema](#database-schema)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Testing Guide](#testing-guide)
- [Performance & Monitoring](#performance--monitoring)

## 🎯 Overview

Project Raseed is a **Python-based real-time AI system** that revolutionizes receipt management for Google Wallet. Built for the Google Cloud Agentic AI Hackathon, it provides **immediate API responses** with intelligent token-based polling for AI processing that exceeds 30-second limits.

### Key Features

- **⚡ Real-time API Processing**: Immediate token response + intelligent polling
- **🐍 Pure Python Backend**: FastAPI + Cloud Run serverless architecture
- **🤖 Advanced AI**: Vertex AI Gemini 2.0 Flash for multilingual receipt analysis
- **💳 Google Wallet Integration**: Dynamic pass generation
- **🌍 Indian Market Focus**: Hindi, Tamil, Kannada, Telugu support
- **🔄 Smart Retry Logic**: Token-based polling with exponential backoff
- **🏠 Local Testing**: Full Docker development environment

## 🏗️ Real-time Architecture

### System Flow Diagram

```mermaid
graph TB
    subgraph "Flutter Mobile App (Other Team)"
        A[Flutter App] --> B[Camera/Gallery Upload]
    end
    
    subgraph "Google Cloud - Python Backend"
        C[API Gateway] --> D[FastAPI Cloud Run]
        D --> E[Token Service]
        D --> F[Background Processing]
        F --> G[Vertex AI Gemini]
        F --> H[Firestore Database]
    end
    
    subgraph "Real-time Token Flow"
        I[POST /upload → Immediate Token]
        J[GET /status/{token} → Poll Results]
        K[Async AI Processing]
    end
    
    A -->|HTTP POST| C
    C -->|Route Request| D
    D -->|Generate Token| E
    D -->|Start Background| F
    F -->|AI Analysis| G
    F -->|Save Results| H
    A -->|Poll Status| J
```

### Processing Timeline

```
🔄 Real-time Flow (Python FastAPI):
┌─────────────────────────────────────────────────────────────┐
│ 0-2s    │ POST /upload → Token Generated → HTTP 202         │
│ 2-45s   │ Background: Vertex AI Processing                  │
│ Every 3s│ GET /status/{token} → Progress Updates            │
│ 45s+    │ Results Ready → GET returns final JSON            │
└─────────────────────────────────────────────────────────────┘

⚠️ If >30s timeout: Frontend retries with same token_id
✅ Backend maps token to processing state and returns results
```

## 🐍 Python Backend Stack

### Core Technology Stack

```python
# Primary Technologies
Framework: FastAPI (High-performance Python web framework)
Server: Cloud Run (1 hour timeout, perfect for AI processing)
AI Engine: Vertex AI Python SDK + Gemini 2.0 Flash
Database: Firestore (Python client)
Authentication: Firebase Auth (Python admin SDK)
Validation: Pydantic (Data validation and serialization)
Async: asyncio + uvicorn ASGI server

# Development & Deployment
Local Dev: Docker Compose + Emulators
Testing: pytest + pytest-asyncio
Monitoring: Prometheus + Google Cloud Monitoring
CI/CD: Google Cloud Build
```

### Project Structure

```
raseed_backend/                    # Python Backend Root
├── main.py                       # FastAPI application entry
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Production container
├── docker-compose.yml            # Local development
├──
├── app/
│   ├── api/                     # FastAPI routes
│   │   ├── receipts.py          # Receipt processing endpoints
│   │   └── health.py            # Health check endpoints
│   │
│   ├── models/                  # Pydantic data models
│   │   ├── receipt.py           # Receipt & token models
│   │   └── response.py          # API response models
│   │
│   ├── services/                # Business logic (Python)
│   │   ├── receipt_processor.py # Main processing service
│   │   ├── vertex_ai_service.py # Gemini AI integration
│   │   ├── token_service.py     # Token management
│   │   └── firestore_service.py # Database operations
│   │
│   └── core/                    # Configuration & utilities
│       ├── config.py            # Settings management
│       ├── security.py          # Firebase auth
│       └── database.py          # Database connections
│
├── tests/                       # Python test suite
├── scripts/                     # Deployment scripts
└── docs/                        # Documentation
```

## 📡 API Design

### Real-time Processing Endpoints

#### **1. Upload Endpoint - Immediate Token Response**

```python
# POST /api/v1/receipts/upload
class ReceiptUploadRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image")
    user_id: str = Field(..., description="User identifier")
    metadata: Optional[UploadMetadata] = None

class ReceiptUploadResponse(BaseModel):
    processing_token: str = Field(..., description="Token for status tracking")
    estimated_time: int = Field(..., description="Estimated processing seconds")
    status_url: str = Field(..., description="URL for polling status")
    expires_at: float = Field(..., description="Token expiration timestamp")
    retry_after: int = Field(default=3, description="Polling interval")

# Example Response (returned in <2 seconds):
{
  "processing_token": "proc_1721934567_abc123def",
  "estimated_time": 45,
  "status_url": "/api/v1/receipts/status/proc_1721934567_abc123def",
  "expires_at": 1721935167.0,
  "retry_after": 3
}
```

#### **2. Status Polling Endpoint**

```python
# GET /api/v1/receipts/status/{token}
class ProcessingStatusResponse(BaseModel):
    processing_token: str
    status: ProcessingStatus  # queued, processing, completed, failed
    progress: ProcessingProgress
    result: Optional[ProcessingResult] = None  # When completed
    error: Optional[ProcessingError] = None    # When failed
    next_poll_after: int = Field(..., description="Seconds until next poll")
    expires_at: float

# Example Responses:
# Processing (30% complete):
{
  "processing_token": "proc_1721934567_abc123def",
  "status": "processing",
  "progress": {
    "stage": "ai_analysis",
    "percentage": 30,
    "current_step": "Analyzing receipt with Vertex AI"
  },
  "next_poll_after": 3,
  "expires_at": 1721935167.0
}

# Completed (100%):
{
  "processing_token": "proc_1721934567_abc123def",
  "status": "completed",
  "result": {
    "receipt_id": "receipt_20250726_xyz789",
    "store_info": {"name": "Fresh Mart", "date": "2025-07-26"},
    "items": [{"name": "Basmati Rice", "total_price": 450.0}],
    "totals": {"total": 531.0},
    "confidence_score": 94.5
  },
  "next_poll_after": 0
}
```

## 🔄 Token-Based Processing

### Smart Retry Mechanism

```python
# Frontend Implementation (Flutter team reference)
class ReceiptProcessingService:
    static const int MAX_RETRIES = 20
    static const int BASE_DELAY = 3

    Future<ReceiptResult> uploadAndProcess(File imageFile) async {
        # Step 1: Upload and get token (fast response)
        final uploadResponse = await _uploadReceipt(imageFile)
        final token = uploadResponse.processingToken
        
        # Step 2: Poll for results with smart retry
        return await _pollForResults(token)
    }
    
    Future<ReceiptResult> _pollForResults(String token) async {
        int attempt = 0
        int delay = BASE_DELAY
        
        while attempt < MAX_RETRIES:
            try:
                final response = await _checkStatus(token)
                
                switch response.status:
                    case ProcessingStatus.COMPLETED:
                        return ReceiptResult.success(response.result!)
                        
                    case ProcessingStatus.FAILED:
                        if response.error?.retryPossible == true:
                            delay = min(delay * 2, MAX_DELAY)
                        else:
                            return ReceiptResult.error(response.error!)
                        break
                        
                    case ProcessingStatus.PROCESSING:
                        delay = response.nextPollAfter ?? BASE_DELAY
                        break
                        
            except e:
                # Network timeout - exponential backoff
                delay = min(delay * 2, MAX_DELAY)
                
            attempt++
            await Future.delayed(Duration(seconds: delay))
        
        return ReceiptResult.timeout()
    }
```

### Python Backend Processing

```python
# app/services/receipt_processor.py
class ReceiptProcessor:
    async def process_receipt_async(
        self,
        processing_token: str,
        image_base64: str,
        user_id: str
    ):
        """Main async processing method"""
        try:
            # Update status: Processing started
            await self.token_service.update_progress(
                processing_token,
                ProcessingStatus.PROCESSING,
                ProcessingProgress(
                    stage=ProcessingStage.VALIDATION,
                    percentage=10,
                    current_step="Validating image data"
                )
            )
            
            # Step 1: Image validation & optimization
            image_buffer = base64.b64decode(image_base64)
            optimized_image = await self.optimize_image_for_ai(image_buffer)
            
            # Step 2: Vertex AI processing
            await self.token_service.update_progress(
                processing_token,
                ProcessingStatus.PROCESSING,
                ProcessingProgress(
                    stage=ProcessingStage.AI_ANALYSIS,
                    percentage=30,
                    current_step="Processing with Vertex AI Gemini"
                )
            )
            
            result = await self.vertex_ai_service.process_receipt_image(
                base64.b64encode(optimized_image).decode(),
                user_context={"user_id": user_id}
            )
            
            # Step 3: Save results
            await self.token_service.update_progress(
                processing_token,
                ProcessingStatus.PROCESSING,
                ProcessingProgress(
                    stage=ProcessingStage.FINALIZATION,
                    percentage=90,
                    current_step="Saving results and generating wallet pass"
                )
            )
            
            # Save to database
            await self.firestore_service.save_receipt(user_id, result)
            
            # Mark as completed
            await self.token_service.complete_processing(
                processing_token,
                result.dict()
            )
            
        except Exception as e:
            await self.token_service.mark_failed(
                processing_token,
                ProcessingError(
                    code="PROCESSING_FAILED",
                    message=str(e),
                    retry_possible=self._is_retryable_error(e)
                )
            )

# app/services/vertex_ai_service.py
class VertexAIService:
    """Vertex AI Gemini integration service"""
    
    async def process_receipt_image(
        self,
        image_base64: str,
        user_context: Dict[str, Any]
    ) -> ProcessingResult:
        """Process receipt with Gemini 2.0 Flash"""
        
        # Initialize Vertex AI
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location="asia-south1"  # Mumbai region for India
        )
        
        model = GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "max_output_tokens": 8192,
                "temperature": 0.1,  # Low for accuracy
                "response_mime_type": "application/json"
            }
        )
        
        # Multilingual prompt for Indian market
        prompt = """
        You are an expert AI receipt analyzer for the Indian market.
        Extract ALL information from this receipt into valid JSON.
        
        REQUIREMENTS:
        1. 🇮🇳 INDIAN FOCUS: Handle Hindi, Tamil, Kannada, Telugu text
        2. 💰 CURRENCY: Recognize ₹, INR, Rupees in various formats
        3. 🏪 LOCAL CONTEXT: Indian store chains, GST, UPI payments
        4. 📊 ACCURACY: Extract every item with precise pricing
        
        JSON OUTPUT FORMAT:
        {
          "store_info": {
            "name": "Store Name",
            "date": "YYYY-MM-DD",
            "time": "HH:MM:SS",
            "address": "Full address if visible",
            "receipt_number": "Bill/Receipt number"
          },
          "items": [
            {
              "name": "Item name",
              "quantity": 1.0,
              "unit_price": 100.0,
              "total_price": 100.0,
              "category": "groceries"
            }
          ],
          "totals": {
            "subtotal": 100.0,
            "tax": 18.0,
            "total": 118.0,
            "payment_method": "upi"
          },
          "confidence_score": 95.0
        }
        """
        
        # Process with Vertex AI
        image_part = Part.from_data(
            mime_type="image/jpeg",
            data=base64.b64decode(image_base64)
        )
        
        response = await asyncio.to_thread(
            model.generate_content,
            [prompt, image_part]
        )
        
        # Parse and validate JSON response
        result_data = json.loads(response.text)
        return ProcessingResult(**result_data)
```

## 🗄️ Database Schema

### Firestore Collections (Python Models)

#### **1. Processing Tokens Collection**

```python
# app/models/token.py
class TokenData(BaseModel):
    token: str                                  # Processing token ID
    user_id: str                               # Owner's Firebase UID
    status: ProcessingStatus                   # Current processing state
    
    progress: ProcessingProgress = Field(...)   # Processing progress info
    
    request_data: Dict[str, Any]               # Upload metadata
    result: Optional[ProcessingResult] = None   # Final results
    error: Optional[ProcessingError] = None     # Error details
    
    created_at: datetime
    expires_at: datetime                       # Token expiration (10 min)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

# Collection: processing_tokens
# Document ID: {processing_token}
```

#### **2. Receipts Collection**

```python
# app/models/receipt.py
class ProcessingResult(BaseModel):
    receipt_id: str                            # Unique receipt identifier
    
    store_info: StoreInfo                      # Store details
    items: List[ReceiptItem]                   # Receipt items
    totals: ReceiptTotals                     # Receipt totals
    
    confidence_score: float                    # AI confidence (0-100)
    language_detected: str = "en"             # Detected language
    wallet_pass_url: Optional[str] = None     # Google Wallet pass URL

class StoreInfo(BaseModel):
    name: str                                 # Store name
    address: Optional[str] = None             # Store address
    date: str                                 # Transaction date YYYY-MM-DD
    time: str                                 # Transaction time HH:MM:SS
    receipt_number: Optional[str] = None      # Receipt/bill number

class ReceiptItem(BaseModel):
    name: str                                 # Item name
    quantity: float                           # Item quantity
    unit_price: float                         # Price per unit
    total_price: float                        # Total for this item
    category: Optional[str] = None            # Item category
    warranty_implied: bool = False            # Warranty indication
    subscription_indicator: bool = False       # Subscription indication

# Collection: receipts
# Document ID: {receipt_id}
```

#### **3. Users Collection**

```python
# User Profile Schema
{
    "user_id": str,                           # Firebase UID
    "email": str,                             # User email
    "display_name": str,                      # Display name
    
    "preferences": {
        "currency": "INR",                    # Primary currency
        "language": "en",                     # Preferred language
        "timezone": "Asia/Calcutta",          # User timezone
        "categories": List[str]               # Preferred categories
    },
    
    "gamification": {
        "level": int,                         # User level
        "xp": int,                           # Experience points
        "total_receipts_scanned": int,        # Total receipts processed
        "current_streak": int,                # Consecutive days
        "badges": List[str],                  # Earned badges
        "achievements": List[str]             # Earned achievements
    },
    
    "created_at": datetime,
    "account_status": "active"                # Account status
}

# Collection: users
# Document ID: {user_id}
```

#### **4. Analytics Collection**

```python
# Monthly Analytics Schema
{
    "user_id": str,                          # Owner's Firebase UID
    "month": "2025-07",                      # YYYY-MM format
    
    "total_spent": float,                    # Total spending this month
    "total_receipts": int,                   # Number of receipts
    "average_per_receipt": float,            # Average per receipt
    
    "category_spending": {
        "groceries": {
            "amount": float,                  # Amount spent in category
            "count": int                      # Number of transactions
        },
        # ... other categories
    },
    
    "top_stores": {
        "Store Name": {
            "amount": float,                  # Total spent at store
            "visits": int                     # Number of visits
        }
        # ... other stores
    },
    
    "created_at": datetime,
    "updated_at": datetime
}

# Collection: analytics
# Document ID: {user_id}_{YYYY-MM}
```

### Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null
        && request.auth.uid == userId;
    }
    
    // Processing tokens - owner access only
    match /processing_tokens/{token} {
      allow read, write: if request.auth != null
        && request.auth.uid == resource.data.user_id;
    }
    
    // Receipts - owner access only
    match /receipts/{receiptId} {
      allow read, write: if request.auth != null
        && request.auth.uid == resource.data.user_id;
    }
    
    // Analytics - read-only for owner
    match /analytics/{analyticsId} {
      allow read: if request.auth != null
        && request.auth.uid == resource.data.user_id;
    }
  }
}
```

## 🏠 Local Development

### Python Docker Development Environment

#### **1. Quick Setup**

```bash
# Clone and setup
git clone <your-repo>
cd raseed_backend

# Setup local environment
python scripts/setup_local.py

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f raseed-backend
```

#### **2. Development Services**

```yaml
# docker-compose.yml
version: '3.8'
services:
  # FastAPI Backend
  raseed-backend:
    build:
      context: .
      target: development
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=development
      - FIRESTORE_EMULATOR_HOST=firestore-emulator:8080
      - VERTEX_AI_MOCK_HOST=vertex-ai-mock:8090
    volumes:
      - .:/app
    command: python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

  # Firestore Emulator
  firestore-emulator:
    image: gcr.io/google.com/cloudsdktool/cloud-sdk:latest
    ports:
      - "8080:8080"  # Firestore
      - "4000:4000"  # UI
    command: >
      gcloud emulators firestore start --host-port=0.0.0.0:8080

  # Mock Vertex AI (for local testing)
  vertex-ai-mock:
    build: ./dev-tools/vertex-ai-mock
    ports:
      - "8090:8090"
    environment:
      - MOCK_RESPONSE_DELAY=3000

  # Test Web Interface
  test-interface:
    build: ./dev-tools/test-interface
    ports:
      - "3000:3000"
```

#### **3. Local Testing Commands**

```python
# scripts/test_receipt.py - Manual testing script
import asyncio
import base64
import requests
from pathlib import Path

async def test_receipt_processing():
    """Test complete receipt processing flow"""
    
    # Step 1: Encode test image
    image_path = Path("test-data/receipts/sample_receipt.jpg")
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    # Step 2: Upload receipt
    upload_response = requests.post("http://localhost:8080/api/v1/receipts/upload",
        json={
            "image_base64": image_base64,
            "user_id": "test-user-123",
            "metadata": {"source": "test_script"}
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    if upload_response.status_code == 202:
        token = upload_response.json()["processing_token"]
        print(f"✅ Upload successful! Token: {token}")
        
        # Step 3: Poll for results
        await poll_for_results(token)
    else:
        print(f"❌ Upload failed: {upload_response.text}")

async def poll_for_results(token: str):
    """Poll processing status until completion"""
    import time
    
    for attempt in range(20):  # Max 20 attempts (1 minute)
        response = requests.get(f"http://localhost:8080/api/v1/receipts/status/{token}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Status: {data['status']} ({data['progress']['percentage']}%)")
            
            if data['status'] == 'completed':
                print("🎉 Processing completed!")
                print(f"Receipt ID: {data['result']['receipt_id']}")
                print(f"Confidence: {data['result']['confidence_score']}%")
                return
            elif data['status'] == 'failed':
                print(f"❌ Processing failed: {data['error']['message']}")
                return
        
        await asyncio.sleep(3)  # Wait 3 seconds
    
    print("⏰ Polling timeout")

if __name__ == "__main__":
    asyncio.run(test_receipt_processing())
```

#### **4. Development URLs**

```
🚀 Local Development URLs:
├── FastAPI Backend: http://localhost:8080
├── API Documentation: http://localhost:8080/docs
├── Firestore Emulator UI: http://localhost:4000
├── Test Interface: http://localhost:3000
└── Health Check: http://localhost:8080/api/v1/health
```

## 🚀 Production Deployment

### Google Cloud Run Deployment

#### **1. Automated Deployment Script**

```python
#!/usr/bin/env python3
# scripts/deploy.py
import subprocess
import sys
import os

def deploy_to_production(project_id: str, region: str = "asia-south1"):
    """Deploy Python backend to Google Cloud Run"""
    
    print(f"🚀 Deploying to Cloud Run (Project: {project_id})")
    
    # Step 1: Enable APIs
    apis = [
        "run.googleapis.com",
        "aiplatform.googleapis.com",
        "firestore.googleapis.com"
    ]
    
    for api in apis:
        subprocess.run([
            "gcloud", "services", "enable", api,
            "--project", project_id
        ])
    
    # Step 2: Deploy to Cloud Run
    deploy_cmd = [
        "gcloud", "run", "deploy", "raseed-receipt-processor",
        "--source", ".",
        "--project", project_id,
        "--region", region,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--memory", "4Gi",
        "--cpu", "2",
        "--timeout", "3600",  # 1 hour timeout
        "--max-instances", "100",
        "--min-instances", "2",
        "--set-env-vars", f"GOOGLE_CLOUD_PROJECT={project_id},VERTEX_AI_LOCATION={region}",
    ]
    
    result = subprocess.run(deploy_cmd)
    
    if result.returncode == 0:
        print("✅ Deployment successful!")
        
        # Get service URL
        url_cmd = [
            "gcloud", "run", "services", "describe", "raseed-receipt-processor",
            "--project", project_id, "--region", region,
            "--format", "value(status.url)"
        ]
        
        url_result = subprocess.run(url_cmd, capture_output=True, text=True)
        if url_result.returncode == 0:
            service_url = url_result.stdout.strip()
            print(f"🔗 Service URL: {service_url}")
            print(f"📚 API Docs: {service_url}/docs")
    else:
        print("❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/deploy.py <project-id>")
        sys.exit(1)
    
    deploy_to_production(sys.argv[1])
```

#### **2. Production Configuration**

```python
# app/core/config.py - Production settings
class ProductionSettings(Settings):
    """Production environment settings"""
    
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    
    # Scale settings
    MAX_RETRIES: int = 3
    PROCESSING_TIMEOUT: int = 300
    TOKEN_EXPIRY_MINUTES: int = 10
    
    # Performance settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600
    
    # Security
    ALLOWED_HOSTS: List[str] = [
        "raseed-receipt-processor-*.run.app",
        "api.raseed-app.com"
    ]
    
    @validator("GOOGLE_CLOUD_PROJECT")
    def validate_production_project(cls, v):
        if not v:
            raise ValueError("GOOGLE_CLOUD_PROJECT required in production")
        return v
```

#### **3. CI/CD Pipeline**

```yaml
# cloudbuild.yaml
steps:
  # Python Tests
  - name: 'python:3.11'
    entrypoint: 'bash'
    args:
    - '-c'
    - |
      pip install -r requirements.txt
      pip install pytest pytest-asyncio
      python -m pytest tests/ -v

  # Build & Deploy
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'raseed-receipt-processor'
    - '--source'
    - '.'
    - '--region'
    - 'asia-south1'
    - '--memory'
    - '4Gi'
    - '--timeout'
    - '3600'
    - '--allow-unauthenticated'

timeout: '1200s'
```

## 🧪 Testing Guide

### Python Test Suite

#### **1. Unit Tests**

```python
# tests/test_api/test_receipts.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from main import app

client = TestClient(app)

class TestReceiptUpload:
    @patch('app.services.vertex_ai_service.VertexAIService.process_receipt_image')
    @patch('app.core.security.verify_firebase_token')
    def test_upload_success(self, mock_auth, mock_vertex_ai):
        """Test successful receipt upload"""
        
        # Setup mocks
        mock_auth.return_value = {"uid": "test-user-123"}
        mock_vertex_ai.return_value = Mock()
        
        response = client.post("/api/v1/receipts/upload", json={
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI/hm...",
            "user_id": "test-user-123"
        })
        
        assert response.status_code == 202
        data = response.json()
        assert "processing_token" in data
        assert "estimated_time" in data

    def test_upload_invalid_image(self):
        """Test upload with invalid image"""
        response = client.post("/api/v1/receipts/upload", json={
            "image_base64": "invalid-base64",
            "user_id": "test-user-123"
        })
        
        assert response.status_code == 400
```

#### **2. Integration Tests**

```python
# tests/test_integration/test_full_flow.py
import pytest
import asyncio
from unittest.mock import patch

@pytest.mark.asyncio
class TestFullProcessingFlow:
    async def test_complete_receipt_processing(self):
        """Test end-to-end receipt processing"""
        
        with patch('app.services.vertex_ai_service.VertexAIService') as mock_vertex:
            # Setup mock response
            mock_vertex.return_value.process_receipt_image.return_value = {
                "receipt_id": "test_receipt_123",
                "confidence_score": 95.0,
                "store_info": {"name": "Test Store"},
                "items": [{"name": "Test Item", "total_price": 100.0}],
                "totals": {"total": 100.0}
            }
            
            # Test the flow
            # Upload -> Process -> Status Check -> Results
            # Implementation here...
```

#### **3. Load Tests**

```python
# scripts/load_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_upload(session, user_id: int):
    """Simulate concurrent receipt uploads"""
    
    async with session.post("http://localhost:8080/api/v1/receipts/upload",
        json={
            "image_base64": "test_image_data",
            "user_id": f"load-test-user-{user_id}"
        }) as response:
        
        if response.status == 202:
            token = (await response.json())["processing_token"]
            return await poll_for_completion(session, token)
        return False

async def main():
    """Run load test with 50 concurrent uploads"""
    
    async with aiohttp.ClientSession() as session:
        tasks = [load_test_upload(session, i) for i in range(50)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        successful = sum(1 for r in results if r is True)
        print(f"Completed {successful}/50 uploads in {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 Performance & Monitoring

### Python Monitoring Setup

#### **1. Prometheus Metrics**

```python
# app/utils/monitoring.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
RECEIPT_PROCESSING_COUNTER = Counter(
    'receipt_processing_total',
    'Total receipt processing requests',
    ['status', 'user_type']
)

PROCESSING_TIME_HISTOGRAM = Histogram(
    'receipt_processing_duration_seconds',
    'Receipt processing time',
    ['stage']
)

ACTIVE_TOKENS_GAUGE = Gauge(
    'active_processing_tokens',
    'Number of active processing tokens'
)

class MetricsCollector:
    def record_processing_start(self):
        RECEIPT_PROCESSING_COUNTER.labels(status='started', user_type='regular').inc()
    
    def record_processing_time(self, stage: str, duration: float):
        PROCESSING_TIME_HISTOGRAM.labels(stage=stage).observe(duration)
```

#### **2. Health Monitoring**

```python
# app/api/health.py
from fastapi import APIRouter
from app.utils.monitoring import HealthChecker

router = APIRouter()
health_checker = HealthChecker()

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    return await health_checker.check_health()

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

## 🚀 Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up Google Cloud project and enable required APIs
- [ ] Configure Firestore database and security rules
- [ ] Implement basic authentication with Firebase Auth
- [ ] Create Cloud Storage buckets and lifecycle policies
- [ ] Set up Pub/Sub topics and subscriptions

### Phase 2: Receipt Processing (Week 2)  
- [ ] Implement Vertex AI integration for Gemini processing
- [ ] Create receipt upload and processing pipeline
- [ ] Build Cloud Functions for event-driven processing
- [ ] Implement error handling and retry mechanisms
- [ ] Add support for multiple image formats

### Phase 3: Mobile App Development (Week 3)
- [ ] Create Flutter app with camera integration
- [ ] Implement real-time status updates
- [ ] Build user interface for receipt management
- [ ] Add offline capability and sync
- [ ] Integrate push notifications

### Phase 4: Google Wallet Integration (Week 4)
- [ ] Set up Google Wallet API credentials
- [ ] Implement pass generation and management
- [ ] Create dynamic pass updates
- [ ] Add deep linking support
- [ ] Test wallet pass functionality

### Phase 5: AI Features & Analytics (Week 5)
- [ ] Implement AI-powered insights generation
- [ ] Build analytics dashboard
- [ ] Add subscription detection
- [ ] Create personalized recommendations
- [ ] Implement gamification features

### Phase 6: Testing & Optimization (Week 6)
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Performance optimization and caching
- [ ] Security audit and penetration testing
- [ ] Load testing and scalability validation
- [ ] Documentation and deployment guides

## 🔧 Step-by-Step Setup Guide (Windows)

### Phase 1: Google Cloud Storage Setup

#### **Step 1: Install Google Cloud SDK on Windows**

1. **Download Google Cloud SDK:**
   - Go to: https://cloud.google.com/sdk/docs/install-sdk
   - Download the Windows installer (x64)
   - Run the installer and follow prompts

2. **Initialize gcloud CLI:**
   ```cmd
   # Open Command Prompt or PowerShell as Administrator
   gcloud init
   
   # Follow the prompts to:
   # - Login to your Google account
   # - Select your project ID
   # - Set default region (recommend for India: asia-south1)
   ```

   **🇮🇳 Best Google Cloud Regions for India:**
   - **asia-south1 (Mumbai)** - Primary choice, lowest latency for most of India
   - **asia-south2 (Delhi)** - Alternative option, good for North India
   - **asia-southeast1 (Singapore)** - Backup option if India regions unavailable

   **Why Mumbai (asia-south1) is recommended:**
   - ✅ Lowest latency from India (10-30ms)
   - ✅ Best performance for mobile apps
   - ✅ All Google Cloud services available
   - ✅ Vertex AI and Gemini fully supported
   - ✅ Cost-effective for Indian users

3. **Get Your Project ID:**

   **Option A: From gcloud CLI (if you already have a project):**
   ```cmd
   # List all your projects
   gcloud projects list
   
   # Get current project ID
   gcloud config get-value project
   
   # Example output: my-hackathon-project-2025
   ```

   **Option B: Create a new project for hackathon:**
   ```cmd
   # Create new project (replace with your preferred name)
   gcloud projects create walletarium-raseed-2025 --name="Project Raseed Hackathon"
   
   # Set as active project
   gcloud config set project walletarium-raseed-2025
   
   # Your project ID is: walletarium-raseed-2025
   ```

   **Option C: From Google Cloud Console (Web Interface):**
   - Go to: https://console.cloud.google.com/
   - Click the project dropdown at the top
   - Your project ID is shown next to project name
   - Or create new project: Click "New Project" → Enter name → Note the Project ID

   **Option D: Check what's currently configured:**
   ```cmd
   gcloud config list --format="value(core.project)"
   ```

4. **Verify Installation & Set Project:**
   ```cmd
   gcloud --version
   gcloud auth list
   gcloud config list
   
   # If you need to switch projects:
   gcloud config set project YOUR-ACTUAL-PROJECT-ID
   ```

#### **Step 2: Enable Required APIs**

```cmd
# Enable all necessary Google Cloud APIs
gcloud services enable storage.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firebase.googleapis.com
```

#### **Step 3: Create Storage Buckets**

```cmd
# IMPORTANT: Replace 'your-project-id-here' with your ACTUAL project ID from Step 2
# Example: if your project ID is 'walletarium-raseed-2025', then:
set PROJECT_ID=walletarium-raseed-2025

# Or get it automatically from gcloud:
for /f %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

# Verify your project ID is set correctly
echo Your Project ID is: %PROJECT_ID%

# Create primary staging bucket (where receipts are uploaded) - Mumbai region for India
gsutil mb -p %PROJECT_ID% -c STANDARD -l asia-south1 gs://receipts-staging-bucket-%PROJECT_ID%

# Create archive bucket for long-term storage - Mumbai region
gsutil mb -p %PROJECT_ID% -c NEARLINE -l asia-south1 gs://receipts-archive-bucket-%PROJECT_ID%

# Alternative: Delhi region (if you prefer)
# gsutil mb -p %PROJECT_ID% -c STANDARD -l asia-south2 gs://receipts-staging-bucket-%PROJECT_ID%
# gsutil mb -p %PROJECT_ID% -c NEARLINE -l asia-south2 gs://receipts-archive-bucket-%PROJECT_ID%

# Verify buckets were created
gsutil ls

# Example of what you should see:
# gs://receipts-staging-bucket-walletarium-raseed-2025/
# gs://receipts-archive-bucket-walletarium-raseed-2025/
```

**📋 Quick Project ID Reference:**
- **List all projects:** `gcloud projects list`
- **Get current project:** `gcloud config get-value project`
- **Set project:** `gcloud config set project YOUR-PROJECT-ID`
- **Create new project:** `gcloud projects create PROJECT-NAME`

#### **Step 4: Configure Bucket Permissions & Lifecycle**

1. **Create lifecycle configuration file:**
   
   Create `storage-lifecycle.json`:
   ```json
   {
     "lifecycle": {
       "rule": [
         {
           "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
           "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]}
         },
         {
           "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
           "condition": {"age": 90, "matchesStorageClass": ["NEARLINE"]}
         },
         {
           "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
           "condition": {"age": 365, "matchesStorageClass": ["COLDLINE"]}
         },
         {
           "action": {"type": "Delete"},
           "condition": {"age": 1, "matchesPathPattern": "**/temp/**"}
         }
       ]
     }
   }
   ```

2. **Apply lifecycle policy:**
   ```cmd
   gsutil lifecycle set storage-lifecycle.json gs://receipts-staging-bucket-%PROJECT_ID%
   ```

#### **Step 5: Set Up Bucket Structure**

```cmd
# Create initial folder structure (these are just markers - folders are created automatically when files are uploaded)
echo. > temp-marker.txt

# Create test user folder structure
gsutil cp temp-marker.txt gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/original/
gsutil cp temp-marker.txt gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/processed/
gsutil cp temp-marker.txt gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/thumbnails/

# Clean up temp file
del temp-marker.txt
gsutil rm gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/original/temp-marker.txt
gsutil rm gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/processed/temp-marker.txt
gsutil rm gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/thumbnails/temp-marker.txt
```

#### **Step 6: Configure CORS for Web Access (Optional)**

Create `cors-config.json`:
```json
[
  {
    "origin": ["*"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type", "Access-Control-Allow-Origin"],
    "maxAgeSeconds": 3600
  }
]
```

```cmd
gsutil cors set cors-config.json gs://receipts-staging-bucket-%PROJECT_ID%
```

#### **Step 7: Test Storage Setup**

1. **Create a test receipt image** (any .jpg/.png file)

2. **Upload test receipt:**
   ```cmd
   # Upload a test image (replace 'test-receipt.jpg' with your actual file)
   gsutil cp test-receipt.jpg gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/original/

   # Verify upload
   gsutil ls gs://receipts-staging-bucket-%PROJECT_ID%/users/test-user-123/receipts/2025/07/original/
   ```

3. **Check bucket details:**
   ```cmd
   gsutil du -sh gs://receipts-staging-bucket-%PROJECT_ID%
   gsutil lifecycle get gs://receipts-staging-bucket-%PROJECT_ID%
   ```

#### **Step 8: Set Up Monitoring & Notifications**

```cmd
# Create a Pub/Sub topic for storage notifications (we'll use this later)
gcloud pubsub topics create receipt-uploaded

# Add storage notification (this will trigger when files are uploaded)
gsutil notification create -t receipt-uploaded -f json gs://receipts-staging-bucket-%PROJECT_ID%
```

#### **Windows-Specific Tips:**

1. **Use PowerShell for better command support:**
   ```powershell
   # PowerShell equivalent for environment variables
   $env:PROJECT_ID = "your-project-id-here"
   gsutil mb -p $env:PROJECT_ID -c STANDARD -l us-central1 gs://receipts-staging-bucket-$env:PROJECT_ID
   ```

2. **Create batch script for repeated testing:**
   
   Create `test-upload.bat`:
   ```batch
   @echo off
   set PROJECT_ID=your-project-id-here
   set BUCKET=receipts-staging-bucket-%PROJECT_ID%
   set USER_ID=test-user-123
   
   echo Uploading test receipt...
   gsutil cp %1 gs://%BUCKET%/users/%USER_ID%/receipts/2025/07/original/test_receipt_%time:~0,2%%time:~3,2%%time:~6,2%.jpg
   
   echo Upload complete! Checking bucket...
   gsutil ls gs://%BUCKET%/users/%USER_ID%/receipts/2025/07/original/
   ```

   **Usage:**
   ```cmd
   test-upload.bat my-receipt.jpg
   ```

#### **Verification Checklist:**

- [ ] Google Cloud SDK installed and authenticated
- [ ] Required APIs enabled
- [ ] Storage buckets created with lifecycle policies
- [ ] Folder structure established
- [ ] Pub/Sub topic created for notifications
- [ ] Test upload successful
- [ ] Monitoring notifications configured

#### **Next Steps:**

Once storage is set up, we'll move to:
1. **Firestore Database Setup**
2. **Cloud Functions for Processing**
3. **Vertex AI Integration**
4. **Google Wallet API Configuration**

**Current Status:** ✅ Google Cloud Storage configured and ready for receipt uploads!

---

## 🔧 Complete Deployment Guide

### Prerequisites

1. **Google Cloud Setup:**
   ```bash
   gcloud auth login
   gcloud config set project your-project-id
   gcloud services enable \
     storage.googleapis.com \
     firestore.googleapis.com \
     cloudfunctions.googleapis.com \
     run.googleapis.com \
     aiplatform.googleapis.com \
     pubsub.googleapis.com
   ```

2. **Firebase Setup:**
   ```bash
   npm install -g firebase-tools
   firebase login
   firebase init
   ```

### Deployment Steps

1. **Deploy Cloud Functions:**
   ```bash
   firebase deploy --only functions
   ```

2. **Deploy Cloud Run Services:**
   ```bash
   gcloud run deploy receipt-api-service \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Configure Firestore:**
   ```bash
   firebase deploy --only firestore
   ```

4. **Set up monitoring:**
   ```bash
   gcloud logging sinks create raseed-sink \
     bigquery.googleapis.com/projects/your-project/datasets/logs
   ```

### Environment Configuration

```yaml
# .env.production
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_EMULATOR_HOST=localhost:8080
STORAGE_EMULATOR_HOST=localhost:9199
PUBSUB_EMULATOR_HOST=localhost:8085

# Vertex AI
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash-002

# Google Wallet
GOOGLE_WALLET_ISSUER_ID=your-issuer-id
GOOGLE_WALLET_AUDIENCE=your-audience

# Firebase
FIREBASE_PROJECT_ID=your-firebase-project
```

## 🧪 Complete Testing Guide

### 🚀 **Testing Your Receipt Image: `miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg`**

You have multiple ways to test your enhanced Gemini 2.5 Flash receipt analysis system. Here's every option:

---

## **Method 1: Quick CLI Test with Your Real Receipt**

### **Step 1: Use the Real Receipt Script**

```bash
# Test with your specific receipt image
cd scripts
python test_real_receipt.py "../docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg"
```

**Expected Output:**
```
📸 Analyzing Real Receipt: ../docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg
==================================================
1. Converting image to base64...
   ✅ Image converted: 2.34 MB
2. Uploading receipt...
   ✅ Upload successful - Token: proc_1721934567_abc123def
3. Processing receipt with Gemini 2.5 Flash...
   Polling... 1/30
   Status: processing - analysis (30.0%)
   Polling... 2/30
   Status: processing - analysis (60.0%)
   Polling... 3/30
   Status: completed - completed (100.0%)

🎉 Analysis Completed!

📊 Receipt Analysis Results:
🏪 Store: El Chalan Restaurant
💰 Total Amount: $47.85
📂 Category: Dining
📝 Description: 8 items from El Chalan Restaurant
📅 Transaction Time: 2024-01-15T19:30:00Z
💳 Transaction Type: debit
⭐ Importance: medium
🔄 Recurring: false
🛡️ Warranty: false

💾 Full analysis saved to: real_receipt_result_miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.json
```

---

## **Method 2: Postman API Testing** ⭐ **(Recommended for Development)**

### **Step A: Install Postman**
1. Download from: https://www.postman.com/downloads/
2. Install and create free account
3. Open Postman desktop app

### **Step B: Create New Collection**
1. Click **"New" → "Collection"**
2. Name it: **"Raseed Receipt Analysis API"**
3. Save the collection

### **Step C: Set Environment Variables**
1. Click **gear icon** (⚙️) → **"Manage Environments"**
2. Click **"Add"** → Create **"Local Development"**
3. Add variables:
   ```
   Variable: base_url
   Initial Value: http://localhost:8080
   Current Value: http://localhost:8080
   
   Variable: api_version
   Initial Value: /api/v1
   Current Value: /api/v1
   ```
4. **Save** and **select** the environment

### **Step D: Create Receipt Upload Request**

1. **In your collection, click "Add Request"**
2. **Name it:** `Upload Receipt - Real Image Test`
3. **Configure the request:**

   **Method:** `POST`
   
   **URL:** `{{base_url}}{{api_version}}/receipts/upload`
   
   **Headers:**
   ```
   Content-Type: application/json
   ```
   
   **Body (select "raw" and "JSON"):**
   ```json
   {
     "image_base64": "{{receipt_base64}}",
     "user_id": "postman_test_user_123",
     "metadata": {
       "source": "postman_test",
       "filename": "miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg",
       "test": true,
       "timestamp": "{{$timestamp}}"
     }
   }
   ```

### **Step E: Convert Your Receipt to Base64**

**Option E1: Using Python (Recommended):**
```bash
# Create a quick base64 converter script
cd scripts
python -c "
import base64
with open('../docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg', 'rb') as f:
    data = base64.b64encode(f.read()).decode('utf-8')
    print('Base64 length:', len(data))
    with open('receipt_base64.txt', 'w') as out:
        out.write(data)
    print('Base64 saved to: receipt_base64.txt')
"
```

**Option E2: Using Online Converter:**
1. Go to: https://base64.guru/converter/encode/image
2. Upload your receipt image
3. Copy the base64 string (without `data:image/jpeg;base64,` prefix)

### **Step F: Add Base64 to Postman**
1. **Copy the base64 string** from `receipt_base64.txt`
2. **In Postman**, go to **Environment Variables**
3. **Add new variable:**
   ```
   Variable: receipt_base64
   Initial Value: [paste your base64 string here]
   Current Value: [paste your base64 string here]
   ```
4. **Save** the environment

### **Step G: Create Status Check Request**

1. **Add another request** to your collection
2. **Name it:** `Check Receipt Status`
3. **Configure:**

   **Method:** `GET`
   
   **URL:** `{{base_url}}{{api_version}}/receipts/status/{{processing_token}}`
   
   **No body needed**

### **Step H: Execute the Test Flow**

1. **Run Upload Request:**
   - Click **"Send"** on the upload request
   - **Expected Response (Status 200):**
     ```json
     {
       "processing_token": "proc_1721934567_abc123def",
       "estimated_time": 30,
       "status": "uploaded",
       "message": "Receipt uploaded successfully, processing started"
     }
     ```

2. **Copy the token** from response

3. **Add token to environment:**
   ```
   Variable: processing_token
   Current Value: [paste token here]
   ```

4. **Poll Status Every 3 Seconds:**
   - Click **"Send"** on status check request
   - **Repeat until status = "completed"**

### **Step I: Advanced Postman Features**

**Create Test Scripts (add to Upload Request → "Tests" tab):**
```javascript
// Auto-extract token and save to environment
pm.test("Upload successful", function () {
    pm.response.to.have.status(200);
    
    const response = pm.response.json();
    pm.expect(response).to.have.property('processing_token');
    
    // Save token for next request
    pm.environment.set("processing_token", response.processing_token);
    console.log("Token saved:", response.processing_token);
});
```

**Create Pre-request Script for Status Check:**
```javascript
// Auto-delay for polling
setTimeout(function(){}, 3000); // 3 second delay
```

---

## **Method 3: Browser Interactive Testing** 🌐

### **FastAPI Swagger UI (Easiest for Quick Tests)**

1. **Open browser:** http://localhost:8080/docs
2. **Click on:** `POST /api/v1/receipts/upload`
3. **Click:** "Try it out"
4. **Fill in the request body:**
   ```json
   {
     "image_base64": "[paste your base64 string here]",
     "user_id": "browser_test_user",
     "metadata": {}
   }
   ```
5. **Click:** "Execute"
6. **Copy the token** from response
7. **Go to:** `GET /api/v1/receipts/status/{token}`
8. **Paste token** and click "Execute"
9. **Repeat step 8** until status = "completed"

---

## **Method 4: Complete API Test Suite**

### **Run All Tests:**
```bash
# 1. Test health endpoints
python scripts/test_api.py

# 2. Test with your real receipt
python scripts/test_real_receipt.py "docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg"

# 3. Test core Vertex AI service
python scripts/test_enhanced_receipt.py
```

---

## **Method 5: Advanced Development Testing**

### **Load Testing with Real Receipt:**

Create `scripts/load_test_real.py`:
```python
import asyncio
import aiohttp
import base64
from pathlib import Path

async def load_test_with_real_receipt():
    """Load test with your actual receipt image"""
    
    # Read your receipt
    image_path = Path("../docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg")
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    async with aiohttp.ClientSession() as session:
        # Test 10 concurrent uploads of the same receipt
        tasks = []
        for i in range(10):
            tasks.append(upload_receipt(session, image_base64, f"load_test_user_{i}"))
        
        results = await asyncio.gather(*tasks)
        successful = sum(1 for r in results if r is True)
        print(f"Load test completed: {successful}/10 successful")

async def upload_receipt(session, image_base64, user_id):
    """Upload receipt and poll for completion"""
    try:
        # Upload
        async with session.post("http://localhost:8080/api/v1/receipts/upload",
            json={
                "image_base64": image_base64,
                "user_id": user_id,
                "metadata": {"test": "load_test"}
            }) as response:
            
            if response.status != 200:
                return False
            
            data = await response.json()
            token = data["processing_token"]
            
            # Poll for completion (simplified)
            for _ in range(20):  # Max 1 minute
                await asyncio.sleep(3)
                
                async with session.get(f"http://localhost:8080/api/v1/receipts/status/{token}") as status_response:
                    if status_response.status == 200:
                        status_data = await status_response.json()
                        if status_data["status"] == "completed":
                            return True
                        elif status_data["status"] == "failed":
                            return False
            
            return False  # Timeout
            
    except Exception as e:
        print(f"Error for {user_id}: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(load_test_with_real_receipt())
```

**Run load test:**
```bash
python scripts/load_test_real.py
```

---

## **Method 6: cURL Testing (Command Line)**

### **Upload Receipt:**
```bash
# First, convert image to base64 (one-liner)
export RECEIPT_BASE64=$(base64 -w 0 "docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg")

# Upload via cURL
curl -X POST "http://localhost:8080/api/v1/receipts/upload" \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$RECEIPT_BASE64\",
    \"user_id\": \"curl_test_user\",
    \"metadata\": {
      \"source\": \"curl_test\",
      \"filename\": \"miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg\"
    }
  }" | jq .

# Save the token from response, then check status
export TOKEN="proc_1721934567_abc123def"  # Replace with actual token

# Poll status
curl "http://localhost:8080/api/v1/receipts/status/$TOKEN" | jq .
```

---

## **🔍 What to Expect from Your Receipt Analysis**

### **Your Receipt (`miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg`) Should Extract:**

```json
{
  "store_info": {
    "name": "El Chalan Restaurant",
    "address": "Miami, Florida",
    "date": "2024-XX-XX",
    "time": "XX:XX",
    "receipt_number": "FWREE7"
  },
  "items": [
    {
      "name": "Peruvian Dish 1",
      "quantity": 1,
      "unit_price": 15.99,
      "total_price": 15.99,
      "category": "food"
    },
    // ... more items
  ],
  "totals": {
    "subtotal": 45.67,
    "tax": 3.65,
    "total": 49.32,
    "payment_method": "card"
  },
  "confidence": "high",
  "processing_metadata": {
    "model_version": "gemini-2.5-flash",
    "items_count": 5,
    "retry_count": 0
  }
}
```

---

## **🛠️ Troubleshooting Guide**

### **Common Issues & Solutions:**

| **Issue** | **Symptom** | **Solution** |
|-----------|-------------|--------------|
| **Server not running** | Connection refused | Run `python -m uvicorn main:app --host 0.0.0.0 --port 8080` |
| **Image too large** | Upload fails with 400 | Compress image or check 10MB limit |
| **Processing timeout** | Stuck at "processing" | Check Vertex AI service logs |
| **Invalid base64** | Upload fails with 400 | Re-encode image, remove data URL prefix |
| **Postman variables not working** | 404 errors | Check environment is selected |

### **Debugging Commands:**

```bash
# Check server health
curl http://localhost:8080/api/v1/health

# Check detailed service health
curl http://localhost:8080/api/v1/health/services

# View server logs
# (Check the terminal where uvicorn is running)

# Test with minimal image
python -c "
import base64
from PIL import Image
img = Image.new('RGB', (100, 100), color='white')
img.save('test_minimal.jpg')
with open('test_minimal.jpg', 'rb') as f:
    print(base64.b64encode(f.read()).decode()[:100] + '...')
"
```

---

## **📊 Performance Benchmarks**

### **Expected Performance with Your Receipt:**

- **Upload Response:** < 2 seconds
- **Processing Time:** 10-30 seconds
- **Total Time:** 15-35 seconds
- **Confidence Score:** 85-95%
- **Items Extracted:** 5-15 items
- **Accuracy:** 90-95% for clear receipts

### **Testing Performance:**

```bash
# Time the complete flow
time python scripts/test_real_receipt.py "docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg"

# Memory usage monitoring
python -c "
import psutil
import time
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

---

## **🎯 Quick Start Testing Checklist**

**For Your Specific Receipt:**

- [ ] **Server Running:** `python -m uvicorn main:app --host 0.0.0.0 --port 8080`
- [ ] **Health Check:** Visit http://localhost:8080/api/v1/health
- [ ] **Test Method 1:** CLI script with your receipt
- [ ] **Test Method 2:** Postman setup and execution
- [ ] **Test Method 3:** Browser Swagger UI test
- [ ] **Verify Results:** Check extracted items and totals
- [ ] **Performance Check:** Ensure processing < 30 seconds

**Recommended Testing Order:**
1. 🚀 **Start here:** Browser Swagger UI (Method 3)
2. 🔧 **For development:** Postman setup (Method 2)  
3. 📊 **For automation:** CLI scripts (Method 1)
4. ⚡ **For performance:** Load testing (Method 5)

---

## **💡 Pro Tips for Testing**

### **Image Quality Tips:**
- ✅ **Best results:** Clear, well-lit photos
- ✅ **Good:** Slight angles okay
- ⚠️ **Avoid:** Very blurry or dark images
- ⚠️ **Avoid:** Heavily wrinkled receipts

### **Development Workflow:**
1. **Use Postman** for interactive development
2. **Use CLI scripts** for automated testing  
3. **Use browser** for quick verification
4. **Use load tests** for performance validation

### **Debugging Workflow:**
1. **Check health endpoints** first
2. **Test with simple synthetic receipt** 
3. **Then test with your real receipt**
4. **Monitor server logs** for errors

---

Your enhanced Gemini 2.5 Flash system is now ready for comprehensive testing! 🎉

Choose your preferred testing method and start analyzing your Peruvian restaurant receipt! 🇵🇪🍽️
