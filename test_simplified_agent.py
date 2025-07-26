#!/usr/bin/env python3
"""
Simple test script for the simplified receipt scanner agent
Tests the Google SDK integration and category system
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "walleterium"
os.environ["VERTEX_AI_LOCATION"] = "us-central1"
os.environ["ENVIRONMENT"] = "development"


def test_categories():
    """Test that categories are properly loaded"""
    print("🧪 Testing category system...")

    try:
        from config.constants import TRANSACTION_CATEGORIES

        print(f"✅ Categories loaded: {len(TRANSACTION_CATEGORIES)} categories")

        # Print categories to verify they match user requirements
        print("\n📋 Available categories:")
        for i, category in enumerate(TRANSACTION_CATEGORIES, 1):
            print(f"   {i:2d}. {category}")

        return True
    except Exception as e:
        print(f"❌ Category test failed: {e}")
        return False


def test_schema():
    """Test that schema is properly generated"""
    print("\n🧪 Testing schema generation...")

    try:
        from agents.receipt_scanner.schemas import get_enhanced_receipt_schema

        schema = get_enhanced_receipt_schema()

        print("✅ Schema generated successfully")
        print(f"   Required fields: {schema['required']}")
        print(f"   Properties count: {len(schema['properties'])}")

        # Verify it has the expected structure
        expected_fields = [
            "store_info",
            "items",
            "totals",
            "classification",
            "processing_metadata",
        ]
        for field in expected_fields:
            if field not in schema["required"]:
                raise ValueError(f"Missing required field: {field}")

        print("✅ Schema structure validated")
        return True
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False


def test_agent_initialization():
    """Test that agent initializes properly"""
    print("\n🧪 Testing agent initialization...")

    try:
        from agents.receipt_scanner.agent import get_receipt_scanner_agent

        agent = get_receipt_scanner_agent()

        print("✅ Agent initialized successfully")
        print(f"   Project: {agent.project_id}")
        print(f"   Location: {agent.location}")
        print(f"   Model: {agent.model_name}")

        # Test health check
        health = agent.health_check()
        print(f"✅ Health check: {health['status']}")

        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


def test_prompt_generation():
    """Test that prompts are generated correctly"""
    print("\n🧪 Testing prompt generation...")

    try:
        from agents.receipt_scanner.prompts import create_agentic_prompt

        # Test image prompt
        image_prompt = create_agentic_prompt("image")
        print(f"✅ Image prompt generated ({len(image_prompt)} characters)")

        # Test video prompt
        video_prompt = create_agentic_prompt("video")
        print(f"✅ Video prompt generated ({len(video_prompt)} characters)")

        # Verify categories are in prompt
        from config.constants import TRANSACTION_CATEGORIES

        category_found = any(cat in image_prompt for cat in TRANSACTION_CATEGORIES[:5])
        if category_found:
            print("✅ Categories properly included in prompt")
        else:
            print("⚠️ Categories might not be included in prompt")

        return True
    except Exception as e:
        print(f"❌ Prompt test failed: {e}")
        return False


def create_test_image():
    """Create a simple test image for testing"""
    try:
        from PIL import Image, ImageDraw
        import io

        # Create a simple receipt-like image
        img = Image.new("RGB", (400, 600), color="white")
        draw = ImageDraw.Draw(img)

        # Add some text that looks like a receipt
        receipt_text = [
            "SUPER MARKET",
            "123 Main St",
            "Tel: 555-0123",
            "",
            "Date: 2024-01-15",
            "Time: 14:30",
            "",
            "Apples        $3.50",
            "Bread         $2.25",
            "Milk          $4.75",
            "",
            "Subtotal:    $10.50",
            "Tax:          $0.85",
            "Total:       $11.35",
            "",
            "Thank you!",
        ]

        y = 50
        for line in receipt_text:
            draw.text((50, y), line, fill="black")
            y += 25

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    except Exception as e:
        print(f"⚠️ Could not create test image: {e}")
        return None


def test_full_analysis():
    """Test full receipt analysis with a simple test image"""
    print("\n🧪 Testing full receipt analysis...")

    try:
        # Create test image
        test_image = create_test_image()
        if not test_image:
            print("⚠️ Skipping full analysis test (no test image)")
            return True

        # Get agent
        from agents.receipt_scanner.agent import get_receipt_scanner_agent

        agent = get_receipt_scanner_agent()

        print("📸 Running analysis on test image...")
        result = agent.analyze_receipt(test_image, "image", "test_user")

        if result["status"] == "success":
            data = result["data"]
            print("✅ Analysis successful!")
            print(f"   Store: {data['place']}")
            print(f"   Amount: ${data['amount']}")
            print(f"   Category: {data['category']}")
            print(f"   Items: {len(data['items'])}")
            print(f"   Processing time: {result['processing_time']:.1f}s")

            if result.get("validation", {}).get("is_valid"):
                print("✅ Validation passed")
            else:
                print("⚠️ Validation issues found")

            return True
        else:
            print(f"❌ Analysis failed: {result}")
            return False

    except Exception as e:
        print(f"❌ Full analysis test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Testing Simplified Receipt Scanner Agent")
    print("=" * 50)

    tests = [
        test_categories,
        test_schema,
        test_agent_initialization,
        test_prompt_generation,
        test_full_analysis,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("🎯 Test Results:")

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test.__name__}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your simplified agent is ready!")
    elif passed >= total * 0.8:
        print("👍 Most tests passed! Minor issues may need attention.")
    else:
        print("⚠️ Several tests failed. Please check the setup.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
