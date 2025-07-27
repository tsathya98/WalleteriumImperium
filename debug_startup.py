#!/usr/bin/env python3
"""
Debug script to test service initialization and health checks locally
Run this before deploying to identify any startup issues
"""

import asyncio
import sys
import os
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.firestore_service import FirestoreService
from app.services.token_service import TokenService
from app.core.config import settings
from app.core.logging import setup_logging

# Setup logging
setup_logging("DEBUG")

async def test_service_initialization():
    """Test all service initialization steps"""
    print("🧪 Testing WalleteriumImperium Service Initialization")
    print("=" * 50)
    
    try:
        # Test 1: Firestore Service
        print("1️⃣ Testing Firestore Service...")
        firestore_service = FirestoreService()
        await firestore_service.initialize()
        
        firestore_health = await firestore_service.health_check()
        print(f"   ✅ Firestore Health: {firestore_health}")
        
        # Test 2: Token Service
        print("2️⃣ Testing Token Service...")
        token_service = TokenService(firestore_service=firestore_service)
        await token_service.initialize()
        
        token_health = await token_service.health_check()
        print(f"   ✅ Token Service Health: {token_health}")
        
        # Test 3: Overall Health
        print("3️⃣ Testing Overall Health...")
        overall_healthy = (
            firestore_health.get("status") == "healthy" and
            token_health.get("status") == "healthy"
        )
        
        if overall_healthy:
            print("   ✅ All services healthy!")
        else:
            print("   ❌ Some services unhealthy")
            
        # Test 4: Cleanup
        print("4️⃣ Testing Cleanup...")
        await token_service.shutdown()
        await firestore_service.close()
        print("   ✅ Cleanup successful")
        
        return overall_healthy
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_health_endpoints():
    """Test health endpoint logic without FastAPI"""
    print("\n🏥 Testing Health Check Logic")
    print("=" * 30)
    
    try:
        # Initialize services
        firestore_service = FirestoreService()
        await firestore_service.initialize()
        
        token_service = TokenService(firestore_service=firestore_service)
        await token_service.initialize()
        
        # Test individual health checks
        firestore_health = await firestore_service.health_check()
        token_service_health = await token_service.health_check()
        
        print(f"Firestore Health: {firestore_health}")
        print(f"Token Service Health: {token_service_health}")
        
        # Test overall status logic
        firestore_status = firestore_health.get("status", "unknown")
        token_service_status = token_service_health.get("status", "unknown")
        
        overall_status = (
            "healthy"
            if all(
                status == "healthy"
                for status in [firestore_status, token_service_status]
            )
            else "unhealthy"
        )
        
        print(f"Overall Status: {overall_status}")
        
        # Cleanup
        await token_service.shutdown()
        await firestore_service.close()
        
        return overall_status == "healthy"
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_environment_info():
    """Print environment configuration"""
    print("\n🔧 Environment Configuration")
    print("=" * 30)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Port: {settings.PORT}")
    print(f"Project ID: {settings.GOOGLE_CLOUD_PROJECT_ID}")
    print(f"Vertex AI Location: {settings.VERTEX_AI_LOCATION}")
    print(f"Use Emulators: {settings.USE_EMULATORS}")
    print(f"Firestore Emulator: {settings.FIRESTORE_EMULATOR_HOST}")

async def main():
    """Main debug function"""
    print_environment_info()
    
    # Test service initialization
    init_success = await test_service_initialization()
    
    # Test health endpoints
    health_success = await test_health_endpoints()
    
    print("\n📊 Summary")
    print("=" * 20)
    print(f"Service Initialization: {'✅ PASS' if init_success else '❌ FAIL'}")
    print(f"Health Check Logic: {'✅ PASS' if health_success else '❌ FAIL'}")
    
    if init_success and health_success:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("\n❌ Some tests failed. Fix issues before deploying.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 