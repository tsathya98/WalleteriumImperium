# 🧾 Multimodal Receipt Scanner Agent

A comprehensive AI-powered receipt processing agent that supports **text, Excel, PDF, image, and video inputs** using Google's Agent Development Kit (ADK), Gemini 2.5 Flash for vision AI, and LLM enrichment for structured data extraction. Features robust JSON output with MCP compatibility, local storage, search, analytics, and export capabilities.

## 🌟 Features

### 📁 **Multimodal Input Support**
- **🖼️ Images** (JPG, PNG, GIF, BMP, TIFF, WebP) - Gemini 2.5 Flash Vision AI
- **🎥 Videos** (MP4, AVI, MOV, WMV, FLV, WebM, MKV) - Frame extraction + Vision AI
- **📄 PDF Documents** - OCR text extraction + LLM enrichment
- **📊 Excel/CSV Files** - Structured data processing + LLM categorization
- **📝 Text Files** - Pattern matching + LLM enrichment

### 🤖 **Advanced AI Processing**
- **Gemini 2.5 Flash** for image and video analysis with high accuracy
- **LLM Enrichment** for text-based inputs with automatic categorization
- **Confidence Scoring** for all extracted data elements
- **Smart Categorization** with 10+ predefined categories (food, electronics, etc.)

### 📋 **Robust JSON Output**
- **MCP-Compatible Structure** for seamless agent-to-agent communication
- **Complete Receipt Information**: store details, transaction info, itemized list
- **Financial Accuracy**: subtotals, taxes, discounts, payment methods
- **Metadata Tracking**: processing timestamps, confidence scores, source info
- **Warranty & Return Policies**: automatic detection and expiry calculation

### 💾 **Local Storage & Analytics**
- **JSON + SQLite Storage** for performance and reliability
- **Advanced Search** by store, category, date, amount, or text query
- **Analytics Dashboard** with spending insights and statistics
- **Export Capabilities** to JSON and CSV formats
- **User Tagging** for custom organization and categorization

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Google ADK** - Agent Development Kit
3. **Google API Key** for Gemini AI
4. **Required Dependencies** (see requirements.txt)

### Installation

```bash
# Navigate to the receipt scanner directory
cd receipt_scanner/

# Install dependencies
pip install -r requirements.txt

# Set up your Google API key
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

### ADK Web Interface (Recommended)

```bash
# Start the ADK web interface
adk web

# Open the provided URL in your browser (usually http://localhost:8080)
# Features available:
# - 📁 Upload any supported file type
# - 🤖 Automatic processing with appropriate AI model
# - 📊 Real-time receipt processing results
# - 💾 Automatic local storage
# - 🔍 Search and analytics interface
```

## 📖 Detailed Usage

### 1. **Image Receipt Processing**

Upload any receipt image and get comprehensive extraction:

```python
from agent import process_multimodal_receipt

# Process an image receipt
result = await process_multimodal_receipt(
    file_data="receipt_photo.jpg",
    filename="receipt_photo.jpg",
    store_receipt=True,
    user_tags=["grocery", "weekly-shopping"],
    user_category="Food & Groceries"
)

# Access structured data
if result["status"] == "success":
    receipt_data = result["receipt_data"]
    store_name = receipt_data["receipt_payload"]["store_details"]["name"]
    total = receipt_data["receipt_payload"]["payment_summary"]["total_amount"]
    items = receipt_data["receipt_payload"]["line_items"]

    print(f"Store: {store_name}")
    print(f"Total: ${total}")
    print(f"Items: {len(items)}")
```

### 2. **PDF Receipt Processing**

Process scanned or digital PDF receipts:

```python
# Process PDF receipt with OCR + LLM enrichment
result = await process_multimodal_receipt(
    file_data="invoice.pdf",
    filename="invoice.pdf",
    store_receipt=True,
    user_tags=["business", "office-supplies"],
    user_category="Business Expenses"
)

# PDF processing includes text extraction and smart categorization
```

### 3. **Excel/CSV Processing**

Handle structured expense data:

```python
# Process Excel expense report
result = await process_multimodal_receipt(
    file_data="expenses.xlsx",
    filename="expenses.xlsx",
    store_receipt=True,
    user_tags=["quarterly", "travel"],
    user_category="Travel Expenses"
)

# Excel processing provides high confidence due to structured data
```

### 4. **Video Receipt Processing**

Extract receipts from video recordings:

```python
# Process video of receipt (extracts best frames)
result = await process_multimodal_receipt(
    file_data="receipt_video.mp4",
    filename="receipt_video.mp4",
    store_receipt=True,
    user_tags=["mobile-capture", "restaurant"],
    user_category="Dining Out"
)

# Video processing automatically extracts and analyzes frames
```

### 5. **Text Receipt Processing**

Handle manual text entry or OCR output:

```python
# Process plain text receipt data
text_receipt = """
GROCERY STORE RECEIPT
Store: SuperMart
Date: 2025-01-20
Items:
- Milk: $3.99
- Bread: $2.49
- Bananas: $3.87
Total: $15.49
"""

result = await process_multimodal_receipt(
    file_data=text_receipt.encode('utf-8'),
    filename="manual_receipt.txt",
    store_receipt=True,
    user_tags=["manual-entry"],
    user_category="Groceries"
)
```

## 🔍 Search & Analytics

### Search Stored Receipts

```python
from agent import search_stored_receipts

# Search by text query
results = await search_stored_receipts(
    query="SuperMart",
    filters={"store_name": "SuperMart"},
    limit=10
)

# Search by category and date range
results = await search_stored_receipts(
    query="grocery",
    filters={
        "category": "Groceries",
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "min_amount": 10.00
    }
)
```

### Get Analytics

```python
from agent import get_storage_statistics

# Get comprehensive statistics
stats = await get_storage_statistics()

print(f"Total receipts: {stats['statistics']['total_receipts']}")
print(f"Total spending: ${stats['statistics']['total_spending']}")
print(f"By category: {stats['statistics']['by_category']}")
print(f"By store: {stats['statistics']['by_store']}")
```

### Export Data

```python
from agent import export_receipts

# Export all receipts to JSON
export_file = await export_receipts(format="json")

# Export specific receipts to CSV
export_file = await export_receipts(
    format="csv",
    receipt_ids=["receipt-abc123", "receipt-def456"]
)
```

## 📊 JSON Output Structure

The agent produces comprehensive, MCP-compatible JSON output:

```json
{
  "mcp_format": {
    "protocol_version": "1.0",
    "data_type": "processed_receipt",
    "status": "success",
    "timestamp_utc": "2025-01-20T10:00:00Z",
    "agent_id": "multimodal_receipt_scanner",
    "confidence_score": 0.95
  },
  "receipt_payload": {
    "processing_metadata": {
      "receipt_id": "receipt-abc123",
      "source_filename": "receipt.jpg",
      "source_type": "image",
      "processor_model": "gemini-2.5-flash",
      "processing_duration_ms": 2500
    },
    "store_details": {
      "name": "Tech World Electronics",
      "address": "123 Silicon Valley Blvd, San Jose, CA",
      "phone_number": "(408) 555-0123",
      "confidence_score": 0.98
    },
    "transaction_details": {
      "date": "2025-01-20",
      "time": "15:45:22",
      "currency": "USD",
      "transaction_id": "TXN-123456"
    },
    "line_items": [
      {
        "description": "Wireless Mouse - Logitech MX Master 3",
        "quantity": 1.0,
        "unit_price": 99.99,
        "total_price": 99.99,
        "category": "electronics",
        "confidence_score": 0.97,
        "tax_details": {
          "tax_amount": 8.25,
          "tax_rate": 8.25
        }
      }
    ],
    "payment_summary": {
      "subtotal": 222.95,
      "total_tax_amount": 19.95,
      "total_amount": 242.90
    },
    "payment_method": {
      "method": "Credit Card",
      "card_type": "Visa",
      "last_4_digits": "4567"
    },
    "special_info": {
      "warranty": {
        "is_applicable": true,
        "duration_days": 365,
        "expiry_date": "2026-01-20"
      },
      "return_policy": {
        "is_returnable": true,
        "duration_days": 30,
        "return_deadline": "2025-02-19"
      }
    }
  }
}
```

## 🛠️ System Architecture

```
Multimodal Receipt Scanner
├── 📁 Input Processing
│   ├── 🖼️  Image Processor (PIL, OpenCV)
│   ├── 🎥  Video Processor (OpenCV, frame extraction)
│   ├── 📄  PDF Processor (PyMuPDF/fitz)
│   ├── 📊  Excel Processor (pandas, openpyxl)
│   └── 📝  Text Processor (regex, NLP)
├── 🤖 AI Processing
│   ├── 🔮  Gemini 2.5 Flash (images, videos)
│   └── 🧠  LLM Enrichment (text, PDF, Excel)
├── 💾 Storage System
│   ├── 📄  JSON Storage (primary)
│   ├── 🗄️  SQLite Index (search performance)
│   └── 🔍  Search & Analytics Engine
└── 📋 Output Generation
    ├── 🏷️  MCP Format Compliance
    ├── ✅  Data Validation (Pydantic)
    └── 📊  Export Capabilities
```

## 🔧 Configuration & Setup

### Environment Variables

```bash
# Required: Google Gemini API Key
export GOOGLE_API_KEY="your_api_key_here"

# Optional: Custom storage location
export RECEIPT_STORAGE_DIR="/path/to/storage"

# Optional: Model selection
export GEMINI_MODEL="gemini-2.5-flash"
```

### System Validation

```python
from agent import validate_system_setup

# Check system readiness
validation = await validate_system_setup()

if validation["system_ready"]:
    print("✅ System ready for processing")
    print(f"Supported types: {validation['supported_input_types']}")
else:
    print("❌ System issues detected:")
    print(f"Missing dependencies: {validation['missing_dependencies']}")
```

## 📱 Integration Examples

### Web Application Integration

```javascript
// Upload and process receipt
const formData = new FormData();
formData.append('receipt', fileInput.files[0]);

const response = await fetch('/api/process-receipt', {
    method: 'POST',
    body: formData
});

const result = await response.json();
if (result.status === 'success') {
    console.log('Receipt processed:', result.summary);
    console.log('Stored with ID:', result.summary.receipt_id);
}
```

### Mobile App Integration

```swift
// iOS Swift example
func processReceipt(image: UIImage) {
    let base64String = image.jpegData(compressionQuality: 0.8)?.base64EncodedString()

    let payload = [
        "file_data": base64String,
        "filename": "mobile_receipt.jpg",
        "user_tags": ["mobile", "grocery"]
    ]

    // Send to your backend running the receipt scanner
    APIClient.post("/process-receipt", data: payload) { result in
        // Handle processed receipt data
    }
}
```

## 🧪 Testing & Examples

### Run Example Scripts

```bash
# Run comprehensive examples
python example_usage.py

# This will demonstrate:
# - Processing all input types
# - Storage and retrieval
# - Search capabilities
# - Analytics generation
# - Export functionality
```

### Sample Files

The example script creates sample files for testing:
- `sample_receipt.txt` - Text receipt
- `sample_expenses.csv` - Excel/CSV data

## 🔒 Security & Privacy

- **API Key Security**: Environment variable storage, no hardcoding
- **Local Processing**: All data stored locally by default
- **Data Privacy**: No data sent to external services except for AI processing
- **MCP Compliance**: Structured, secure data exchange format
- **Access Control**: File system permissions for storage directories

## 📈 Performance & Scalability

- **Async Processing**: Non-blocking operations for better performance
- **SQLite Indexing**: Fast search across large receipt collections
- **Batch Processing**: Handle multiple receipts efficiently
- **Memory Management**: Optimized for large file processing
- **Confidence Scoring**: Quality assessment for all extractions

## 🆘 Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```bash
   export GOOGLE_API_KEY="your_key_here"
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Storage Permission Issues**
   ```bash
   mkdir -p receipt_storage
   chmod 755 receipt_storage
   ```

4. **Large File Processing**
   - PDFs: Uses PyMuPDF for superior text extraction and performance
   - Videos: Limit to reasonable file sizes (< 100MB)
   - Images: Automatic resizing for optimal processing

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Validate system setup
validation = await validate_system_setup()
print(json.dumps(validation, indent=2))
```

## 🚀 Deployment Options

### 1. Local Development
```bash
cd receipt_scanner/
adk web
# Access via http://localhost:8080
```

### 2. Production Deployment
```bash
# ADK provides built-in production deployment
adk deploy --platform=cloud-run
# or
adk deploy --platform=kubernetes
```

### 3. Custom API Server
```python
# Create custom FastAPI server
from fastapi import FastAPI, UploadFile
from agent import process_multimodal_receipt

app = FastAPI()

@app.post("/process-receipt")
async def process_receipt_endpoint(file: UploadFile):
    result = await process_multimodal_receipt(
        file_data=await file.read(),
        filename=file.filename,
        store_receipt=True
    )
    return result
```

## 🔮 Future Enhancements

- [ ] **Real-time Collaboration**: Multi-user receipt sharing
- [ ] **Advanced Analytics**: Spending predictions and budgeting
- [ ] **Integration APIs**: Connect with accounting software
- [ ] **Mobile SDKs**: Native iOS and Android components
- [ ] **Cloud Sync**: Optional cloud storage and sync
- [ ] **Multi-language Support**: OCR and processing in multiple languages
- [ ] **Receipt Validation**: Cross-reference with store databases
- [ ] **Tax Integration**: Automatic tax category assignment
- [ ] **Expense Reporting**: Generate formatted expense reports
- [ ] **Subscription Tracking**: Detect and track recurring charges

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Follow the coding standards (see requirements)
5. Submit a pull request

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🎯 Support

- **Issues**: Report bugs and feature requests
- **Documentation**: Check example_usage.py for detailed examples
- **Community**: Join discussions about ADK and Gemini Vision AI

---

**🧾 Built with ❤️ using Google Agent Development Kit, Gemini 2.5 Flash, and comprehensive multimodal AI processing**

### Key Benefits

✅ **Comprehensive**: Handles all major receipt formats and sources
✅ **Accurate**: High-confidence extraction with AI-powered categorization
✅ **Fast**: Optimized processing with async operations and caching
✅ **Scalable**: SQLite indexing and batch processing capabilities
✅ **Secure**: Local storage with optional cloud integration
✅ **Developer-Friendly**: Rich APIs, examples, and documentation
✅ **Production-Ready**: Robust error handling and validation
