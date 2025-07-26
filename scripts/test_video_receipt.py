#!/usr/bin/env python3
"""
Test script for Video Receipt Analysis
Tests video processing capabilities with Gemini 2.5 Flash using multipart uploads
"""

import asyncio
import json
import time
import requests
from pathlib import Path

# API Configuration
API_BASE = "http://localhost:8080/api/v1"
RECEIPTS_API = f"{API_BASE}/receipts"

def get_video_info(video_path: str) -> tuple[float, str]:
    """Get video file size and MIME type"""
    try:
        file_size_mb = Path(video_path).stat().st_size / 1024 / 1024
        file_extension = Path(video_path).suffix.lower()

        # Determine MIME type
        if file_extension == '.mp4':
            mime_type = 'video/mp4'
        elif file_extension == '.mov':
            mime_type = 'video/quicktime'
        elif file_extension == '.avi':
            mime_type = 'video/avi'
        elif file_extension == '.mkv':
            mime_type = 'video/x-matroska'
        elif file_extension == '.webm':
            mime_type = 'video/webm'
        else:
            mime_type = 'video/mp4'  # Default fallback

        return file_size_mb, mime_type
    except Exception as e:
        raise ValueError(f"Failed to get video info for {video_path}: {str(e)}")

def analyze_video_receipt(video_path: str, user_id: str = "video_test_user"):
    """Analyze a video receipt"""
    print(f"🎥 Analyzing Video Receipt: {video_path}")
    print("=" * 60)

    try:
        # Check if video exists
        if not Path(video_path).exists():
            print(f"❌ Video file not found: {video_path}")
            return

        # Get video info
        print("1. Preparing video for upload...")
        video_size_mb, mime_type = get_video_info(video_path)
        print(f"   ✅ Video ready: {video_size_mb:.2f} MB ({mime_type})")

        if video_size_mb > 100:
            print(f"   ⚠️  Warning: Video is very large ({video_size_mb:.2f} MB)")
            print("   Consider compressing the video for faster processing")

        # Upload video receipt with multipart form-data
        print("2. Uploading video receipt with multipart form-data...")

        with open(video_path, 'rb') as f:
            files = {'file': (Path(video_path).name, f, mime_type)}
            data = {
                'user_id': user_id,
                'metadata': json.dumps({
                    "source": "video_test",
                    "filename": Path(video_path).name,
                    "size_mb": video_size_mb,
                    "media_type": "video"
                })
            }

            upload_response = requests.post(
                f"{RECEIPTS_API}/upload",
                files=files,
                data=data
            )

        if upload_response.status_code != 202:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text}")
            return

        upload_data = upload_response.json()
        token = upload_data["processing_token"]
        print(f"   ✅ Upload successful - Token: {token}")
        print(f"   📊 Estimated processing time: {upload_data['estimated_time']}s")

        # Poll for results (videos may take longer)
        print("3. Processing video with Gemini 2.5 Flash...")
        print("   📹 Video analysis may take longer than images...")
        max_attempts = 40  # Videos might take longer (2 minutes max)
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
            print(f"   Message: {progress['message']}")

            if status == "completed":
                print("\n🎉 Video Analysis Completed!")

                # Display detailed results
                result = status_data["result"]
                print(f"\n📊 Video Receipt Analysis Results:")
                print(f"🏪 Store: {result['place']}")
                print(f"💰 Total Amount: ${result['amount']:.2f}")
                print(f"📂 Category: {result['category']}")
                print(f"📝 Description: {result['description']}")
                print(f"📅 Transaction Time: {result['time']}")
                print(f"💳 Transaction Type: {result['transactionType']}")
                print(f"⭐ Importance: {result.get('importance', 'N/A')}")
                print(f"🔄 Recurring: {result.get('recurring', False)}")
                print(f"🛡️ Warranty: {result.get('warranty', False)}")

                # Performance metrics
                print(f"\n📈 Performance Metrics:")
                print(f"   Video Size: {video_size_mb:.2f} MB")
                print(f"   Processing Time: {attempt * 3}s")
                print(f"   Attempts: {attempt}")

                # Save detailed result
                output_file = f"video_receipt_result_{Path(video_path).stem}.json"
                with open(output_file, 'w') as f:
                    json.dump(status_data, f, indent=2, default=str)
                print(f"\n💾 Full analysis saved to: {output_file}")

                return status_data

            elif status == "failed":
                print("\n❌ Video Processing Failed!")
                if "error" in status_data:
                    error = status_data["error"]
                    print(f"Error Code: {error.get('code', 'Unknown')}")
                    print(f"Error Message: {error.get('message', 'Unknown')}")
                break

            time.sleep(3)  # Wait 3 seconds between polls

        if attempt >= max_attempts:
            print("\n⏰ Video processing timed out")
            print("   Large videos may require more time")

    except Exception as e:
        print(f"❌ Video analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()

def create_test_video():
    """Create a simple test video (requires OpenCV)"""
    print("🎬 Creating test video...")

    try:
        import cv2
        import numpy as np

        # Create a simple video with receipt-like content
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter('test_receipt_video.mp4', fourcc, 1.0, (640, 480))

        # Create frames with receipt content
        for frame_num in range(10):  # 10 second video at 1 FPS
            # Create white background
            frame = np.full((480, 640, 3), 255, dtype=np.uint8)

            # Add receipt text
            receipt_lines = [
                "SAMPLE STORE",
                "123 Main Street",
                "Receipt #: 12345",
                "",
                "Coffee          $4.50",
                "Sandwich        $8.99",
                "Tax             $1.08",
                "",
                f"Total          $14.57",
                "",
                "Thank you!"
            ]

            y_offset = 50
            for line in receipt_lines:
                cv2.putText(frame, line, (50, y_offset),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                y_offset += 35

            # Add frame number
            cv2.putText(frame, f"Frame {frame_num + 1}", (500, 450),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

            video.write(frame)

        video.release()
        print("   ✅ Test video created: test_receipt_video.mp4")
        return "test_receipt_video.mp4"

    except ImportError:
        print("   ⚠️  OpenCV not available for video creation")
        print("   Install with: pip install opencv-python")
        return None
    except Exception as e:
        print(f"   ❌ Failed to create test video: {e}")
        return None

def compare_video_vs_image_analysis():
    """Compare video analysis vs image analysis performance"""
    print("🔬 Video vs Image Analysis Comparison")
    print("=" * 60)

    # This would require having both a video and image of the same receipt
    print("To run this comparison:")
    print("1. Record a video of a receipt")
    print("2. Take a photo of the same receipt")
    print("3. Analyze both and compare accuracy/performance")
    print("4. Expected: Video may be more accurate but slower")

def main():
    """Main test function"""
    print("🎥 Video Receipt Analysis Test")
    print("=" * 60)

    # Check for video files in common locations
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    test_videos = []

    # Look for videos in current directory
    for ext in video_extensions:
        videos = list(Path('.').glob(f'*{ext}'))
        test_videos.extend(videos)

    # Look for videos in docs/video_samples
    video_samples_dir = Path('../docs/video_samples')
    if video_samples_dir.exists():
        for ext in video_extensions:
            videos = list(video_samples_dir.glob(f'*{ext}'))
            test_videos.extend(videos)

    if test_videos:
        print("Found video files:")
        for i, video in enumerate(test_videos, 1):
            print(f"  {i}. {video}")

        print("\nTesting first video...")
        analyze_video_receipt(str(test_videos[0]))
    else:
        print("❌ No video files found!")
        print("\nTo test video analysis:")
        print("1. Record a video of a receipt with your phone")
        print("2. Save it in this directory or docs/video_samples/")
        print("3. Run this script again")
        print("\nOr create a test video:")

        test_video = create_test_video()
        if test_video:
            print(f"\nTesting created video: {test_video}")
            analyze_video_receipt(test_video)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Custom video path provided
        custom_path = sys.argv[1]
        analyze_video_receipt(custom_path)
    else:
        # Look for videos automatically
        main()
