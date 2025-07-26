"""
Firestore service for Project Raseed
Handles all database operations with Firestore
MVP: Simplified operations for receipt analysis data
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import uuid

from google.cloud import firestore
from google.cloud.firestore import AsyncClient
from google.api_core.exceptions import NotFound

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import TokenData, ReceiptAnalysis, ProcessingStatus, ProcessingStage

settings = get_settings()
logger = get_logger(__name__)


class FirestoreService:
    """Async Firestore service for database operations"""

    def __init__(self):
        self.client: Optional[AsyncClient] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Firestore client"""
        try:
            if settings.use_firestore_emulator:
                # Use emulator for local development
                import os

                os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST
                logger.info(
                    f"Using Firestore emulator at {settings.FIRESTORE_EMULATOR_HOST}"
                )

            self.client = firestore.AsyncClient(
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                database=settings.FIRESTORE_DATABASE,
            )

            # Test connection
            await self._test_connection()
            self._initialized = True

            logger.info("✅ Firestore service initialized successfully (MVP mode)")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore: {e}")
            raise

    async def _test_connection(self):
        """Test Firestore connection"""
        try:
            # Try to read from a system collection
            test_doc = self.client.collection("_health").document("test")
            await test_doc.set({"timestamp": datetime.utcnow()}, merge=True)
            logger.debug("Firestore connection test successful")
        except Exception as e:
            logger.error(f"Firestore connection test failed: {e}")
            raise

    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized or not self.client:
            raise RuntimeError("Firestore service not initialized")

    # Token Operations
    async def create_token(self, user_id: str, expires_in_minutes: int = None) -> str:
        """Create a new processing token"""
        self._ensure_initialized()

        if expires_in_minutes is None:
            expires_in_minutes = settings.TOKEN_EXPIRY_MINUTES

        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

        token_data = TokenData(
            token=token,
            user_id=user_id,
            status=ProcessingStatus.UPLOADED,
            progress={
                "stage": ProcessingStage.UPLOAD,
                "percentage": 0.0,
                "message": "Receipt uploaded, processing queued",
                "estimated_remaining": expires_in_minutes * 60,
            },
            expires_at=expires_at,
        )

        try:
            doc_ref = self.client.collection("processing_tokens").document(token)
            await doc_ref.set(token_data.dict())

            logger.info(
                f"Token created: {token}",
                extra={
                    "token": token,
                    "user_id": user_id,
                    "expires_at": expires_at.isoformat(),
                },
            )

            return token

        except Exception as e:
            logger.error(
                f"Failed to create token: {e}",
                extra={"user_id": user_id, "error": str(e)},
            )
            raise

    async def get_token(self, token: str) -> Optional[TokenData]:
        """Get token data by token ID"""
        self._ensure_initialized()

        try:
            doc_ref = self.client.collection("processing_tokens").document(token)
            doc = await doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                return TokenData(**data)

            return None

        except Exception as e:
            logger.error(
                f"Failed to get token: {e}", extra={"token": token, "error": str(e)}
            )
            raise

    async def update_token_status(
        self,
        token: str,
        status: ProcessingStatus,
        progress: Dict[str, Any] = None,
        result: ReceiptAnalysis = None,  # Updated for MVP
        error: Dict[str, Any] = None,
    ) -> bool:
        """Update token status and progress"""
        self._ensure_initialized()

        try:
            doc_ref = self.client.collection("processing_tokens").document(token)

            # Prepare update data
            update_data = {"status": status.value, "updated_at": datetime.utcnow()}

            if progress:
                update_data["progress"] = progress

            if result:
                update_data["result"] = result.dict()
                update_data["processing_end_time"] = datetime.utcnow()

            if error:
                update_data["error"] = error
                update_data["processing_end_time"] = datetime.utcnow()

            # Update document
            await doc_ref.update(update_data)

            logger.info(
                f"Token status updated: {token}",
                extra={
                    "token": token,
                    "status": status.value,
                    "has_result": result is not None,
                    "has_error": error is not None,
                },
            )

            return True

        except NotFound:
            logger.warning(f"Token not found: {token}")
            return False
        except Exception as e:
            logger.error(
                f"Failed to update token: {e}",
                extra={"token": token, "status": status.value, "error": str(e)},
            )
            raise

    async def increment_retry_count(self, token: str) -> int:
        """Increment retry count for a token"""
        self._ensure_initialized()

        try:
            doc_ref = self.client.collection("processing_tokens").document(token)

            # Use atomic increment
            await doc_ref.update(
                {"retry_count": firestore.Increment(1), "updated_at": datetime.utcnow()}
            )

            # Get updated document to return new count
            doc = await doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("retry_count", 0)

            return 0

        except Exception as e:
            logger.error(
                f"Failed to increment retry count: {e}",
                extra={"token": token, "error": str(e)},
            )
            raise

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        self._ensure_initialized()

        try:
            # Use timezone-aware UTC for Firestore queries (Firestore prefers this)
            now = datetime.now(timezone.utc)

            # Query expired tokens
            query = (
                self.client.collection("processing_tokens")
                .where("expires_at", "<", now)
                .limit(100)
            )  # Process in batches

            docs = [doc async for doc in query.stream()]
            deleted_count = 0

            # Delete expired tokens
            batch = self.client.batch()
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1

            if deleted_count > 0:
                await batch.commit()
                logger.info(f"Cleaned up {deleted_count} expired tokens")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            raise

    # Receipt Operations (Updated for MVP)
    async def save_receipt(self, receipt_data: ReceiptAnalysis) -> str:
        """Save analyzed receipt to database"""
        self._ensure_initialized()

        try:
            receipt_id = receipt_data.receipt_id

            # Save to receipts collection
            doc_ref = self.client.collection("receipts").document(receipt_id)
            receipt_dict = receipt_data.dict()
            receipt_dict.update(
                {"created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            )

            await doc_ref.set(receipt_dict)

            logger.info(
                f"Receipt saved: {receipt_id}",
                extra={
                    "receipt_id": receipt_id,
                    "place": receipt_data.place,
                    "amount": receipt_data.amount,
                    "category": receipt_data.category,
                },
            )

            return receipt_id

        except Exception as e:
            logger.error(
                f"Failed to save receipt: {e}",
                extra={
                    "receipt_id": getattr(receipt_data, "receipt_id", "unknown"),
                    "error": str(e),
                },
            )
            raise

    async def get_receipt(self, receipt_id: str) -> Optional[ReceiptAnalysis]:
        """Get receipt by ID"""
        self._ensure_initialized()

        try:
            doc_ref = self.client.collection("receipts").document(receipt_id)
            doc = await doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                # Remove Firestore timestamps for Pydantic parsing
                data.pop("created_at", None)
                data.pop("updated_at", None)
                return ReceiptAnalysis(**data)

            return None

        except Exception as e:
            logger.error(
                f"Failed to get receipt: {e}",
                extra={"receipt_id": receipt_id, "error": str(e)},
            )
            raise

    async def get_user_receipts(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[ReceiptAnalysis]:
        """Get receipts for a user (MVP: simplified query)"""
        self._ensure_initialized()

        try:
            # Note: In MVP, we don't store user_id in receipt documents
            # This would need to be added for proper user isolation
            query = (
                self.client.collection("receipts")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )

            docs = [doc async for doc in query.stream()]
            receipts = []

            for doc in docs:
                data = doc.to_dict()
                # Remove Firestore timestamps for Pydantic parsing
                data.pop("created_at", None)
                data.pop("updated_at", None)
                try:
                    receipts.append(ReceiptAnalysis(**data))
                except Exception as parse_error:
                    logger.warning(f"Failed to parse receipt {doc.id}: {parse_error}")
                    continue

            logger.info(
                f"Retrieved {len(receipts)} receipts (MVP)",
                extra={"user_id": user_id, "limit": limit, "offset": offset},
            )

            return receipts

        except Exception as e:
            logger.error(
                f"Failed to get user receipts: {e}",
                extra={"user_id": user_id, "error": str(e)},
            )
            raise

    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Health check for Firestore service"""
        try:
            # Check initialization status
            if not self._initialized:
                logger.warning("Firestore health check: Service not initialized")
                return {"status": "unhealthy", "error": "Not initialized"}

            if not self.client:
                logger.warning("Firestore health check: Client is None")
                return {"status": "unhealthy", "error": "Client not available"}

            # Test basic operations with detailed logging
            start_time = datetime.utcnow()
            logger.debug("Firestore health check: Starting test write")

            test_doc = self.client.collection("_health").document("check")
            await test_doc.set({"timestamp": start_time}, merge=True)

            logger.debug("Firestore health check: Test write successful")

            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000

            logger.debug(
                f"Firestore health check: Completed successfully, latency: {latency}ms"
            )

            return {
                "status": "healthy",
                "mode": "mvp",
                "latency_ms": round(latency, 2),
                "emulator_mode": settings.use_firestore_emulator,
            }

        except Exception as e:
            logger.error(f"Firestore health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close Firestore connection"""
        if self.client:
            self.client.close()
            self._initialized = False
            logger.info("Firestore service closed")


# Global service instance
firestore_service = FirestoreService()
