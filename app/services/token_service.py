"""
Enhanced Token service for receipt processing
Manages token-based processing workflow with hybrid agentic agent
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from app.services.firestore_service import FirestoreService


class TokenService:
    """Enhanced token service for managing receipt processing tokens with raw bytes (SYNC VERSION)"""

    def __init__(self, firestore_service: FirestoreService = None):
        """Initialize token service with dependency injection"""
        self._firestore_service = firestore_service
        self._processing_tasks: Dict[str, Any] = {}  # Simple dict instead of async tasks
        self._initialized = False
        
        print(f"🎫 Initializing Enhanced Token Service (SYNC VERSION)")

    def initialize(self):
        """Initialize the service (SYNC VERSION)"""
        try:
            if not self._firestore_service:
                raise RuntimeError("FirestoreService dependency not provided")

            self._initialized = True
            print("✅ Enhanced token service initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize token service: {e}")
            raise

    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Token service not initialized")

    def create_processing_token(
        self, user_id: str, media_bytes: bytes, media_type: str
    ) -> str:
        """Create a new processing token and start processing with raw bytes (SYNC VERSION)"""
        self._ensure_initialized()

        try:
            # Create token in database using injected service
            # For sync version, we'll use a simple token generation
            token = f"proc_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            print(f"🎫 Processing token created with raw bytes")
            print(f"   Token: {token}")
            print(f"   User: {user_id}")
            print(f"   Media type: {media_type}")
            print(f"   Size: {len(media_bytes) / 1024:.1f} KB")

            # For sync processing, we'll process immediately
            result = self._process_receipt_sync(token, user_id, media_bytes, media_type)
            
            # Store the result
            self._processing_tasks[token] = {
                "status": "completed" if result["status"] == "success" else "failed",
                "result": result,
                "created_at": datetime.utcnow(),
                "user_id": user_id
            }

            return token

        except Exception as e:
            print(f"❌ Failed to create processing token: {e}")
            raise

    def get_token_status(self, token: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a processing token (SYNC VERSION)"""
        self._ensure_initialized()

        try:
            # Check our local storage first for sync processing
            if token in self._processing_tasks:
                task_data = self._processing_tasks[token]
                
                # Simple expiry check (10 minutes)
                if datetime.utcnow() - task_data["created_at"] > timedelta(minutes=10):
                    print(f"⏰ Token expired: {token}")
                    del self._processing_tasks[token]
                    return None
                
                return {
                    "status": task_data["status"],
                    "result": task_data["result"].get("data") if task_data["status"] == "completed" else None,
                    "error": task_data["result"].get("error") if task_data["status"] == "failed" else None,
                    "progress": {
                        "stage": "completed" if task_data["status"] == "completed" else "failed",
                        "percentage": 100.0,
                        "message": "Processing completed successfully!" if task_data["status"] == "completed" else "Processing failed"
                    }
                }

            return None

        except Exception as e:
            print(f"❌ Failed to get token status: {e} (token: {token})")
            raise

    def _process_receipt_sync(
        self, token: str, user_id: str, media_bytes: bytes, media_type: str
    ) -> Dict[str, Any]:
        """
        Synchronous receipt processing with raw bytes (MUCH SIMPLER!)
        """
        try:
            print(f"🚀 Starting sync receipt processing")
            print(f"   Token: {token}")
            print(f"   User: {user_id}")

            # Process with Enhanced Receipt Scanner Agent (SYNC VERSION)
            from agents.receipt_scanner.agent import get_enhanced_receipt_scanner_agent
            
            enhanced_agent = get_enhanced_receipt_scanner_agent()
            print(f"DEBUG TokenService: About to call enhanced_agent with media_type: {media_type!r}")
            print(f"DEBUG TokenService: media_bytes size: {len(media_bytes)} bytes")
            print(f"DEBUG TokenService: user_id: {user_id!r}")
            
            # SYNC CALL - much simpler!
            ai_result = enhanced_agent.analyze_receipt_media(
                media_bytes, media_type, user_id
            )
            
            if ai_result["status"] == "success":
                print(f"✅ Sync receipt processing completed")
                print(f"   Token: {token}")
                return ai_result
            else:
                raise ValueError(f"Enhanced agent failed: {ai_result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Sync processing failed")
            print(f"   Token: {token}")
            print(f"   User: {user_id}")
            print(f"   Error: {e}")
            
            return {
                "status": "failed",
                "error": str(e)
            }

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics (SYNC VERSION)"""
        try:
            completed = sum(1 for task in self._processing_tasks.values() if task["status"] == "completed")
            failed = sum(1 for task in self._processing_tasks.values() if task["status"] == "failed")
            
            return {
                "total_processed": len(self._processing_tasks),
                "completed": completed,
                "failed": failed,
                "success_rate": completed / len(self._processing_tasks) * 100 if self._processing_tasks else 0
            }

        except Exception as e:
            print(f"Failed to get processing stats: {e}")
            return {}

    def cleanup_expired_tokens(self):
        """Clean up expired tokens (SYNC VERSION)"""
        try:
            now = datetime.utcnow()
            expired_tokens = [
                token for token, data in self._processing_tasks.items()
                if now - data["created_at"] > timedelta(minutes=10)
            ]
            
            for token in expired_tokens:
                del self._processing_tasks[token]
            
            if expired_tokens:
                print(f"Cleaned up {len(expired_tokens)} expired tokens")

        except Exception as e:
            print(f"Cleanup error: {e}")

    def shutdown(self):
        """Shutdown token service gracefully (SYNC VERSION)"""
        print("Shutting down token service...")
        self._processing_tasks.clear()
        self._initialized = False
        print("Token service shutdown complete")


# Global service instance for backward compatibility
token_service = TokenService()
