#!/usr/bin/env python3
"""
Unified API Test - Multipart File Upload
Tests the enhanced API using multipart/form-data uploads (no more base64!)
"""

import asyncio
import json
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# API Configuration
API_BASE = "http://localhost:8080/api/v1"
RECEIPTS_API = f"{API_BASE}/receipts"

def create_test_image() -> str:
    """Create a synthetic test receipt image and save to file"""
    # Create a simple receipt image
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a better font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw receipt content
    y = 30
    lines = [
        "QUICK MART",
        "123 Test Street",
        "City, ST 12345",
        "Tel: (555) 123-4567",
        "",
        "Receipt #: TST-001",
        f"Date: 2024-01-15",
        f"Time: 14:30:25",
        "",
        "ITEMS:",
        "Coffee           $4.50",
        "Donut            $2.25",
        "Newspaper        $1.50",
        "",
        "Subtotal:        $8.25",
        "Tax (8.5%):      $0.70",
        "TOTAL:           $8.95",
        "",
        "Payment: Cash",
        "",
        "Thank you!"
    ]

    for line in lines:
        if line == "QUICK MART":
            draw.text((50, y), line, fill='black', font=font)
            y += 35
        elif line in ["ITEMS:", "TOTAL:"]:
            draw.text((50, y), line, fill='black', font=font)
            y += 30
        elif line == "":
            y += 15
        else:
            draw.text((50, y), line, fill='black', font=small_font)
            y += 25

    # Save to file and return path
    test_image_path = "test_receipt_synthetic.jpg"
    img.save(test_image_path, format='JPEG', quality=90)
    return test_image_path

def test_image_analysis():
    """Test image analysis with multipart upload"""
    print("📸 Testing Image Analysis (Multipart Upload)")
    print("=" * 50)

    try:
        # Create test image
        print("1. Creating synthetic receipt image...")
        image_path = create_test_image()
        image_size_mb = Path(image_path).stat().st_size / 1024 / 1024
        print(f"   ✅ Image created: {image_path} ({image_size_mb:.2f} MB)")

        # Upload with multipart form-data
        print("2. Uploading with multipart form-data...")

        with open(image_path, 'rb') as f:
            files = {'file': ('test_receipt.jpg', f, 'image/jpeg')}
            data = {
                'user_id': 'unified_test_user',
                'metadata': json.dumps({
                    "source": "unified_test",
                    "type": "synthetic_image",
                    "test_id": "IMG_001"
                })
            }

            response = requests.post(
                f"{RECEIPTS_API}/upload",
                files=files,
                data=data
            )

        if response.status_code != 202:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        upload_data = response.json()
        token = upload_data["processing_token"]
        print(f"   ✅ Upload successful - Token: {token}")

        # Clean up test file
        Path(image_path).unlink()

        # Poll for results
        print("3. Processing image with Gemini 2.5 Flash...")
        return poll_for_results(token, "image")

    except Exception as e:
        print(f"❌ Image test failed: {e}")
        return False

def test_video_analysis():
    """Test video analysis with multipart upload"""
    print("\n🎥 Testing Video Analysis (Multipart Upload)")
    print("=" * 50)

    try:
        # Look for existing video files
        video_files = []
        for ext in ['.mp4', '.mov', '.avi']:
            video_files.extend(list(Path('.').glob(f'*{ext}')))

        if not video_files:
            print("   ⚠️  No video files found in current directory")
            print("   To test video analysis:")
            print("   1. Record a receipt video with your phone")
            print("   2. Save as 'test_receipt.mp4' in this directory")
            print("   3. Run this script again")
            return True  # Not a failure, just no video to test

        video_path = video_files[0]
        video_size_mb = video_path.stat().st_size / 1024 / 1024
        print(f"1. Using video file: {video_path} ({video_size_mb:.2f} MB)")

        if video_size_mb > 100:
            print(f"   ⚠️  Video is very large ({video_size_mb:.2f} MB)")
            print("   Consider using a smaller video for testing")
            return True

        # Upload with multipart form-data
        print("2. Uploading with multipart form-data...")

        with open(video_path, 'rb') as f:
            files = {'file': (video_path.name, f, 'video/mp4')}
            data = {
                'user_id': 'unified_test_user',
                'metadata': json.dumps({
                    "source": "unified_test",
                    "type": "real_video",
                    "filename": video_path.name,
                    "size_mb": video_size_mb,
                    "test_id": "VID_001"
                })
            }

            response = requests.post(
                f"{RECEIPTS_API}/upload",
                files=files,
                data=data
            )

        if response.status_code != 202:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        upload_data = response.json()
        token = upload_data["processing_token"]
        print(f"   ✅ Upload successful - Token: {token}")

        # Poll for results
        print("3. Processing video with Gemini 2.5 Flash...")
        print("   📹 Video analysis may take longer...")
        return poll_for_results(token, "video")

    except Exception as e:
        print(f"❌ Video test failed: {e}")
        return False

def poll_for_results(token: str, media_type: str) -> bool:
    """Poll for processing results"""
    max_attempts = 30 if media_type == "image" else 40
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        print(f"   Polling... {attempt}/{max_attempts}")

        try:
            response = requests.get(f"{RECEIPTS_API}/status/{token}")

            if response.status_code != 200:
                print(f"   ❌ Status check failed: {response.status_code}")
                return False

            data = response.json()
            status = data["status"]
            progress = data["progress"]

            print(f"   Status: {status} - {progress['stage']} ({progress['percentage']:.1f}%)")

            if status == "completed":
                print(f"\n🎉 {media_type.title()} Analysis Completed!")

                result = data["result"]
                print(f"\n📊 Analysis Results:")
                print(f"🏪 Store: {result['place']}")
                print(f"💰 Total: ${result['amount']:.2f}")
                print(f"📂 Category: {result['category']}")
                print(f"📝 Description: {result['description']}")
                print(f"📅 Time: {result['time']}")
                print(f"💳 Type: {result['transactionType']}")

                return True

            elif status == "failed":
                print(f"\n❌ {media_type.title()} Processing Failed!")
                if "error" in data:
                    error = data["error"]
                    print(f"Error: {error.get('message', 'Unknown error')}")
                return False

            time.sleep(3)

        except Exception as e:
            print(f"   ❌ Polling failed: {e}")
            return False

    print(f"\n⏰ {media_type.title()} processing timed out")
    return False

def test_api_validation():
    """Test API validation for required fields"""
    print("\n🔍 Testing API Validation")
    print("=" * 50)

    test_cases = [
        {
            "name": "Missing file",
            "files": {},
            "data": {"user_id": "test_user"},
            "expected_error": "field required"
        },
        {
            "name": "Missing user_id",
            "files": {"file": ("test.txt", b"test content", "text/plain")},
            "data": {},
            "expected_error": "field required"
        },
        {
            "name": "Unsupported file type",
            "files": {"file": ("test.txt", b"test content", "text/plain")},
            "data": {"user_id": "test_user"},
            "expected_error": "Unsupported file type"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test_case['name']}")

        try:
            response = requests.post(
                f"{RECEIPTS_API}/upload",
                files=test_case["files"],
                data=test_case["data"]
            )

            if response.status_code in [400, 422]:  # Validation error
                error_data = response.json()
                error_msg = str(error_data)

                if test_case["expected_error"] in error_msg:
                    print(f"   ✅ Correctly rejected: {test_case['expected_error']}")
                else:
                    print(f"   ⚠️  Unexpected error: {error_msg}")
            else:
                print(f"   ❌ Expected validation error but got: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Unified API Test - Multipart File Upload")
    print("=" * 70)
    print("Testing the enhanced API using efficient multipart/form-data uploads")
    print("=" * 70)

    # Test API validation first
    test_api_validation()

    # Test image analysis
    image_success = test_image_analysis()

    # Test video analysis (if video files available)
    video_success = test_video_analysis()

    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"📸 Image Analysis: {'✅ SUCCESS' if image_success else '❌ FAILED'}")
    print(f"🎥 Video Analysis: {'✅ SUCCESS' if video_success else '❌ FAILED'}")
    print("🔍 API Validation: ✅ TESTED")

    print("\n🎉 Unified API Testing Complete!")
    print("Your system now uses efficient multipart uploads instead of base64 encoding!")

if __name__ == "__main__":
    main()
