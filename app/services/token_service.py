"""
Token service for Project Raseed
Manages token-based processing workflow and background tasks
MVP: Simplified processing with realistic receipt stubs
"""

import asyncio
from typing import List, Optional, Dict, Any, TYPE_CHECKING
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

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from app.services.firestore_service import FirestoreService
    from app.services.vertex_ai_service import VertexAIReceiptService

settings = get_settings()
logger = get_logger(__name__)


class TokenService:
    """Token-based processing service for MVP"""

    def __init__(
        self,
        firestore_service: "FirestoreService" = None,
        vertex_ai_service: "VertexAIReceiptService" = None,
    ):
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
        self._firestore_service = firestore_service
        self._vertex_ai_service = vertex_ai_service

    async def initialize(self):
        """Initialize token service"""
        try:
            # Validate dependencies
            if not self._firestore_service:
                raise RuntimeError("FirestoreService dependency not provided")
            if not self._vertex_ai_service:
                raise RuntimeError("VertexAI service dependency not provided")

            # Start background cleanup task
            asyncio.create_task(self._background_cleanup_task())
            self._initialized = True

            logger.info("✅ Token service initialized successfully (MVP mode)")

        except Exception as e:
            logger.error(f"❌ Failed to initialize token service: {e}")
            raise

    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Token service not initialized")

    @log_async_performance(logger)
    async def create_processing_token(
        self, user_id: str, media_base64: str, media_type: str
    ) -> str:
        """Create a new processing token and start background processing"""
        self._ensure_initialized()

        try:
            # Create token in database using injected service
            token = await self._firestore_service.create_token(user_id)

            # Start background processing
            processing_task = asyncio.create_task(
                self._process_receipt_background(
                    token, user_id, media_base64, media_type
                )
            )

            # Track the task
            self._processing_tasks[token] = processing_task

            logger.info(
                "Processing token created (MVP)",
                extra={"token": token, "user_id": user_id},
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
        self, token: str, user_id: str, media_base64: str, media_type: str
    ):
        """
        Background receipt processing with progress updates
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

            # Process with Enhanced Vertex AI service using injected service
            if self._vertex_ai_service:
                ai_result = await self._vertex_ai_service.analyze_receipt_media(
                    media_base64, media_type, user_id
                )
                # Transform AI result to ReceiptAnalysis model
                processing_result = self._transform_ai_result_to_receipt_analysis(
                    ai_result, token
                )
            else:
                # Fallback to get_vertex_ai_service if not injected
                from app.services.vertex_ai_service import get_vertex_ai_service

                vertex_ai_service = get_vertex_ai_service()
                ai_result = await vertex_ai_service.analyze_receipt_media(
                    media_base64, media_type, user_id
                )
                processing_result = self._transform_ai_result_to_receipt_analysis(
                    ai_result, token
                )

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
                "Background receipt processing completed (MVP)",
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

    def _transform_ai_result_to_receipt_analysis(
        self, ai_result: Dict[str, Any], token: str
    ) -> ReceiptAnalysis:
        """
        Transform the enhanced AI analysis result to ReceiptAnalysis model

        Args:
            ai_result: Result from Vertex AI service
            token: Processing token for receipt_id

        Returns:
            ReceiptAnalysis object compatible with the app models
        """
        try:
            if ai_result["status"] != "success":
                raise ValueError(
                    f"AI analysis failed: {ai_result.get('error', 'Unknown error')}"
                )

            data = ai_result["data"]
            store_info = data.get("store_info", {})
            totals = data.get("totals", {})
            items = data.get("items", [])

            # Extract date and time
            transaction_date = store_info.get("date")
            transaction_time = store_info.get("time")

            # Combine date and time into ISO 8601 format
            if transaction_date and transaction_date not in ["Unknown", "Not provided"]:
                if transaction_time and transaction_time not in [
                    "Unknown",
                    "Not provided",
                ]:
                    time_str = f"{transaction_date}T{transaction_time}:00Z"
                else:
                    time_str = (
                        f"{transaction_date}T12:00:00Z"  # Default to noon if no time
                    )
            else:
                time_str = (
                    datetime.utcnow().isoformat() + "Z"
                )  # Use current time as fallback

            # Determine category based on items
            category = self._determine_category_from_items(items)

            # Check for warranty indicators (basic heuristic)
            warranty = any(
                "warranty" in item.get("name", "").lower()
                or item.get("category") == "electronics"
                for item in items
            )

            # Check for subscription indicators
            recurring = any(
                "subscription" in item.get("name", "").lower()
                or "monthly" in item.get("name", "").lower()
                for item in items
            )

            # Create ReceiptAnalysis object
            receipt_analysis = ReceiptAnalysis(
                place=store_info.get("name", "Unknown Store"),
                time=time_str,
                amount=float(totals.get("total", 0)),
                transactionType="debit",  # Default assumption for receipts
                category=category,
                description=self._generate_description(store_info, items),
                importance="medium",  # Default importance
                warranty=warranty,
                recurring=recurring,
                subscription=None,  # TODO: Could be enhanced with AI analysis
                warrantyDetails=None,  # TODO: Could be enhanced with AI analysis
                receipt_id=token,  # Use token as receipt ID
                processing_time=ai_result.get("processing_time"),
            )

            logger.info(
                "Successfully transformed AI result to ReceiptAnalysis",
                extra={
                    "receipt_id": token,
                    "store_name": receipt_analysis.place,
                    "amount": receipt_analysis.amount,
                    "items_count": len(items),
                },
            )

            return receipt_analysis

        except Exception as e:
            logger.error(
                "Failed to transform AI result",
                extra={
                    "token": token,
                    "error": str(e),
                    "ai_result_status": ai_result.get("status", "unknown"),
                },
            )
            raise ValueError(f"Failed to transform AI result: {str(e)}")

    def _determine_category_from_items(self, items: List[Dict[str, Any]]) -> str:
        """Determine overall category based on item categories"""
        if not items:
            return "other"

        category_counts = {}
        for item in items:
            category = item.get("category", "other")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Return the most common category, with some smart mapping
        most_common = max(category_counts, key=category_counts.get)

        # Map to common expense categories
        category_mapping = {
            "food": "Groceries",
            "beverage": "Dining",
            "household": "Household",
            "personal_care": "Personal Care",
            "electronics": "Electronics",
            "clothing": "Shopping",
            "pharmacy": "Healthcare",
            "other": "Other",
        }

        return category_mapping.get(most_common, "Other")

    def _generate_description(
        self, store_info: Dict[str, Any], items: List[Dict[str, Any]]
    ) -> str:
        """Generate a description based on store and items"""
        store_name = store_info.get("name", "Unknown Store")
        if store_name in ["Not provided", "Unknown"]:
            store_name = "Unknown Store"

        items_count = len(items)

        if items_count == 0:
            return f"Transaction at {store_name}"
        elif items_count == 1:
            item_name = items[0].get("name", "item")
            return f"{item_name} from {store_name}"
        else:
            return f"{items_count} items from {store_name}"

    async def shutdown(self):
        """Shutdown token service gracefully"""
        logger.info("Shutting down token service (MVP)...")

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
