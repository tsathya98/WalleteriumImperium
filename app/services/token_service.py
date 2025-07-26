"""
Enhanced Token service for receipt processing
Manages token-based processing workflow with hybrid agentic agent
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import ProcessingStatus, ReceiptAnalysis
from app.services.firestore_service import FirestoreService
from agents.receipt_scanner.agent import get_receipt_scanner_agent

logger = get_logger(__name__)
settings = get_settings()


class TokenService:
    """Enhanced token service for managing receipt processing tokens."""

    def __init__(self, firestore_service: FirestoreService):
        self._firestore_service = firestore_service
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
        logger.info("Initializing Enhanced Token Service...")

    async def initialize(self):
        """Initializes the service."""
        try:
            if not self._firestore_service:
                raise RuntimeError("FirestoreService dependency not provided")
            await self._firestore_service.initialize()
            self._initialized = True
            logger.info("✅ Enhanced token service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize token service: {e}", exc_info=True)
            raise

    def _ensure_initialized(self):
        if not self._initialized:
            raise RuntimeError("Token service not initialized")

    async def create_processing_token(
        self, user_id: str, media_bytes: bytes, media_type: str
    ) -> str:
        """Creates a token, saves it, and starts background processing."""
        self._ensure_initialized()
        try:
            token = await self._firestore_service.create_token(user_id)
            logger.info(f"Processing token created: {token} for user {user_id}")

            task = asyncio.create_task(
                self._process_receipt_async(token, user_id, media_bytes, media_type)
            )
            self._processing_tasks[token] = task
            task.add_done_callback(lambda t: self._processing_tasks.pop(token, None))

            return token
        except Exception as e:
            logger.error(f"❌ Failed to create processing token: {e}", exc_info=True)
            raise

    async def get_token_status(self, token: str) -> Optional[Dict[str, Any]]:
        """Gets the status of a processing token from Firestore."""
        self._ensure_initialized()
        try:
            token_data = await self._firestore_service.get_token(token)
            if not token_data:
                return None
            return token_data.dict()
        except Exception as e:
            logger.error(f"❌ Failed to get token status for {token}: {e}", exc_info=True)
            raise

    async def _process_receipt_async(
        self, token: str, user_id: str, media_bytes: bytes, media_type: str
    ):
        """Asynchronous receipt processing and Firestore saving."""
        logger.info(f"🚀 Starting async receipt processing for token: {token}")
        try:
            agent = get_receipt_scanner_agent()
            ai_result = agent.analyze_receipt(media_bytes, media_type, user_id)

            if ai_result["status"] == "success":
                receipt_analysis = ReceiptAnalysis(**ai_result["data"])
                
                await self._firestore_service.save_receipt(
                    user_id, receipt_analysis
                )
                logger.info(f"✅ Receipt saved to Firestore: {receipt_analysis.receipt_id}")

                await self._firestore_service.update_token_status(
                    token,
                    status=ProcessingStatus.COMPLETED,
                    result=receipt_analysis,
                    progress={"stage": "completed", "percentage": 100.0, "message": "Processing complete"},
                )
                logger.info(f"✅ Sync receipt processing completed for token: {token}")
            else:
                error_message = ai_result.get("error", "Unknown agent error")
                raise ValueError(f"Agent failed: {error_message}")

        except Exception as e:
            logger.error(f"❌ Async processing failed for token {token}: {e}", exc_info=True)
            await self._firestore_service.update_token_status(
                token,
                status=ProcessingStatus.FAILED,
                error={"code": "processing_error", "message": str(e)},
                progress={"stage": "failed", "percentage": 100.0, "message": "Processing failed"},
            )

    async def retry_failed_processing(self, token: str) -> bool:
        """Retries a failed processing task."""
        self._ensure_initialized()
        logger.info(f"🔄 Retrying processing for token: {token}")
        # Implementation would require re-fetching media bytes or storing them
        # For now, this is a placeholder for demonstrating the API endpoint.
        return True

    async def cancel_processing(self, token: str) -> bool:
        """Cancels an ongoing processing task."""
        self._ensure_initialized()
        if token in self._processing_tasks:
            self._processing_tasks[token].cancel()
            logger.info(f"Processing cancelled for token: {token}")
            await self._firestore_service.update_token_status(
                token,
                status=ProcessingStatus.FAILED,
                error={"code": "cancelled", "message": "Processing cancelled by user."},
            )
            return True
        return False

    async def shutdown(self):
        """Shuts down the token service gracefully."""
        logger.info("Shutting down token service...")
        for task in self._processing_tasks.values():
            task.cancel()
        await asyncio.gather(*self._processing_tasks.values(), return_exceptions=True)
        self._processing_tasks.clear()
        if self._firestore_service:
            await self._firestore_service.close()
        self._initialized = False
        logger.info("Token service shutdown complete.")
