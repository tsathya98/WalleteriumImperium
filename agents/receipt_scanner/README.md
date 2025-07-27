# 🧾 Simple Receipt Scanner API

A simple AI-powered receipt scanning service that accepts receipt images via REST API and returns structured data.

## ✨ Features

- **Single REST Endpoint**: Upload receipt and get analysis immediately
- **Multipart Form Data**: Standard file upload via HTTP
- **Simple JSON Response**: Easy to parse structured data
- **Image & Video Support**: Process receipt images and videos
- **Gemini AI Powered**: Uses Google's Gemini Vision AI for accurate extraction

## 🚀 API Usage

### Upload Receipt

**Endpoint:** `POST /api/receipts/upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file`: Receipt image or video file (jpg, png, mp4, etc.)
- `user_id`: User identifier

**Example with curl:**
```bash
curl -X POST \
  -F "file=@receipt.jpg" \
  -F "user_id=user123" \
  http://localhost:8000/api/receipts/upload
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "receipt_id": "d2116b7d-2edb-46f6-b2ee-9f2b0ba8c270",
    "place": "El Chalan Restaurant", 
    "time": "2016-03-12T13:13:00Z",
    "amount": 49.52,
    "transactionType": "debit",
    "category": "Restaurant, fast-food",
    "description": "Peruvian dinner for 2",
    "items": [
      {
        "name": "Ceviche",
        "quantity": 1,
        "unit_price": 15.00,
        "total_price": 15.00,
        "category": "Restaurant, fast-food"
      }
    ],
    "metadata": {
      "vendor_type": "RESTAURANT",
      "confidence": "high",
      "processing_time_seconds": 2.5,
      "model_version": "gemini-2.5-flash"
    }
  },
  "processing_time": 2.5
}
```

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Google Cloud Project with Vertex AI enabled
- Service account credentials

### Environment Variables
```bash
GOOGLE_CLOUD_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
```

### Installation
```bash
pip install -r requirements.txt
```

## 📁 File Structure

```
receipt_scanner/
├── agent.py          # Main AI agent 
├── prompts.py        # AI prompts
├── requirements.txt  # Dependencies
└── README.md        # This file
```

## 🎯 Design Principles

- **Keep It Simple**: One endpoint, direct response
- **REST First**: Standard HTTP multipart uploads
- **No Complexity**: No tokens, polling, or extra APIs
- **Fast**: Immediate response with results
