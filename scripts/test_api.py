#!/usr/bin/env python3
"""
Test script for Receipt API endpoints
Tests the complete receipt upload and processing workflow
"""

import asyncio
import base64
import json
import time
import sys
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# API Configuration
API_BASE = "http://localhost:8080/api/v1"
RECEIPTS_API = f"{API_BASE}/receipts"

def create_test_receipt_base64() -> str:
    """Create a test receipt image as base64"""
    # Create a simple receipt-like image
    width, height = 400, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw receipt content
    y_pos = 20
    line_height = 25
    
    receipt_lines = [
        "TARGET STORE #1234",
        "123 SHOPPING BLVD",
        "ANYTOWN, CA 90210",
        "Tel: (555) 123-4567",
        "",
        "Date: 2024-01-26",
        "Time: 15:45",
        "Receipt #: T1234567890",
        "",
        "Items Purchased:",
        "Shampoo Herbal       $4.99",
        "Toothpaste Mint      $3.49", 
        "Soap Bar 3pk         $2.99",
        "Vitamin C 60ct       $8.99",
        "Energy Drink 4pk    $12.99",
        "",
        "Subtotal:           $33.45",
        "Tax (8.5%):          $2.84", 
        "Total:              $36.29",
        "",
        "Payment: VISA ****1234",
        "Thank you for shopping!"
    ]
    
    for line in receipt_lines:
        draw.text((20, y_pos), line, fill='black', font=font)
        y_pos += line_height
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    image_bytes = buffer.getvalue()
    
    return base64.b64encode(image_bytes).decode('utf-8')

def test_health_endpoints():
    """Test all health endpoints"""
    print("🏥 Testing Health Endpoints")
    print("=" * 40)
    
    endpoints = [
        "/health",
        "/health/services", 
        "/health/ready",
        "/health/live"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}")
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"{status} {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    print(f"    Status: {data['status']}")
            
        except Exception as e:
            print(f"❌ FAIL {endpoint} - Error: {str(e)}")
    
    print()

def test_receipt_upload():
    """Test receipt upload and processing workflow"""
    print("📄 Testing Receipt Upload Workflow")
    print("=" * 40)
    
    try:
        # Step 1: Create test receipt
        print("1. Creating test receipt image...")
        image_base64 = create_test_receipt_base64()
        print(f"   ✅ Image created: {len(image_base64)} chars")
        
        # Step 2: Upload receipt
        print("2. Uploading receipt...")
        upload_payload = {
            "image_base64": image_base64,
            "user_id": "test_user_api_123",
            "metadata": {
                "test": True,
                "source": "api_test",
                "timestamp": time.time()
            }
        }
        
        upload_response = requests.post(
            f"{RECEIPTS_API}/upload",
            json=upload_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if upload_response.status_code != 200:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text}")
            return None
        
        upload_data = upload_response.json()
        processing_token = upload_data["processing_token"]
        print(f"   ✅ Upload successful")
        print(f"   Token: {processing_token}")
        print(f"   Estimated time: {upload_data['estimated_time']}s")
        
        # Step 3: Poll for status
        print("3. Polling for processing status...")
        max_attempts = 20
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"   Attempt {attempt}/{max_attempts}...")
            
            status_response = requests.get(f"{RECEIPTS_API}/status/{processing_token}")
            
            if status_response.status_code != 200:
                print(f"   ❌ Status check failed: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            status = status_data["status"]
            progress = status_data["progress"]
            
            print(f"   Status: {status}")
            print(f"   Progress: {progress['stage']} - {progress['percentage']:.1f}%")
            print(f"   Message: {progress['message']}")
            
            if status == "completed":
                print("   ✅ Processing completed!")
                
                # Display results
                result = status_data["result"]
                print(f"\n📊 Analysis Results:")
                print(f"   🏪 Store: {result['place']}")
                print(f"   💰 Amount: ${result['amount']:.2f}")
                print(f"   📂 Category: {result['category']}")
                print(f"   📝 Description: {result['description']}")
                print(f"   📅 Time: {result['time']}")
                print(f"   🔄 Transaction Type: {result['transactionType']}")
                
                # Save detailed result
                output_file = Path("api_test_result.json")
                with open(output_file, 'w') as f:
                    json.dump(status_data, f, indent=2, default=str)
                print(f"   💾 Full result saved to: {output_file}")
                
                return processing_token
                
            elif status == "failed":
                print("   ❌ Processing failed!")
                if "error" in status_data:
                    print(f"   Error: {status_data['error']}")
                break
            
            # Wait before next poll
            time.sleep(2)
        
        if attempt >= max_attempts:
            print("   ⏰ Timeout: Processing took too long")
        
        return processing_token
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_history_endpoints(token=None):
    """Test receipt history endpoints"""
    print("\n📚 Testing History Endpoints")
    print("=" * 40)
    
    try:
        # Test history endpoint
        print("1. Testing receipt history...")
        history_response = requests.get(f"{RECEIPTS_API}/history?limit=5")
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            receipts = history_data.get("receipts", [])
            print(f"   ✅ Retrieved {len(receipts)} receipts")
            
            for i, receipt in enumerate(receipts[:3], 1):
                print(f"   {i}. {receipt.get('place', 'Unknown')} - ${receipt.get('amount', 0):.2f}")
        else:
            print(f"   ❌ History failed: {history_response.status_code}")
        
        # Test individual receipt endpoint (if we have a token)
        if token:
            print("2. Testing individual receipt retrieval...")
            receipt_response = requests.get(f"{RECEIPTS_API}/{token}")
            
            if receipt_response.status_code == 200:
                print("   ✅ Individual receipt retrieved")
            else:
                print(f"   ❌ Individual receipt failed: {receipt_response.status_code}")
    
    except Exception as e:
        print(f"❌ History test failed: {str(e)}")

def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n🚨 Testing Error Scenarios")
    print("=" * 40)
    
    test_cases = [
        {
            "name": "Invalid base64",
            "payload": {"image_base64": "invalid_base64", "user_id": "test"},
            "expected_status": 400
        },
        {
            "name": "Missing user_id",
            "payload": {"image_base64": "dGVzdA=="},
            "expected_status": 422
        },
        {
            "name": "Empty payload",
            "payload": {},
            "expected_status": 422
        }
    ]
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{RECEIPTS_API}/upload",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"}
            )
            
            expected = test_case["expected_status"]
            actual = response.status_code
            
            if actual == expected:
                print(f"   ✅ {test_case['name']}: {actual} (expected)")
            else:
                print(f"   ❌ {test_case['name']}: {actual} (expected {expected})")
                
        except Exception as e:
            print(f"   ❌ {test_case['name']}: Error - {str(e)}")

def main():
    """Run all API tests"""
    print("🚀 Receipt Analysis API Test Suite")
    print("=" * 60)
    print(f"Testing API at: {API_BASE}")
    print("=" * 60)
    
    # Test 1: Health endpoints
    test_health_endpoints()
    
    # Test 2: Receipt upload workflow
    token = test_receipt_upload()
    
    # Test 3: History endpoints
    test_history_endpoints(token)
    
    # Test 4: Error scenarios
    test_error_scenarios()
    
    print("\n" + "=" * 60)
    print("🎉 API Test Suite Completed!")
    print("\nNext steps:")
    print("1. Try uploading a real receipt image")
    print("2. Test with your frontend application")
    print("3. Monitor logs for any issues")
    print("4. Deploy to production when ready")

if __name__ == "__main__":
    main() 