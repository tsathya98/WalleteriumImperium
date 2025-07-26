#!/usr/bin/env python3
"""
Test script for real receipt media (images and videos)
Upload and analyze actual receipt photos or videos
"""

import json
import time
import requests
from pathlib import Path

# API Configuration
API_BASE = "http://localhost:8080/api/v1"
RECEIPTS_API = f"{API_BASE}/receipts"


def get_file_info(file_path: str) -> tuple[float, str]:
    """Get file size and appropriate MIME type"""
    try:
        file_size_mb = Path(file_path).stat().st_size / 1024 / 1024
        file_extension = Path(file_path).suffix.lower()

        # Determine MIME type
        if file_extension in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif file_extension == ".png":
            mime_type = "image/png"
        elif file_extension == ".gif":
            mime_type = "image/gif"
        elif file_extension in [".mp4"]:
            mime_type = "video/mp4"
        elif file_extension in [".mov"]:
            mime_type = "video/quicktime"
        elif file_extension in [".avi"]:
            mime_type = "video/avi"
        else:
            mime_type = "application/octet-stream"

        return file_size_mb, mime_type
    except Exception as e:
        raise ValueError(f"Failed to get file info for {file_path}: {str(e)}")


def analyze_real_receipt(media_path: str, user_id: str = "real_test_user"):
    """Analyze a real receipt image or video"""

    # Determine media type from file extension
    media_path_obj = Path(media_path)
    extension = media_path_obj.suffix.lower()

    if extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
        media_type = "image"
        icon = "📸"
    elif extension in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
        media_type = "video"
        icon = "🎥"
    else:
        print(f"❌ Unsupported file type: {extension}")
        print("Supported: Images (.jpg, .png) and Videos (.mp4, .mov, .avi)")
        return

    print(f"{icon} Analyzing Real Receipt {media_type.title()}: {media_path}")
    print("=" * 60)

    try:
        # Check if media file exists
        if not Path(media_path).exists():
            print(f"❌ {media_type.title()} file not found: {media_path}")
            return

        # Get file info
        print(f"1. Preparing {media_type} for upload...")
        file_size_mb, mime_type = get_file_info(media_path)
        print(f"   ✅ {media_type.title()} ready: {file_size_mb:.2f} MB ({mime_type})")

        size_limit = 10 if media_type == "image" else 100
        if file_size_mb > size_limit:
            print(
                f"   ⚠️  Warning: {media_type.title()} is large ({file_size_mb:.2f} MB)"
            )

        # Upload receipt with multipart form-data
        print(f"2. Uploading receipt {media_type} with multipart form-data...")

        with open(media_path, "rb") as f:
            files = {"file": (Path(media_path).name, f, mime_type)}
            data = {
                "user_id": user_id,
                "metadata": json.dumps(
                    {
                        "source": f"real_{media_type}_test",
                        "filename": Path(media_path).name,
                        "size_mb": file_size_mb,
                        "media_type": media_type,
                    }
                ),
            }

            upload_response = requests.post(
                f"{RECEIPTS_API}/upload", files=files, data=data
            )

        if upload_response.status_code != 202:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text}")
            return

        upload_data = upload_response.json()
        token = upload_data["processing_token"]
        print(f"   ✅ Upload successful - Token: {token}")

        # Poll for results
        print("3. Processing receipt with Gemini 2.5 Flash...")
        if media_type == "video":
            print("   📹 Video analysis may take longer than images...")
        max_attempts = 30 if media_type == "image" else 40  # Videos might take longer
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

            print(
                f"   Status: {status} - {progress['stage']} ({progress['percentage']:.1f}%)"
            )

            if status == "completed":
                print("\n🎉 Analysis Completed!")

                # Display detailed results
                result = status_data["result"]
                print("\n📊 Receipt Analysis Results:")
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
                output_file = f"real_receipt_result_{Path(media_path).stem}.json"
                with open(output_file, "w") as f:
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

            time.sleep(3)  # Wait a bit longer for real media

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
    test_media = [
        "receipt1.jpg",
        "receipt2.png",
        "receipt.jpeg",
        "test_receipt.jpg",
        "receipt_video.mp4",
        "receipt.mov",
    ]

    print("Looking for receipt images and videos in current directory...")

    # Find available media
    available_media = []
    for media in test_media:
        if Path(media).exists():
            available_media.append(media)
            ext = Path(media).suffix.lower()
            media_type = "📸 Image" if ext in [".jpg", ".jpeg", ".png"] else "🎥 Video"
            print(f"✅ Found {media_type}: {media}")

    if not available_media:
        print("\n❌ No receipt images or videos found!")
        print("\nTo test with real receipts:")
        print("1. Take a photo/video of a receipt with your phone")
        print("2. Save it as 'receipt.jpg' or 'receipt.mp4' in this directory")
        print("3. Run this script again")
        print("\nOr specify a custom path:")
        print("python test_real_receipt.py path/to/your/receipt.jpg")
        print("python test_real_receipt.py path/to/your/receipt.mp4")
        return

    # Analyze each available media
    for media_path in available_media:
        analyze_real_receipt(media_path)
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Custom image path provided
        custom_path = sys.argv[1]
        analyze_real_receipt(custom_path)
    else:
        # Look for images in current directory
        main()
