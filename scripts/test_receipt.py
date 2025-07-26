#!/usr/bin/env python3
"""
MVP testing script for Project Raseed receipt processing
Tests the complete FastAPI backend with realistic JSON stub responses

Usage: python scripts/test_receipt.py [--base-url URL]
"""

import asyncio
import aiohttp
import base64
import json
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.logging import get_logger

logger = get_logger("test_receipt_mvp")


class MVPReceiptTester:
    """Test MVP receipt processing functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token = "mvp-test-token-123"  # Mock token for MVP
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test health check endpoint"""
        logger.info("🏥 Testing MVP health check endpoint...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data['status']}")
                    logger.info(f"🏷️  Mode: {data.get('metrics', {}).get('mode', 'unknown')}")
                    return {"success": True, "data": data}
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return {"success": False, "status": response.status}
                    
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_test_image(self) -> str:
        """Create a simple test image in base64 format"""
        # Create a simple test image (1x1 PNG)
        test_image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI/hm"
            "K4fQAAAABJRU5ErkJggg=="
        )
        return base64.b64encode(test_image_bytes).decode()
    
    async def test_receipt_upload(self, image_base64: str = None) -> Optional[str]:
        """Test receipt upload and get processing token"""
        logger.info("📤 Testing MVP receipt upload...")
        
        try:
            if not image_base64:
                image_base64 = await self.create_test_image()
            
            # Upload request
            upload_data = {
                "image_base64": image_base64,
                "user_id": "mvp-test-user",
                "metadata": {
                    "source": "mvp_test_script",
                    "test_timestamp": time.time(),
                    "test_mode": "mvp"
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/receipts/upload",
                json=upload_data
            ) as response:
                
                if response.status == 202:
                    data = await response.json()
                    token = data["processing_token"]
                    logger.info(f"✅ Upload successful! Token: {token}")
                    logger.info(f"⏱️  Estimated time: {data['estimated_time']}s")
                    return token
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Upload failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return None
    
    async def poll_for_results(self, token: str, max_attempts: int = 20) -> Dict[str, Any]:
        """Poll processing status until completion or timeout"""
        logger.info(f"🔄 Polling for MVP results: {token}")
        
        for attempt in range(max_attempts):
            try:
                async with self.session.get(
                    f"{self.base_url}/api/v1/receipts/status/{token}"
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        status = data["status"]
                        progress = data["progress"]["percentage"]
                        
                        logger.info(f"📊 Status: {status} ({progress:.1f}%) - {data['progress']['message']}")
                        
                        if status == "completed":
                            result = data.get("result")
                            if result:
                                logger.info("🎉 Processing completed successfully!")
                                logger.info(f"🏪 Place: {result.get('place', 'Unknown')}")
                                logger.info(f"💰 Amount: ₹{result.get('amount', 0):.2f}")
                                logger.info(f"📂 Category: {result.get('category', 'Unknown')}")
                                logger.info(f"🔖 Transaction Type: {result.get('transactionType', 'Unknown')}")
                                
                                # Check for subscription details
                                if result.get('recurring') and result.get('subscription'):
                                    sub = result['subscription']
                                    logger.info(f"🔄 Subscription: {sub.get('name')} ({sub.get('recurrence')})")
                                
                                # Check for warranty details
                                if result.get('warranty') and result.get('warrantyDetails'):
                                    warranty = result['warrantyDetails']
                                    logger.info(f"🛡️  Warranty until: {warranty.get('validUntil')}")
                                
                            return {"success": True, "data": data}
                        elif status == "failed":
                            logger.error(f"❌ Processing failed: {data.get('error', {}).get('message', 'Unknown error')}")
                            return {"success": False, "data": data}
                    else:
                        logger.error(f"❌ Status check failed: {response.status}")
                        return {"success": False, "status": response.status}
                
                # Wait before next poll (shorter for MVP)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                await asyncio.sleep(2)
        
        logger.error("⏰ Polling timeout - max attempts reached")
        return {"success": False, "error": "timeout"}
    
    async def test_receipt_history(self) -> Dict[str, Any]:
        """Test receipt history endpoint"""
        logger.info("📚 Testing MVP receipt history...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/receipts/history?limit=5"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    receipts = data.get("receipts", [])
                    logger.info(f"✅ Retrieved {len(receipts)} receipts")
                    
                    # Display some receipt details
                    for i, receipt in enumerate(receipts[:3]):
                        logger.info(f"   Receipt {i+1}: {receipt.get('place', 'Unknown')} - ₹{receipt.get('amount', 0):.2f}")
                    
                    return {"success": True, "data": data}
                else:
                    logger.error(f"❌ History request failed: {response.status}")
                    return {"success": False, "status": response.status}
                    
        except Exception as e:
            logger.error(f"❌ History request error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_multiple_receipts(self, count: int = 3) -> Dict[str, Any]:
        """Test processing multiple receipts"""
        logger.info(f"🔄 Testing {count} concurrent MVP receipts...")
        
        results = {"successful": 0, "failed": 0, "tokens": []}
        
        # Upload multiple receipts
        for i in range(count):
            token = await self.test_receipt_upload()
            if token:
                results["tokens"].append(token)
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            # Small delay between uploads
            await asyncio.sleep(0.5)
        
        # Wait for all to complete
        if results["tokens"]:
            logger.info(f"⏳ Waiting for {len(results['tokens'])} receipts to process...")
            
            # Poll all tokens
            for token in results["tokens"]:
                await self.poll_for_results(token, max_attempts=15)
        
        logger.info(f"📊 Multiple receipt test: {results['successful']} successful, {results['failed']} failed")
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive MVP test suite"""
        logger.info("🚀 Starting comprehensive MVP receipt processing test")
        start_time = time.time()
        
        results = {
            "test_start": start_time,
            "health_check": {},
            "single_upload": {},
            "processing": {},
            "history": {},
            "multiple_receipts": {},
            "overall_success": False,
            "total_duration": 0
        }
        
        # Test 1: Health Check
        logger.info("\n" + "="*50)
        logger.info("TEST 1: Health Check")
        logger.info("="*50)
        results["health_check"] = await self.test_health_check()
        if not results["health_check"]["success"]:
            logger.error("❌ Health check failed, aborting tests")
            return results
        
        # Test 2: Single Receipt Upload
        logger.info("\n" + "="*50)
        logger.info("TEST 2: Single Receipt Upload")
        logger.info("="*50)
        token = await self.test_receipt_upload()
        results["single_upload"] = {"success": token is not None, "token": token}
        
        if not token:
            logger.error("❌ Upload failed, aborting processing tests")
            return results
        
        # Test 3: Processing Status Polling
        logger.info("\n" + "="*50)
        logger.info("TEST 3: Processing & Status Polling")
        logger.info("="*50)
        results["processing"] = await self.poll_for_results(token)
        
        # Test 4: Receipt History
        logger.info("\n" + "="*50)
        logger.info("TEST 4: Receipt History")
        logger.info("="*50)
        results["history"] = await self.test_receipt_history()
        
        # Test 5: Multiple Receipts
        logger.info("\n" + "="*50)
        logger.info("TEST 5: Multiple Receipt Processing")
        logger.info("="*50)
        results["multiple_receipts"] = await self.test_multiple_receipts(2)
        
        # Calculate overall success
        results["overall_success"] = all([
            results["health_check"]["success"],
            results["single_upload"]["success"],
            results["processing"]["success"],
            results["history"]["success"],
            results["multiple_receipts"]["successful"] > 0
        ])
        
        results["total_duration"] = time.time() - start_time
        
        # Print summary
        self._print_test_summary(results)
        
        return results
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "="*70)
        print("🧪 MVP TEST SUMMARY")
        print("="*70)
        
        status_emoji = "✅" if results["overall_success"] else "❌"
        print(f"{status_emoji} Overall Status: {'PASS' if results['overall_success'] else 'FAIL'}")
        print(f"⏱️  Total Duration: {results['total_duration']:.2f}s")
        print(f"🏷️  Mode: MVP (JSON Stubs)")
        
        print("\n📋 Individual Test Results:")
        test_results = [
            ("Health Check", results["health_check"]["success"]),
            ("Receipt Upload", results["single_upload"]["success"]),
            ("Processing & Polling", results["processing"]["success"]),
            ("History Retrieval", results["history"]["success"]),
            ("Multiple Receipts", results["multiple_receipts"].get("successful", 0) > 0)
        ]
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} {test_name}")
        
        # Show sample receipt data if available
        if results["processing"]["success"] and "data" in results["processing"]:
            processing_data = results["processing"]["data"]
            if "result" in processing_data:
                result = processing_data["result"]
                print(f"\n📊 Sample Receipt Analysis (MVP):")
                print(f"   🏪 Place: {result.get('place', 'Unknown')}")
                print(f"   💰 Amount: ₹{result.get('amount', 0):.2f}")
                print(f"   📂 Category: {result.get('category', 'Unknown')}")
                print(f"   🔖 Type: {result.get('transactionType', 'Unknown')}")
                print(f"   ⭐ Importance: {result.get('importance', 'Unknown')}")
                
                if result.get('recurring'):
                    print(f"   🔄 Recurring: Yes")
                if result.get('warranty'):
                    print(f"   🛡️  Warranty: Yes")
        
        # Performance stats
        if results["multiple_receipts"]:
            multi = results["multiple_receipts"]
            print(f"\n⚡ Performance:")
            print(f"   Multiple Receipts: {multi.get('successful', 0)}/{multi.get('successful', 0) + multi.get('failed', 0)}")
        
        print("="*70)


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test Project Raseed MVP receipt processing")
    parser.add_argument("--base-url", default="http://localhost:8080", 
                       help="Base URL for the API (default: http://localhost:8080)")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick test (skip multiple receipts)")
    
    args = parser.parse_args()
    
    logger.info(f"Starting MVP tests against: {args.base_url}")
    
    try:
        async with MVPReceiptTester(args.base_url) as tester:
            if args.quick:
                # Quick test - just health and single receipt
                logger.info("🏃‍♂️ Running quick test...")
                health = await tester.test_health_check()
                if health["success"]:
                    token = await tester.test_receipt_upload()
                    if token:
                        await tester.poll_for_results(token)
                        await tester.test_receipt_history()
            else:
                # Full comprehensive test
                results = await tester.run_comprehensive_test()
                sys.exit(0 if results["overall_success"] else 1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())