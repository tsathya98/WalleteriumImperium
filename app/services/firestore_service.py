"""
Firestore service for Project Raseed
Handles all database operations with Firestore
MVP: Simplified operations for receipt analysis data
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import uuid
import asyncio

from google.cloud import firestore
from google.cloud.firestore import AsyncClient
from google.api_core.exceptions import NotFound
from vertexai.generative_models import Content

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import TokenData, ReceiptAnalysis, ProcessingStatus, ProcessingStage
from agents.onboarding_agent.schemas import UserProfile

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

    # Onboarding Agent Operations
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieves a user profile from Firestore."""
        self._ensure_initialized()
        logger.debug(f"Getting user profile for user_id: {user_id}")
        doc_ref = self.client.collection("user_profiles").document(user_id)
        try:
            doc = await doc_ref.get()
            if doc.exists:
                logger.debug(f"User profile found for {user_id}")
                return UserProfile(**doc.to_dict())
            else:
                logger.debug(f"No user profile found for {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}", exc_info=True)
            raise

    async def save_user_profile(self, profile: UserProfile):
        """Saves a user profile to Firestore."""
        self._ensure_initialized()
        logger.debug(f"Saving user profile for user_id: {profile.user_id}")
        doc_ref = self.client.collection("user_profiles").document(profile.user_id)
        try:
            await doc_ref.set(profile.dict(), merge=True)
            logger.info(f"User profile for {profile.user_id} saved successfully.")
        except Exception as e:
            logger.error(f"Error saving user profile for {profile.user_id}: {e}", exc_info=True)
            raise

    async def get_chat_history(self, session_id: str) -> List[Content]:
        """Retrieves chat history for a session from Firestore."""
        self._ensure_initialized()
        logger.debug(f"Getting chat history for session_id: {session_id}")
        doc_ref = self.client.collection("chat_sessions").document(session_id)
        try:
            doc = await doc_ref.get()
            if doc.exists:
                history_data = doc.to_dict().get("history", [])
                logger.debug(f"Found {len(history_data)} messages for session {session_id}")
                return [Content.from_dict(item) for item in history_data]
            else:
                logger.debug(f"No history found for session {session_id}")
                return []
        except Exception as e:
            logger.error(f"Error getting chat history for {session_id}: {e}", exc_info=True)
            return []

    async def save_chat_history(self, session_id: str, history: List[Content]):
        """Saves chat history for a session to Firestore."""
        self._ensure_initialized()
        logger.debug(f"Saving {len(history)} chat messages for session: {session_id}")
        doc_ref = self.client.collection("chat_sessions").document(session_id)
        try:
            history_data = [item.to_dict() for item in history]
            await doc_ref.set({"history": history_data})
            logger.info(f"Chat history for session {session_id} saved successfully.")
        except Exception as e:
            logger.error(f"Error saving chat history for {session_id}: {e}", exc_info=True)
            raise

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
    async def save_receipt(self, user_id: str, receipt_data: ReceiptAnalysis) -> str:
        """Save analyzed receipt to database"""
        self._ensure_initialized()

        try:
            receipt_id = receipt_data.receipt_id

            # Save to receipts collection
            doc_ref = self.client.collection("receipts").document(receipt_id)
            receipt_dict = receipt_data.dict()
            receipt_dict.update(
                {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
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
                .where("user_id", "==", user_id)
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

    # Transaction RAG Operations
    async def save_transaction_with_rag_indexing(self, transaction_data: Dict[str, Any]) -> str:
        """
        Save a transaction to Firestore and automatically index it for RAG
        
        Args:
            transaction_data: Transaction data to save
            
        Returns:
            str: Transaction ID
        """
        self._ensure_initialized()
        
        try:
            # Generate transaction ID if not provided
            transaction_id = transaction_data.get('receipt_id', str(uuid.uuid4()))
            transaction_data['receipt_id'] = transaction_id
            
            # Add timestamps
            transaction_data.update({
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
            # Save to Firestore
            doc_ref = self.client.collection("transactions").document(transaction_id)
            await doc_ref.set(transaction_data)
            
            logger.info(f"Transaction saved: {transaction_id}")
            
            # Auto-index for RAG (async, don't wait)
            asyncio.create_task(self._auto_index_transaction(transaction_data))
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
            raise
    
    async def update_transaction_with_rag_indexing(self, transaction_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a transaction and re-index it for RAG
        
        Args:
            transaction_id: Transaction ID to update
            update_data: Data to update
            
        Returns:
            bool: Success status
        """
        self._ensure_initialized()
        
        try:
            # Add update timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Update in Firestore
            doc_ref = self.client.collection("transactions").document(transaction_id)
            await doc_ref.update(update_data)
            
            # Get updated document for re-indexing
            updated_doc = await doc_ref.get()
            if updated_doc.exists:
                transaction_data = updated_doc.to_dict()
                
                # Re-index for RAG (async, don't wait)
                asyncio.create_task(self._auto_index_transaction(transaction_data))
                
                logger.info(f"Transaction updated and re-indexed: {transaction_id}")
                return True
            else:
                logger.warning(f"Transaction not found for update: {transaction_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update transaction {transaction_id}: {e}")
            raise
    
    async def _auto_index_transaction(self, transaction_data: Dict[str, Any]):
        """
        Automatically index a transaction for RAG (background task)
        
        Args:
            transaction_data: Transaction data to index
        """
        try:
            # Import here to avoid circular imports
            from agents.transaction_rag_agent.agent import get_transaction_rag_agent
            
            # Get RAG agent and index the transaction
            rag_agent = await get_transaction_rag_agent()
            success = await rag_agent.index_transaction(transaction_data)
            
            if success:
                logger.info(f"Auto-indexed transaction: {transaction_data.get('receipt_id')}")
            else:
                logger.warning(f"Failed to auto-index transaction: {transaction_data.get('receipt_id')}")
                
        except Exception as e:
            logger.error(f"Auto-indexing failed for transaction {transaction_data.get('receipt_id')}: {e}")
            # Don't raise - this is a background task and shouldn't affect the main operation
    
    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single transaction by ID
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Optional[Dict]: Transaction data or None if not found
        """
        self._ensure_initialized()
        
        try:
            doc_ref = self.client.collection("transactions").document(transaction_id)
            doc = await doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get transaction {transaction_id}: {e}")
            raise
    
    async def get_transactions_for_user(
        self, 
        user_id: str, 
        limit: int = 100,
        start_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific user
        
        Args:
            user_id: User ID
            limit: Maximum number of transactions to return
            start_after: Transaction ID to start after (for pagination)
            
        Returns:
            List[Dict]: List of transactions
        """
        self._ensure_initialized()
        
        try:
            query = self.client.collection("transactions").where("user_id", "==", user_id).limit(limit)
            
            if start_after:
                # Get the document to start after
                start_doc = await self.client.collection("transactions").document(start_after).get()
                if start_doc.exists:
                    query = query.start_after(start_doc)
            
            docs = query.stream()
            transactions = []
            
            async for doc in docs:
                transaction_data = doc.to_dict()
                transaction_data['id'] = doc.id
                transactions.append(transaction_data)
            
            logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transactions for user {user_id}: {e}")
            raise

    async def close(self):
        """Close Firestore connection"""
        if self.client:
            self.client.close()
            self._initialized = False
            logger.info("Firestore service closed")


# Global service instance
firestore_service = FirestoreService()
