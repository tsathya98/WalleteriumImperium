#!/usr/bin/env python3
"""
Test script for real receipt images
Upload and analyze actual receipt photos
"""

import base64
import json
import time
import requests
from pathlib import Path

# API Configuration
API_BASE = "http://localhost:8080/api/v1"
RECEIPTS_API = f"{API_BASE}/receipts"

def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to read image {image_path}: {str(e)}")

def analyze_real_receipt(image_path: str, user_id: str = "real_test_user"):
    """Analyze a real receipt image"""
    print(f"📸 Analyzing Real Receipt: {image_path}")
    print("=" * 50)
    
    try:
        # Check if image exists
        if not Path(image_path).exists():
            print(f"❌ Image file not found: {image_path}")
            return
        
        # Convert image to base64
        print("1. Converting image to base64...")
        image_base64 = image_to_base64(image_path)
        image_size_mb = len(image_base64) * 3 / 4 / 1024 / 1024
        print(f"   ✅ Image converted: {image_size_mb:.2f} MB")
        
        if image_size_mb > 10:
            print(f"   ⚠️  Warning: Image is large ({image_size_mb:.2f} MB)")
        
        # Upload receipt
        print("2. Uploading receipt...")
        upload_payload = {
            "image_base64": image_base64,
            "user_id": user_id,
            "metadata": {
                "source": "real_image_test",
                "filename": Path(image_path).name,
                "size_mb": image_size_mb
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
            return
        
        upload_data = upload_response.json()
        token = upload_data["processing_token"]
        print(f"   ✅ Upload successful - Token: {token}")
        
        # Poll for results
        print("3. Processing receipt with Gemini 2.5 Flash...")
        max_attempts = 30  # Real images might take longer
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"   Polling... {attempt}/{max_attempts}")
            
            status_response = requests.get(f"{RECEIPTS_API}/status/{token}")
            
            if status_response.status_code != 200:
                print(f"   ❌ Status check failed: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            status = status_data["status"]
            progress = status_data["progress"]
            
            print(f"   Status: {status} - {progress['stage']} ({progress['percentage']:.1f}%)")
            
            if status == "completed":
                print("\n🎉 Analysis Completed!")
                
                # Display detailed results
                result = status_data["result"]
                print(f"\n📊 Receipt Analysis Results:")
                print(f"🏪 Store: {result['place']}")
                print(f"💰 Total Amount: ${result['amount']:.2f}")
                print(f"📂 Category: {result['category']}")
                print(f"📝 Description: {result['description']}")
                print(f"📅 Transaction Time: {result['time']}")
                print(f"💳 Transaction Type: {result['transactionType']}")
                print(f"⭐ Importance: {result.get('importance', 'N/A')}")
                print(f"🔄 Recurring: {result.get('recurring', False)}")
                print(f"🛡️ Warranty: {result.get('warranty', False)}")
                
                # Save detailed result
                output_file = f"real_receipt_result_{Path(image_path).stem}.json"
                with open(output_file, 'w') as f:
                    json.dump(status_data, f, indent=2, default=str)
                print(f"\n💾 Full analysis saved to: {output_file}")
                
                return status_data
                
            elif status == "failed":
                print("\n❌ Processing Failed!")
                if "error" in status_data:
                    error = status_data["error"]
                    print(f"Error Code: {error.get('code', 'Unknown')}")
                    print(f"Error Message: {error.get('message', 'Unknown')}")
                break
            
            time.sleep(3)  # Wait a bit longer for real images
        
        if attempt >= max_attempts:
            print("\n⏰ Processing timed out")
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("📸 Real Receipt Analysis Test")
    print("=" * 60)
    
    # Example usage - you can modify these paths
    test_images = [
        "receipt1.jpg",
        "receipt2.png", 
        "receipt.jpeg",
        "test_receipt.jpg"
    ]
    
    print("Looking for receipt images in current directory...")
    
    # Find available images
    available_images = []
    for img in test_images:
        if Path(img).exists():
            available_images.append(img)
            print(f"✅ Found: {img}")
    
    if not available_images:
        print("\n❌ No receipt images found!")
        print("\nTo test with real receipts:")
        print("1. Take a photo of a receipt with your phone")
        print("2. Save it as 'receipt.jpg' in this directory")
        print("3. Run this script again")
        print("\nOr specify a custom path:")
        print("python test_real_receipt.py path/to/your/receipt.jpg")
        return
    
    # Analyze each available image
    for image_path in available_images:
        analyze_real_receipt(image_path)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Custom image path provided
        custom_path = sys.argv[1]
        analyze_real_receipt(custom_path)
    else:
        # Look for images in current directory
        main() 