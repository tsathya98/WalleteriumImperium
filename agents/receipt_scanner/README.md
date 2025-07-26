# 🧾 Receipt Scanner Agent

An advanced AI-powered receipt scanning agent built with Google's Agent Development Kit (ADK) and Gemini Vision AI. This agent can process receipt images to extract itemized information, pricing details, and provide structured data output compatible with the Model Context Protocol (MCP).

## ✨ Features

### 📸 **Receipt Scanning Capabilities**
- **Store Information Extraction**: Name, address, phone, date, time, receipt number
- **Individual Item Details**: Name, quantity, unit price, total price, category
- **Financial Totals**: Subtotal, tax, discounts, final total, payment method
- **Multi-format Support**: File paths, base64 encoded images, URLs

### 🔄 **MCP Integration**
- **Structured Data Output**: Compatible with Model Context Protocol for agent-to-agent communication
- **JSON-formatted Responses**: Easy integration with other systems and agents
- **Standardized Error Handling**: Consistent status reporting across all operations

### 📊 **Analysis Features**
- **Spending Trend Analysis**: Track expenses over time
- **Category Breakdowns**: Organize spending by item categories
- **Store Analytics**: Identify most frequented stores
- **Item Purchase Patterns**: Track frequently bought items

### 📱 **Camera Integration Ready**
- **Multiple Input Methods**: Support for various camera integration approaches
- **Platform Agnostic**: Works with mobile, web, and desktop camera implementations
- **Real-time Processing**: Optimized for quick receipt scanning workflows

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Google ADK** - Agent Development Kit
3. **Google API Key** for Gemini Vision AI
4. **Required Dependencies** (see requirements.txt)

### Installation

```bash
# Clone or navigate to the receipt scanner directory
cd multi_tool_agent/receipt_scanner/

# Install dependencies
pip install -r requirements.txt

# Set up your Google API key
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

### ADK Web Interface (Recommended)

```bash
# Start the ADK web interface with camera support
adk web

# Open the provided URL in your browser (usually http://localhost:8080)
# The interface provides:
# - 📸 Camera capture from browser
# - 📁 Drag & drop file upload
# - 🔍 Real-time receipt processing
# - 📊 MCP-formatted results
# - 📈 Analytics dashboard
```

### Programmatic Usage

```python
from agent import process_receipt_image

# Scan a receipt from file path
result = process_receipt_image("path/to/receipt.jpg", image_format="file_path")

# Scan a receipt from base64 data (e.g., from camera)
result = process_receipt_image(base64_image_data, image_format="base64")

print(result)
```

## 📖 Detailed Usage

### 1. File Path Scanning

```python
from agent import process_receipt_image

# Process receipt from saved image file
result = process_receipt_image(
    image_data="receipt_photo.jpg",
    image_format="file_path"
)

if result["status"] == "success":
    receipt_data = result["receipt_data"]
    print(f"Store: {receipt_data['store_info']['name']}")
    print(f"Total: ${receipt_data['totals']['total']}")
    print(f"Items: {len(receipt_data['items'])}")
```

### 2. Base64 Scanning (Camera Integration)

```python
import base64
from agent import process_receipt_image

# Convert image to base64 (simulating camera capture)
with open("receipt.jpg", "rb") as img_file:
    image_data = base64.b64encode(img_file.read()).decode('utf-8')

# Process the base64 image
result = process_receipt_image(
    image_data=image_data,
    image_format="base64"
)

# Access MCP-formatted data
mcp_data = result["mcp_format"]
extracted = mcp_data["extracted_data"]
store_info = extracted["store_information"]
line_items = extracted["line_items"]
```

### 3. Receipt Trend Analysis

```python
from agent import analyze_receipt_trends

# Analyze multiple receipts for spending patterns
receipt_history = [
    {
        "status": "success",
        "receipt_data": {
            "store_info": {"name": "Grocery Store", "date": "2024-01-15"},
            "items": [
                {"name": "Apples", "category": "food", "total_price": 3.99},
                {"name": "Bread", "category": "food", "total_price": 2.50}
            ],
            "totals": {"total": 6.49}
        }
    }
    # ... more receipts
]

analysis = analyze_receipt_trends(receipt_history)
insights = analysis["insights"]
print(f"Total Spending: ${insights['total_spending']}")
print(f"Most Frequent Store: {insights['most_frequent_store']}")
```

## 🔌 Camera Integration Examples

### Mobile App Integration (React Native)

```javascript
// React Native example
import { launchImageLibrary } from 'react-native-image-picker';

const captureReceipt = () => {
  launchImageLibrary({ mediaType: 'photo' }, (response) => {
    if (response.assets && response.assets[0]) {
      const base64Data = response.assets[0].base64;

      // Send to Python backend
      fetch('http://your-backend/scan-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: base64Data,
          image_format: 'base64'
        })
      });
    }
  });
};
```

### Web Application Integration

```javascript
// Web camera capture
const captureReceiptFromCamera = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  const video = document.createElement('video');
  video.srcObject = stream;
  video.play();

  // Capture frame to canvas
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Convert to base64
  const base64Data = canvas.toDataURL('image/jpeg').split(',')[1];

  // Send to backend for processing
  const response = await fetch('/api/scan-receipt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_data: base64Data,
      image_format: 'base64'
    })
  });

  const result = await response.json();
  console.log('Receipt data:', result);
};
```

### Desktop Camera Integration (Python)

```python
import cv2
import base64
from agent import process_receipt_image

def capture_and_scan_receipt():
    # Initialize camera
    cap = cv2.VideoCapture(0)

    print("Press SPACE to capture receipt, ESC to exit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow('Receipt Scanner - Press SPACE to capture', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Spacebar to capture
            # Save captured frame
            cv2.imwrite('captured_receipt.jpg', frame)

            # Process the receipt
            result = process_receipt_image(
                'captured_receipt.jpg',
                image_format='file_path'
            )

            print("Scan result:", result)
            break
        elif key == 27:  # ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()
```

## 📊 MCP (Model Context Protocol) Integration

The receipt scanner agent outputs data in MCP-compatible format for seamless integration with other AI agents:

```python
# Example MCP output structure
mcp_response = {
    "mcp_format": {
        "protocol_version": "1.0",
        "data_type": "receipt_scan",
        "status": "success",
        "timestamp": "2024-01-15T10:30:00",
        "extracted_data": {
            "store_information": {
                "name": "Store Name",
                "address": "Store Address",
                "date": "2024-01-15",
                "time": "10:30"
            },
            "line_items": [
                {
                    "name": "Item Name",
                    "quantity": 1,
                    "unit_price": 5.99,
                    "total_price": 5.99,
                    "category": "food"
                }
            ],
            "financial_totals": {
                "subtotal": 5.99,
                "tax": 0.48,
                "total": 6.47
            },
            "metadata": {
                "confidence_level": "high",
                "items_count": 1,
                "processing_method": "gemini_vision_ocr"
            }
        }
    }
}

# Other agents can easily consume this data
expense_tracker.add_receipt(mcp_response["mcp_format"])
budget_analyzer.process_spending(mcp_response["mcp_format"])
```

## 🔧 Configuration

### Environment Variables

```bash
# Required: Google Gemini API Key
export GOOGLE_API_KEY="your_api_key_here"

# Optional: Custom model selection
export GEMINI_MODEL="gemini-2.5-flash"  # Default model
```

### Custom Configuration

```python
# Customize the agent behavior
from agent import receipt_scanner_agent

# Access the underlying tools
receipt_scanner_agent.tools[0]  # process_receipt_image
receipt_scanner_agent.tools[1]  # capture_and_scan_receipt
receipt_scanner_agent.tools[2]  # analyze_receipt_trends

# Use with custom parameters
result = process_receipt_image(
    image_data="receipt.jpg",
    image_format="file_path"
)
```

## 🧪 Testing

### ADK Web Interface Testing (Recommended)
```bash
# Start the web interface
adk web

# Test in browser:
# 1. Open http://localhost:8080
# 2. Upload a receipt image or use camera
# 3. View real-time processing results
# 4. Download MCP-formatted data
```

### Programmatic Testing
```bash
python example_usage.py
```

This will demonstrate:
- File path scanning
- Base64 data processing
- Trend analysis
- Camera integration concepts
- MCP format examples

## 🏗️ Architecture

```
Receipt Scanner Agent
├── agent.py                 # Main agent implementation
├── requirements.txt         # Dependencies
├── example_usage.py        # Usage examples
└── README.md              # Documentation

Core Components:
├── process_receipt_image()    # Main OCR processing function
├── capture_and_scan_receipt() # Camera integration stub
├── analyze_receipt_trends()   # Analytics and insights
└── receipt_scanner_agent     # ADK Agent instance
```

## 🔒 Security & Privacy

- **API Key Security**: Store Google API keys securely using environment variables
- **Image Data**: Receipt images are processed in memory and not stored permanently
- **Data Privacy**: All extracted data remains within your system unless explicitly shared
- **MCP Protocol**: Structured data sharing follows standardized protocols for security

## 🚀 Deployment Options

### 1. Local Development with ADK Web
```bash
cd receipt_scanner/
adk web
# Access via browser at http://localhost:8080
```

### 2. Programmatic Testing
```bash
cd receipt_scanner/
python example_usage.py
```

### 3. Production Deployment
```bash
# ADK provides built-in production deployment
adk deploy --platform=cloud-run
# or
adk deploy --platform=kubernetes
```

### 4. Custom Integration
```python
# Import the agent into your existing application
from multi_tool_agent.receipt_scanner.agent import receipt_scanner_agent

# Use with your own web framework or API
result = receipt_scanner_agent.process_receipt_image(image_data, "base64")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests in the project issues
- **Documentation**: Check this README and example_usage.py for guidance
- **Community**: Join discussions about Google ADK and Gemini Vision AI

## 🔮 Future Enhancements

- [ ] Real-time camera preview with scanning overlay
- [ ] Multi-language receipt support
- [ ] Advanced analytics dashboard
- [ ] Integration with popular expense tracking apps
- [ ] Batch processing for multiple receipts
- [ ] Custom category training
- [ ] Receipt validation and correction tools

---

## 🚀 Frontend Integration Guide

This guide provides instructions for frontend applications to interact with the WalleteriumImperium API.

### **Core API Endpoints**

| **Endpoint** | **Method** | **Description** |
|--------------|------------|-----------------|
| `/api/v1/receipts/upload` | POST | Upload receipt for analysis |
| `/api/v1/receipts/status/{token}` | GET | Check processing status |
| `/api/v1/receipts/history/{user_id}` | GET | Get user's receipt history |
| `/api/v1/receipts/{receipt_id}` | GET | Get detailed receipt information |

### **Integration Flow: Step-by-Step**

Here's the recommended workflow for a seamless user experience:

1.  **User Uploads Receipt**: The user selects an image or video file and a `user_id` is provided.
2.  **Call `/upload` Endpoint**: Your frontend sends the file and `user_id` to the `/upload` endpoint.
3.  **Receive Processing Token**: The API will immediately respond with a `processing_token`.
4.  **Poll for Status**: Use the `processing_token` to periodically call the `/status/{token}` endpoint until the status is `completed` or `failed`.
5.  **Display Results**: Once completed, the response from the status endpoint will contain the full analysis results.

### **Code Examples**

#### **cURL Example**
```bash
# 1. Upload the receipt and get a token
curl -X POST "http://localhost:8080/api/v1/receipts/upload" \
  -F "file=@/path/to/your/receipt.jpg" \
  -F "user_id=hackathon_user_123"

# Response will be like:
# {"processing_token":"abc-123","estimated_time":15,"status":"uploaded",...}

# 2. Poll for the result
curl "http://localhost:8080/api/v1/receipts/status/abc-123"

# 3. Get user history
curl "http://localhost:8080/api/v1/receipts/history/hackathon_user_123"
```

#### **JavaScript (fetch) Example**
```javascript
const API_BASE_URL = 'http://localhost:8080/api/v1';

// Step 1: Upload a receipt
const uploadReceipt = async (file, userId) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    try {
        const response = await fetch(`${API_BASE_URL}/receipts/upload`, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();
        console.log('Upload initiated:', data);
        return data.processing_token; // Return the token for polling
    } catch (error) {
        console.error('Upload failed:', error);
    }
};

// Step 2: Poll for the result
const checkStatus = async (token) => {
    try {
        const response = await fetch(`${API_BASE_URL}/receipts/status/${token}`);
        const data = await response.json();

        if (data.status === 'completed') {
            console.log('Analysis complete:', data.result);
            // Update your UI with the results here
        } else if (data.status === 'processing' || data.status === 'uploaded') {
            console.log('Still processing...', data.progress);
            // Continue polling after a delay
            setTimeout(() => checkStatus(token), 3000); // Poll every 3 seconds
        } else {
            console.error('Processing failed:', data.error);
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
};

// Example Usage
const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    const userId = 'hackathon_user_123'; // Get this from your auth system or user input

    if (file && userId) {
        const token = await uploadReceipt(file, userId);
        if (token) {
            checkStatus(token);
        }
    }
};
```

#### **Flutter (Dart) Example**
This example provides a service class and a widget to handle file uploads and status polling.

**1. Add Dependencies to `pubspec.yaml`**
```yaml
dependencies:
  http: ^1.2.1
  image_picker: ^1.1.2
  http_parser: ^4.0.2
```

**2. Create an `ApiService`**
```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  static const String _baseUrl = 'http://YOUR_API_BASE_URL'; // Replace with your URL

  static Future<String?> uploadReceipt(File imageFile, String userId) async {
    final uri = Uri.parse('$_baseUrl/api/v1/receipts/upload');
    final request = http.MultipartRequest('POST', uri)
      ..fields['user_id'] = userId
      ..files.add(await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
        contentType: MediaType('image', 'jpeg'),
      ));

    final response = await request.send();
    if (response.statusCode == 202) {
      final responseBody = await response.stream.bytesToString();
      return jsonDecode(responseBody)['processing_token'];
    }
    return null;
  }

  static Future<Map<String, dynamic>?> checkStatus(String token) async {
    final uri = Uri.parse('$_baseUrl/api/v1/receipts/status/$token');
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return null;
  }
}
```

**3. Create the UI Widget**
```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
// ... import your ApiService

class ReceiptUploaderScreen extends StatefulWidget {
  @override
  _ReceiptUploaderScreenState createState() => _ReceiptUploaderScreenState();
}

class _ReceiptUploaderScreenState extends State<ReceiptUploaderScreen> {
  String _statusMessage = 'Upload a receipt to begin.';
  bool _isLoading = false;

  void _handleUpload() async {
    final image = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() {
      _isLoading = true;
      _statusMessage = 'Uploading...';
    });

    final token = await ApiService.uploadReceipt(File(image.path), 'hackathon_user');
    if (token != null) {
      setState(() => _statusMessage = 'Processing...');
      _pollForResult(token);
    } else {
      setState(() => _statusMessage = 'Upload failed.');
    }
  }

  void _pollForResult(String token) async {
    while (_isLoading) {
      final response = await ApiService.checkStatus(token);
      if (response != null && response['status'] == 'completed') {
        setState(() {
          _isLoading = false;
          _statusMessage = 'Success! Store: ${response['result']['place']}';
        });
        return;
      }
      await Future.delayed(Duration(seconds: 3));
    }
  }

  // ... rest of your widget build method
}
```

---

**Built with ❤️ using Google Agent Development Kit and Gemini Vision AI**
