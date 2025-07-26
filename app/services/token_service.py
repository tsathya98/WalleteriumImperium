"""
Enhanced Token service for receipt processing
Manages token-based processing workflow with hybrid agentic agent
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger, log_async_performance
from app.models import (
    ProcessingStatus,
    ProcessingStage,
    ProcessingProgress,
    ReceiptAnalysis,
    TokenData,
    ErrorDetail,
)

settings = get_settings()
logger = get_logger(__name__)


class TokenService:
    """Enhanced Token-based processing service using hybrid agentic workflow"""

    def __init__(
        self,
        firestore_service = None,
    ):
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
        self._firestore_service = firestore_service

    async def initialize(self):
        """Initialize token service"""
        try:
            # Validate dependencies
            if not self._firestore_service:
                raise RuntimeError("FirestoreService dependency not provided")

            # Start background cleanup task
            asyncio.create_task(self._background_cleanup_task())
            self._initialized = True

            logger.info("✅ Enhanced token service initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize token service: {e}")
            raise

    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Token service not initialized")

    @log_async_performance(logger)
    async def create_processing_token(
        self, user_id: str, media_bytes: bytes, media_type: str
    ) -> str:
        """Create a new processing token and start background processing with raw bytes"""
        self._ensure_initialized()

        try:
            # Create token in database using injected service
            token = await self._firestore_service.create_token(user_id)

            # Start background processing with raw bytes
            processing_task = asyncio.create_task(
                self._process_receipt_background(
                    token, user_id, media_bytes, media_type
                )
            )

            # Track the task
            self._processing_tasks[token] = processing_task

            logger.info(
                "Processing token created with raw bytes",
                extra={
                    "token": token, 
                    "user_id": user_id,
                    "media_size_kb": len(media_bytes) / 1024,
                    "media_type": media_type
                },
            )

            return token

        except Exception as e:
            logger.error(
                f"Failed to create processing token: {e}", extra={"user_id": user_id}
            )
            raise

    async def get_token_status(self, token: str) -> Optional[TokenData]:
        """Get current status of processing token"""
        self._ensure_initialized()

        try:
            # Get token from database using injected service
            token_data = await self._firestore_service.get_token(token)

            if not token_data:
                return None

            # Check if token is expired (handle timezone-aware/naive comparison)
            now_utc = datetime.utcnow()
            expires_at = token_data.expires_at

            # Convert timezone-aware to naive for comparison if needed
            if expires_at.tzinfo is not None:
                expires_at = expires_at.replace(tzinfo=None)

            if now_utc > expires_at:
                logger.warning(f"Token expired: {token}")
                return None

            return token_data

        except Exception as e:
            logger.error(f"Failed to get token status: {e}", extra={"token": token})
            raise

    @log_async_performance(logger)
    async def _process_receipt_background(
        self, token: str, user_id: str, media_bytes: bytes, media_type: str
    ):
        """
        Background receipt processing with raw bytes
        Supports both image and video analysis
        """
        try:
            logger.info(
                "Starting background receipt processing (MVP)",
                extra={"token": token, "user_id": user_id},
            )

            # Stage 1: Analysis (MVP)
            await self._update_progress(
                token, ProcessingStage.ANALYSIS, 50.0, "Analyzing receipt data..."
            )

            # Process with Enhanced Receipt Scanner Agent
            from agents.receipt_scanner.agent import get_enhanced_receipt_scanner_agent
            
            enhanced_agent = get_enhanced_receipt_scanner_agent()
            ai_result = await enhanced_agent.analyze_receipt_media(
                media_bytes, media_type, user_id
            )
            
            # The enhanced agent already returns a ReceiptAnalysis object in ai_result["data"]
            if ai_result["status"] == "success":
                processing_result = ai_result["data"]
                # Convert dict back to ReceiptAnalysis object if needed
                if isinstance(processing_result, dict):
                    processing_result = ReceiptAnalysis(**processing_result)
            else:
                raise ValueError(f"Enhanced agent failed: {ai_result.get('error', 'Unknown error')}")
                
            # Stage 2: Completion
            await self._update_progress(
                token,
                ProcessingStage.COMPLETED,
                100.0,
                "Processing completed successfully!",
            )

            # Update token with final result using injected service
            await self._firestore_service.update_token_status(
                token=token, status=ProcessingStatus.COMPLETED, result=processing_result
            )

            # Save receipt to database using injected service
            await self._firestore_service.save_receipt(processing_result)

            logger.info(
                "Enhanced background receipt processing completed",
                extra={
                    "token": token,
                    "receipt_id": processing_result.receipt_id,
                    "place": processing_result.place,
                    "amount": processing_result.amount,
                },
            )

        except Exception as e:
            logger.error(
                "Background processing failed",
                extra={"token": token, "user_id": user_id, "error": str(e)},
            )

            # Update token with error using injected service
            error_detail = ErrorDetail(
                code="PROCESSING_FAILED",
                message=str(e),
                details={"timestamp": datetime.utcnow().isoformat()},
            )

            await self._firestore_service.update_token_status(
                token=token, status=ProcessingStatus.FAILED, error=error_detail.dict()
            )

        finally:
            # Clean up task tracking
            self._processing_tasks.pop(token, None)

    async def _update_progress(
        self, token: str, stage: ProcessingStage, percentage: float, message: str
    ):
        """Update processing progress"""
        try:
            # Calculate estimated remaining time (simplified for MVP)
            if percentage >= 100:
                remaining_seconds = 0
            elif percentage >= 50:
                remaining_seconds = 2  # Almost done
            else:
                remaining_seconds = 5  # Getting started

            progress = ProcessingProgress(
                stage=stage,
                percentage=percentage,
                message=message,
                estimated_remaining=remaining_seconds,
            )

            # Use injected service
            await self._firestore_service.update_token_status(
                token=token,
                status=ProcessingStatus.PROCESSING,
                progress=progress.dict(),
            )

            logger.debug(
                f"Progress updated (MVP): {token}",
                extra={"token": token, "stage": stage.value, "percentage": percentage},
            )

        except Exception as e:
            logger.error(
                f"Failed to update progress: {e}",
                extra={"token": token, "stage": stage.value},
            )

    async def retry_failed_processing(self, token: str) -> bool:
        """Retry failed processing"""
        self._ensure_initialized()

        try:
            # Get token data using injected service
            token_data = await self._firestore_service.get_token(token)
            if not token_data:
                return False

            # Check if eligible for retry
            if token_data.retry_count >= settings.MAX_RETRIES:
                logger.warning(f"Max retries exceeded for token: {token}")
                return False

            if token_data.status != ProcessingStatus.FAILED:
                logger.warning(f"Token not in failed state: {token}")
                return False

            # Increment retry count using injected service
            retry_count = await self._firestore_service.increment_retry_count(token)

            logger.info(
                f"Retrying processing (attempt {retry_count}) - MVP",
                extra={"token": token, "retry_count": retry_count},
            )

            # Reset token status using injected service
            await self._firestore_service.update_token_status(
                token=token,
                status=ProcessingStatus.PROCESSING,
                progress=ProcessingProgress(
                    stage=ProcessingStage.ANALYSIS,
                    percentage=0.0,
                    message="Retrying processing...",
                    estimated_remaining=10,
                ).dict(),
                error=None,
            )

            # Note: In MVP, we don't store original image data for retry
            logger.info("MVP: Retry initiated but original image data not stored")

            return True

        except Exception as e:
            logger.error(f"Failed to retry processing: {e}", extra={"token": token})
            return False

    async def cancel_processing(self, token: str) -> bool:
        """Cancel ongoing processing"""
        self._ensure_initialized()

        try:
            # Cancel background task if running
            if token in self._processing_tasks:
                task = self._processing_tasks[token]
                if not task.done():
                    task.cancel()
                self._processing_tasks.pop(token, None)

            # Update token status using injected service
            await self._firestore_service.update_token_status(
                token=token,
                status=ProcessingStatus.FAILED,
                error=ErrorDetail(
                    code="PROCESSING_CANCELLED",
                    message="Processing was cancelled by user",
                ).dict(),
            )

            logger.info(f"Processing cancelled: {token}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel processing: {e}", extra={"token": token})
            return False

    async def _background_cleanup_task(self):
        """Background task for cleanup operations"""
        while True:
            try:
                # Sleep for 5 minutes
                await asyncio.sleep(300)

                # Clean up expired tokens using injected service
                deleted_count = await self._firestore_service.cleanup_expired_tokens()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired tokens")

                # Clean up completed tasks
                completed_tokens = [
                    token
                    for token, task in self._processing_tasks.items()
                    if task.done()
                ]

                for token in completed_tokens:
                    self._processing_tasks.pop(token, None)

                if completed_tokens:
                    logger.info(f"Cleaned up {len(completed_tokens)} completed tasks")

            except Exception as e:
                logger.error(f"Background cleanup error: {e}")

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            active_tasks = len(
                [t for t in self._processing_tasks.values() if not t.done()]
            )
            completed_tasks = len(
                [t for t in self._processing_tasks.values() if t.done()]
            )

            return {
                "active_processing_tokens": active_tasks,
                "completed_tasks": completed_tasks,
                "total_tracked_tasks": len(self._processing_tasks),
                "mode": "mvp",
            }

        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for token service"""
        try:
            if not self._initialized:
                return {"status": "unhealthy", "error": "Not initialized"}

            stats = await self.get_processing_stats()

            return {
                "status": "healthy",
                "mode": "mvp",
                "processing_stats": stats,
                "max_retries": settings.MAX_RETRIES,
                "token_expiry_minutes": settings.TOKEN_EXPIRY_MINUTES,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def shutdown(self):
        """Shutdown token service gracefully"""
        logger.info("Shutting down token service...")

        # Cancel all running tasks
        for token, task in self._processing_tasks.items():
            if not task.done():
                logger.info(f"Cancelling processing task: {token}")
                task.cancel()

        # Wait for tasks to complete
        if self._processing_tasks:
            await asyncio.gather(
                *self._processing_tasks.values(), return_exceptions=True
            )

        self._processing_tasks.clear()
        self._initialized = False

        logger.info("Token service shutdown complete")


# Global service instance (deprecated - use dependency injection)
# This is kept for backward compatibility but should not be used
token_service = TokenService()
