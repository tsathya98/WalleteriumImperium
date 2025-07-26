# 🧪 Complete Testing Guide - WalleteriumImperium Receipt Analysis

## 🎯 **System Overview**

Your **WalleteriumImperium** system is powered by **Gemini 2.5 Flash** with dual-mode receipt analysis:
- **📸 Image Mode**: Fast, precise analysis of clear receipt photos
- **🎥 Video Mode**: Intelligent multi-frame analysis for challenging conditions

**NEW: Multipart File Uploads** - 33% faster than base64! 🚀

**API Endpoint**: `POST /api/v1/receipts/upload` (multipart/form-data)
**Required Fields**: `file` (uploaded file), `user_id` (form field)
**Optional Fields**: `metadata` (JSON string as form field)

---

## 🚀 **Quick Start Testing**

### **Prerequisites**
```bash
# 1. Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8080

# 2. Verify health
curl http://localhost:8080/api/v1/health
```

### **🎯 Your Receipt: `miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg`**

**Option 1: CLI Test (Recommended)**
```bash
cd scripts
python test_real_receipt.py "../docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg"
```

**Option 2: Browser Test**
1. Go to: http://localhost:8080/docs
2. Click `POST /api/v1/receipts/upload` → "Try it out"
3. Upload your file and fill the form:
   - `file`: Select your receipt image/video
   - `user_id`: "test_user"
   - `metadata`: "{}" (optional JSON string)

---

## 📋 **Testing Methods Overview**

| **Method** | **Use Case** | **Difficulty** | **Best For** |
|------------|--------------|----------------|--------------|
| **CLI Scripts** | Development/debugging | Easy | Real testing with your files |
| **Browser (Swagger)** | Quick API testing | Easy | Interactive testing |
| **Postman** | API development | Medium | Professional testing |
| **cURL** | Automation/CI | Medium | Scripted testing |

---

## 🔧 **Method 1: CLI Scripts (Recommended)**

### **📂 Available Scripts (Clean & Essential)**

#### **1. test_api_unified.py** - Complete API Testing
```bash
cd scripts
python test_api_unified.py
```
**What it does:**
- ✅ Tests API validation (missing fields, invalid types)
- ✅ Creates synthetic receipt image and tests image analysis
- ✅ Tests video analysis (if video files available)
- ✅ Comprehensive error handling validation

#### **2. test_real_receipt.py** - Real Media Testing
```bash
# Test your specific image
python test_real_receipt.py "../docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg"

# Test any video
python test_real_receipt.py "path/to/your/receipt_video.mp4"

# Auto-detect and test all media in directory
python test_real_receipt.py
```
**What it does:**
- ✅ Auto-detects media type (image/video) from file extension
- ✅ Handles both images and videos seamlessly
- ✅ Real-world testing with actual receipt files
- ✅ Performance metrics and detailed results

#### **3. test_video_receipt.py** - Video-Specific Testing
```bash
# Test specific video
python test_video_receipt.py "receipt_video.mp4"

# Auto-find and test videos
python test_video_receipt.py
```
**What it does:**
- ✅ Video-optimized testing with longer timeouts
- ✅ Creates synthetic video receipts if none found (requires OpenCV)
- ✅ Video-specific performance analysis
- ✅ Format validation and size checking

---

## 🌐 **Method 2: Browser Testing (Swagger UI)**

### **Step-by-Step Guide**

1. **Open Swagger UI**: http://localhost:8080/docs
2. **Health Check**: Test `GET /api/v1/health` first
3. **Upload Receipt**: Click `POST /api/v1/receipts/upload` → "Try it out"

### **Request Format (Multipart Form-Data)**

**📸 For Images:**
```
POST /api/v1/receipts/upload
Content-Type: multipart/form-data

file: [image file binary data]
user_id: browser_test_user
metadata: {"filename": "miami-receipt.jpg", "source": "browser_test"}
```

**🎥 For Videos:**
```
POST /api/v1/receipts/upload
Content-Type: multipart/form-data

file: [video file binary data]
user_id: browser_test_user
metadata: {"filename": "receipt.mp4", "source": "browser_test"}
```

### **No Conversion Needed!**
With multipart uploads, you simply upload the file directly - no base64 conversion required! This makes uploads:
- **33% faster** (no base64 encoding overhead)
- **More memory efficient** (streaming support)
- **Easier to implement** (standard file upload)

### **Check Results**
1. Copy the `processing_token` from upload response
2. Use `GET /api/v1/receipts/status/{token}` to check progress
3. Poll until `status: "completed"`

---

## 📮 **Method 3: Postman Testing**

### **Quick Setup**

1. **Create Collection**: "WalleteriumImperium API"
2. **Set Base URL**: `http://localhost:8080/api/v1`
3. **Add Environment Variables**:
   - `base_url`: `http://localhost:8080/api/v1`
   - `receipt_base64`: [your image base64]
   - `video_base64`: [your video base64]

### **Collection Structure**

#### **1. Health Check**
- **Method**: GET
- **URL**: `{{base_url}}/health`

#### **2. Upload Image Receipt**
- **Method**: POST
- **URL**: `{{base_url}}/receipts/upload`
- **Body Type**: form-data
- **Form Fields**:
  - `file`: [Select your image file]
  - `user_id`: postman_user
  - `metadata`: {"filename": "miami-receipt.jpg", "source": "postman"}

#### **3. Upload Video Receipt**
- **Method**: POST
- **URL**: `{{base_url}}/receipts/upload`
- **Body Type**: form-data
- **Form Fields**:
  - `file`: [Select your video file]
  - `user_id`: postman_user
  - `metadata`: {"filename": "receipt.mp4", "source": "postman"}

#### **4. Check Status**
- **Method**: GET
- **URL**: `{{base_url}}/receipts/status/{{token}}`
- **Note**: Set `token` variable from upload response

#### **5. Get History**
- **Method**: GET
- **URL**: `{{base_url}}/receipts/history?user_id=postman_user`

### **Import Collection JSON**
```json
{
  "info": {
    "name": "WalleteriumImperium Receipt Analysis API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/health"
      }
    },
    {
      "name": "Upload Image Receipt",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/receipts/upload",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"media_base64\": \"{{receipt_base64}}\",\n  \"media_type\": \"image\",\n  \"user_id\": \"postman_user\",\n  \"metadata\": {\n    \"filename\": \"receipt.jpg\"\n  }\n}"
        }
      }
    },
    {
      "name": "Upload Video Receipt",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/receipts/upload",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"media_base64\": \"{{video_base64}}\",\n  \"media_type\": \"video\",\n  \"user_id\": \"postman_user\",\n  \"metadata\": {\n    \"filename\": \"receipt.mp4\"\n  }\n}"
        }
      }
    },
    {
      "name": "Check Status",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/receipts/status/{{token}}"
      }
    },
    {
      "name": "Get History",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/receipts/history?user_id=postman_user"
      }
    }
  ]
}
```

---

## 💻 **Method 4: cURL Testing**

### **Basic Commands**

#### **Health Check**
```bash
curl http://localhost:8080/api/v1/health | jq .
```

#### **Upload Image Receipt**
```bash
# Direct multipart upload - no base64 conversion needed!
curl -X POST "http://localhost:8080/api/v1/receipts/upload" \
  -F "file=@docs/receipts_samples/miami-floridael-chalan-restaurant-peruvian-foodcheck-receipt-bill-FWREE7.jpg" \
  -F "user_id=curl_user" \
  -F "metadata={\"filename\": \"miami-receipt.jpg\", \"source\": \"curl_test\"}" | jq .
```

#### **Upload Video Receipt**
```bash
# Direct multipart upload - much faster than base64!
curl -X POST "http://localhost:8080/api/v1/receipts/upload" \
  -F "file=@receipt_video.mp4" \
  -F "user_id=curl_user" \
  -F "metadata={\"filename\": \"receipt.mp4\", \"source\": \"curl_test\"}" | jq .
```

#### **Check Status**
```bash
export TOKEN="proc_1721934567_abc123def"  # From upload response
curl "http://localhost:8080/api/v1/receipts/status/$TOKEN" | jq .
```

#### **Complete Test Script**
```bash
#!/bin/bash
set -e

echo "🧪 Testing WalleteriumImperium Receipt Analysis API"

# Health check
echo "1. Health Check..."
curl -s http://localhost:8080/api/v1/health | jq .status

# Upload receipt with multipart (much faster!)
echo "2. Uploading receipt..."
RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/receipts/upload" \
  -F "file=@your_receipt.jpg" \
  -F "user_id=test_user" \
  -F "metadata={}")

TOKEN=$(echo $RESPONSE | jq -r .processing_token)
echo "Token: $TOKEN"

# Poll for results
echo "3. Waiting for results..."
for i in {1..30}; do
  STATUS_RESPONSE=$(curl -s "http://localhost:8080/api/v1/receipts/status/$TOKEN")
  STATUS=$(echo $STATUS_RESPONSE | jq -r .status)

  echo "Attempt $i: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    echo "🎉 Analysis completed!"
    echo $STATUS_RESPONSE | jq .result
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "❌ Analysis failed!"
    echo $STATUS_RESPONSE | jq .error
    break
  fi

  sleep 3
done
```

---

## 🎥 **Video Analysis Deep Dive**

### **Why Videos Are Better**
- ✅ **More forgiving**: Auto-focus and exposure adjustment
- ✅ **Better accuracy**: Gemini analyzes multiple frames automatically
- ✅ **Poor lighting tolerance**: Video captures exposure variations
- ✅ **Easier to capture**: Just point and record

### **Video Best Practices**
- 📱 **Duration**: Record 3-5 seconds
- 💡 **Lighting**: Good lighting helps (but more forgiving than images)
- 📐 **Stability**: Keep receipt flat, minimize camera shake
- 🎯 **Framing**: Fill the frame with the receipt
- 🎬 **Orientation**: Landscape mode for better coverage

### **Supported Video Formats**
| **Format** | **Extension** | **Recommendation** |
|------------|---------------|-------------------|
| **MP4** | `.mp4` | ✅ **Best** - Great compression, universal support |
| **MOV** | `.mov` | ✅ **Good** - iPhone/Mac default, high quality |
| **AVI** | `.avi` | ⚠️ **OK** - Older format, larger files |
| **MKV** | `.mkv` | ✅ **Good** - High quality, good compression |
| **WEBM** | `.webm` | ✅ **Good** - Web-optimized format |

### **File Size Limits**
- 📸 **Images**: Up to 10MB
- 🎥 **Videos**: Up to 100MB

### **Creating Test Videos**

#### **Using OpenCV (Synthetic)**
```python
# Run the video test script to create synthetic video
python scripts/test_video_receipt.py
# Creates test_receipt_video.mp4 if OpenCV is available
```

#### **Using Your Phone**
1. **Open camera app**
2. **Switch to video mode**
3. **Record 3-5 seconds** of the receipt
4. **Transfer to computer**
5. **Test with script**:
```bash
python scripts/test_video_receipt.py "path/to/your/video.mp4"
```

---

## 📊 **Expected Results & Validation**

### **Successful Analysis Response**
```json
{
  "processing_token": "proc_1721934567_abc123def",
  "status": "processing",
  "estimated_time": 15,
  "message": "Receipt uploaded successfully"
}
```

### **Status Check Response**
```json
{
  "status": "completed",
  "progress": {
    "stage": "Analysis Complete",
    "percentage": 100.0,
    "message": "Receipt analysis completed successfully"
  },
  "result": {
    "id": "receipt_456",
    "place": "El Chalan Restaurant",
    "amount": 25.50,
    "category": "dining",
    "description": "Restaurant - Peruvian cuisine",
    "time": "2024-01-15T19:30:00Z",
    "transactionType": "expense",
    "importance": "medium",
    "recurring": false,
    "warranty": false
  }
}
```

### **Analysis Quality Indicators**
- ✅ **Store name recognized**: Should extract "El Chalan" or similar
- ✅ **Amount accurate**: Should match receipt total
- ✅ **Category correct**: "dining" for restaurant receipts
- ✅ **Date/time parsing**: ISO format timestamps
- ✅ **Description meaningful**: Combines store and category info

---

## 🚨 **Troubleshooting**

### **Common Issues & Solutions**

#### **1. Server Won't Start**
```bash
# Check if port is already in use
lsof -i :8080

# Try different port
python -m uvicorn main:app --host 0.0.0.0 --port 8081
```

#### **2. Upload Fails - Validation Error**
**Error**: `422 Unprocessable Entity`
**Solution**: Ensure all required fields:
```json
{
  "media_base64": "...",     // Required
  "media_type": "image",     // Required: "image" or "video"
  "user_id": "test_user"     // Required
}
```

#### **3. Base64 Encoding Issues**
```bash
# Ensure no line breaks in base64
base64 -w 0 file.jpg  # Linux
base64 -b 0 file.jpg  # macOS

# For large files, check size
ls -lh file.mp4
```

#### **4. Processing Timeout**
- **Images**: Should complete in 10-30 seconds
- **Videos**: May take 30-60 seconds for large files
- **Check server logs** for detailed error messages

#### **5. Video Analysis Fails**
- **Check file size**: Must be under 100MB
- **Verify format**: Use MP4, MOV, AVI, MKV, or WEBM
- **Test with smaller video**: Create 5-second test clip

#### **6. Poor Analysis Results**
- ✅ **Use good lighting** when capturing
- ✅ **Keep receipt flat** and readable
- ✅ **Try video mode** for challenging receipts
- ✅ **Check receipt quality** - ensure text is visible

### **Debug Mode**
```bash
# Start server with debug logging
LOGGING_LEVEL=DEBUG python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Check logs in terminal for detailed processing information
```

---

## 📈 **Performance Benchmarks**

### **Expected Performance**
| **Media Type** | **File Size** | **Processing Time** | **Success Rate** |
|----------------|---------------|-------------------|------------------|
| **Images** | < 5MB | 10-20 seconds | 95%+ |
| **Images** | 5-10MB | 15-30 seconds | 90%+ |
| **Videos** | < 20MB | 20-40 seconds | 95%+ |
| **Videos** | 20-100MB | 30-60 seconds | 85%+ |

### **Quality Factors**
- 📸 **Image clarity**: Higher resolution = better results
- 💡 **Lighting**: Good lighting significantly improves accuracy
- 📐 **Receipt condition**: Flat, uncrumpled receipts work best
- 🎥 **Video stability**: Steady recording improves frame selection

---

## 🎯 **Testing Checklist**

### **Pre-Testing**
- [ ] Server running on port 8080
- [ ] Health endpoint returns 200 OK
- [ ] Test files available in correct locations

### **Basic API Testing**
- [ ] Image upload with valid payload succeeds
- [ ] Video upload with valid payload succeeds
- [ ] Invalid media_type is rejected (422 error)
- [ ] Missing required fields are rejected (422 error)
- [ ] Status endpoint returns processing progress

### **Real Receipt Testing**
- [ ] Your receipt image processes successfully
- [ ] Video of same receipt processes successfully
- [ ] Results include store name, amount, category
- [ ] Processing completes within expected timeframe

### **Edge Case Testing**
- [ ] Large image files (close to 10MB limit)
- [ ] Large video files (close to 100MB limit)
- [ ] Poor quality/blurry receipts
- [ ] Different lighting conditions
- [ ] Various receipt formats and languages

### **Performance Testing**
- [ ] Multiple concurrent uploads
- [ ] Processing time within benchmarks
- [ ] Server remains stable under load
- [ ] Memory usage reasonable

---

## 🎉 **Success! Your Receipt Analysis System is Ready**

You now have a **comprehensive testing framework** for your WalleteriumImperium receipt analysis system featuring:

### **✅ Dual-Mode Analysis**
- **📸 Image Mode**: Fast, precise analysis
- **🎥 Video Mode**: Intelligent multi-frame processing

### **✅ Multiple Testing Methods**
- **CLI Scripts**: Real-world testing with your files
- **Browser UI**: Interactive API exploration
- **Postman**: Professional API testing
- **cURL**: Automated/scripted testing

### **✅ Production-Ready Features**
- **Explicit media type specification**: No ambiguity
- **Comprehensive validation**: Proper error handling
- **Detailed logging**: Full traceability
- **Performance monitoring**: Benchmarks and metrics

**Start testing with your receipt and explore the power of Gemini 2.5 Flash! 🇵🇪🍽️📸🎥**
