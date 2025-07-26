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

## 🧪 Manual Testing & Development

### Testing Pipeline Without Frontend

The event-driven architecture allows you to test the entire processing pipeline by manually uploading files to Cloud Storage. The system will automatically detect uploads and trigger the complete processing flow.

#### **1. Manual Upload via gcloud CLI:**

```bash
# Upload a receipt image manually to trigger the pipeline
gsutil cp receipt-sample.jpg gs://receipts-staging-bucket/users/test-user-123/receipts/2025/07/original/

# The system will automatically:
# 1. Detect the upload via Storage Trigger
# 2. Extract userId from path: 'test-user-123'
# 3. Generate receiptId and publish to Pub/Sub
# 4. Process with Vertex AI Gemini
# 5. Save results to Firestore
# 6. Generate Google Wallet pass
# 7. Send notifications
```

#### **2. Required File Path Structure:**

```yaml
# Critical: Follow this exact path structure for automatic processing
Path Format: /users/{userId}/receipts/{year}/{month}/original/{filename}

Examples:
✅ CORRECT: users/test-user-123/receipts/2025/07/original/receipt_001.jpg
✅ CORRECT: users/demo-user/receipts/2025/07/original/my-receipt.png
❌ WRONG: receipts/receipt.jpg (missing user structure)
❌ WRONG: users/test-user/receipt.jpg (missing year/month/original)
```

#### **3. Batch Testing Script:**

```bash
#!/bin/bash
# test-pipeline.sh - Batch upload multiple receipts for testing

USER_ID="test-user-123"
BUCKET="receipts-staging-bucket"
YEAR=$(date +%Y)
MONTH=$(date +%m)

# Upload multiple test receipts
for i in {1..5}; do
  echo "Uploading test receipt $i..."
  gsutil cp "test-receipts/receipt_$i.jpg" \
    "gs://$BUCKET/users/$USER_ID/receipts/$YEAR/$MONTH/original/test_receipt_$(date +%s)_$i.jpg"
  
  echo "Uploaded - Processing should start automatically..."
  sleep 2
done

echo "All test receipts uploaded! Check Firestore and logs for processing results."
```

#### **4. Monitoring Pipeline Execution:**

```bash
# Watch Cloud Function logs in real-time
gcloud functions logs read receiptUploadTrigger --follow

# Check Pub/Sub message processing
gcloud pubsub topics list-subscriptions receipt-uploaded

# Monitor Vertex AI processing
gcloud ai custom-jobs list --region=us-central1

# Check Firestore for processed results
firebase firestore:get receipts --where userId==test-user-123
```

#### **5. Test Data Validation:**

```typescript
// Create test user in Firestore first (run once)
const testUser = {
  userId: 'test-user-123',
  email: 'test@example.com',
  displayName: 'Test User',
  preferences: {
    currency: 'INR',
    language: 'en',
    categories: ['food', 'transport', 'shopping']
  },
  createdAt: admin.firestore.FieldValue.serverTimestamp()
};

await admin.firestore().collection('users').doc('test-user-123').set(testUser);
```

#### **6. Manual Upload via Google Cloud Console:**

1. **Go to Cloud Storage Console**
2. **Navigate to `receipts-staging-bucket`**
3. **Create folder structure**: `users/test-user-123/receipts/2025/07/original/`
4. **Upload receipt images** directly into the `original/` folder
5. **Pipeline triggers automatically** - no additional action needed!

#### **7. Verify Processing Results:**

```bash
# Check if receipt was processed successfully
firebase firestore:get receipts --where userId==test-user-123 --limit 1

# Expected output:
{
  "receiptId": "receipt_1721934567_abc123",
  "userId": "test-user-123",
  "processingStatus": "completed",
  "confidenceScore": 95,
  "storeInfo": { "name": "Store Name", ... },
  "items": [ { "name": "Item 1", ... } ],
  "totals": { "total": 42.50 },
  "aiInsights": { ... }
}
```

#### **8. Debug Common Issues:**

```yaml
Issue: "No userId extracted from path"
Solution: Ensure path follows exact format: users/{userId}/receipts/{year}/{month}/original/

Issue: "Processing stuck in 'uploaded' status"
Solution: Check Cloud Function logs - may be Vertex AI API issue

Issue: "No Google Wallet pass generated"
Solution: Verify Google Wallet API credentials are configured

Issue: "Firestore security rules blocking writes"
Solution: Temporarily allow admin writes for testing:
  allow write: if true; // FOR TESTING ONLY
```

#### **9. Frontend-Free Testing Workflow:**

```bash
# 1. Deploy backend infrastructure
firebase deploy --only functions,firestore

# 2. Create test user data
node scripts/create-test-user.js

# 3. Upload test receipts
./test-pipeline.sh

# 4. Verify processing results
firebase firestore:get receipts --where userId==test-user-123

# 5. Check Google Wallet passes generated
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://walletobjects.googleapis.com/walletobjects/v1/genericObject/your-issuer-id.receipt_*"
```

### **Key Advantages of Manual Testing:**

✅ **No Frontend Dependency** - Test backend immediately
✅ **Batch Processing** - Upload multiple receipts simultaneously
✅ **Rapid Iteration** - Quick testing of AI prompt changes
✅ **Pipeline Validation** - Verify entire flow end-to-end
✅ **Performance Testing** - Measure processing times
✅ **Error Debugging** - Isolate backend issues from frontend

---

## 📞 Support & Contributing

**Built for Google Cloud Agentic AI Hackathon by Team Walletarium Imperium**

- **Documentation**: Comprehensive API docs and integration guides
- **Support**: Dedicated support for hackathon participants
- **Community**: Join discussions about AI-powered financial tools

### Team Expertise
- **GenAI Specialist**: Advanced Vertex AI and Gemini integration
- **Computer Vision Expert**: Multimodal processing and optimization  
- **Mobile App Developer**: Flutter and cross-platform development

---

*This architecture is designed to be production-ready, scalable, and optimized for the Google Cloud ecosystem while delivering innovative AI-powered financial intelligence.*
