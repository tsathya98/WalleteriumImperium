"""
Receipt processing API endpoints for Project Raseed
Handles receipt upload, processing, and status tracking
"""

import json
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, Request, Depends, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger, log_async_performance
from app.models import (
    ReceiptUploadResponse,
    ReceiptStatusResponse,
    ProcessingStatus,
    ProcessingProgress,
)

# Import service classes only (not instances)

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Extract user information from Firebase Auth token
    In production, this would verify the Firebase JWT token
    For development, we'll use a simplified approach
    """
    if settings.is_development and not credentials:
        # Allow requests without auth in development
        return {"uid": "dev_user", "email": "dev@example.com"}

    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    # In production, verify Firebase JWT token here
    # For now, we'll extract user info from token (placeholder)
    # token = credentials.credentials

    # TODO: Implement Firebase JWT verification
    # For demo purposes, return mock user
    return {"uid": "user_123", "email": "user@example.com"}


@router.post("/upload", response_model=ReceiptUploadResponse, status_code=202)
@log_async_performance(logger)
async def upload_receipt(
    file: UploadFile = File(..., description="Receipt image or video file"),
    user_id: str = Form(..., description="User ID from Firebase Auth"),
    metadata: Optional[str] = Form(
        default="{}", description="Optional metadata as JSON string"
    ),
    http_request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Upload receipt image or video file for AI analysis

    This endpoint accepts multipart file uploads and returns a processing token.
    The client should poll the status endpoint to get results.

    Args:
        file: UploadFile containing the receipt image or video
        user_id: User ID from Firebase Auth
        metadata: Optional metadata as JSON string
        http_request: FastAPI request object for accessing app state
        current_user: Authenticated user information

    Returns:
        ReceiptUploadResponse with processing token and estimated time

    Raises:
        HTTPException: For validation errors, file size limits, or processing failures
    """
    try:
        # Parse metadata from JSON string
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON format")

        # Determine media type from file extension
        file_extension = Path(file.filename or "").suffix.lower()
        if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            media_type = "image"
        elif file_extension in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
            media_type = "video"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: images (.jpg, .png) and videos (.mp4, .mov, .avi)",
            )

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / 1024 / 1024

        logger.info(
            "Receipt upload started",
            extra={
                "user_id": current_user["uid"],
                "filename": file.filename,
                "media_type": media_type,
                "file_size_mb": file_size_mb,
                "metadata": metadata_dict,
            },
        )

        # Validate file size based on type
        max_size_mb = (
            settings.MAX_IMAGE_SIZE_MB if media_type == "image" else 100
        )  # 100MB for videos

        if file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"{media_type.title()} too large ({file_size_mb:.2f}MB). Maximum size: {max_size_mb}MB",
            )

        # Create processing token and start background processing with raw bytes
        # No base64 conversion needed - enhanced agent handles raw bytes directly
        processing_token = (
            await http_request.app.state.token_service.create_processing_token(
                user_id=current_user["uid"],
                media_bytes=file_content,  # Pass raw bytes directly
                media_type=media_type,
            )
        )

        # Estimate processing time based on media type and size
        if media_type == "image":
            estimated_time = min(
                30, max(10, int(file_size_mb * 2))
            )  # 10-30 seconds for images
        else:
            estimated_time = min(
                60, max(20, int(file_size_mb * 1.5))
            )  # 20-60 seconds for videos

        response = ReceiptUploadResponse(
            processing_token=processing_token,
            estimated_time=estimated_time,
            status=ProcessingStatus.UPLOADED,
            message="Receipt uploaded successfully, processing started",
        )

        logger.info(
            "Receipt upload completed",
            extra={
                "user_id": current_user["uid"],
                "processing_token": processing_token,
                "estimated_time": estimated_time,
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Receipt upload failed",
            extra={"user_id": current_user.get("uid", "unknown"), "error": str(e)},
        )

        raise HTTPException(status_code=500, detail="Failed to process receipt upload")


@router.get("/status/{token}", response_model=ReceiptStatusResponse)
async def get_processing_status(
    token: str, http_request: Request, current_user: dict = Depends(get_current_user)
):
    """
    Get processing status by token

    This endpoint allows the frontend to poll for processing updates.
    It returns the current status, progress, and results when available.
    """
    try:
        logger.debug(
            "Status check requested",
            extra={"token": token, "user_id": current_user["uid"]},
        )

        # Get token data
        token_data = await http_request.app.state.token_service.get_token_status(token)

        if not token_data:
            raise HTTPException(
                status_code=404, detail="Processing token not found or expired"
            )

        # Verify token belongs to user (security check)
        if token_data.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=403, detail="Access denied: Token belongs to different user"
            )

        # Build response
        response = ReceiptStatusResponse(
            token=token,
            status=token_data.status,
            progress=token_data.progress,
            result=token_data.result,
            error=token_data.error,
            created_at=token_data.created_at,
            updated_at=token_data.updated_at,
            expires_at=token_data.expires_at,
        )

        logger.debug(
            "Status check completed",
            extra={
                "token": token,
                "status": token_data.status.value,
                "progress": token_data.progress.percentage,
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Status check failed",
            extra={
                "token": token,
                "user_id": current_user.get("uid", "unknown"),
                "error": str(e),
            },
        )

        raise HTTPException(status_code=500, detail="Failed to check processing status")


@router.post("/retry/{token}")
async def retry_processing(
    token: str, http_request: Request, current_user: dict = Depends(get_current_user)
):
    """
    Retry failed processing

    Allows users to retry processing if it failed due to temporary issues.
    """
    try:
        logger.info(
            "Processing retry requested",
            extra={"token": token, "user_id": current_user["uid"]},
        )

        # Get token data to verify ownership
        token_data = await http_request.app.state.token_service.get_token_status(token)

        if not token_data:
            raise HTTPException(
                status_code=404, detail="Processing token not found or expired"
            )

        # Verify token belongs to user
        if token_data.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=403, detail="Access denied: Token belongs to different user"
            )

        # Attempt retry
        success = await http_request.app.state.token_service.retry_failed_processing(
            token
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Retry not possible (max retries reached or invalid status)",
            )

        logger.info(
            "Processing retry initiated",
            extra={"token": token, "user_id": current_user["uid"]},
        )

        return {
            "message": "Processing retry initiated",
            "token": token,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Processing retry failed",
            extra={
                "token": token,
                "user_id": current_user.get("uid", "unknown"),
                "error": str(e),
            },
        )

        raise HTTPException(status_code=500, detail="Failed to retry processing")


@router.delete("/cancel/{token}")
async def cancel_processing(
    token: str, http_request: Request, current_user: dict = Depends(get_current_user)
):
    """
    Cancel ongoing processing

    Allows users to cancel processing that is taking too long.
    """
    try:
        logger.info(
            "Processing cancellation requested",
            extra={"token": token, "user_id": current_user["uid"]},
        )

        # Get token data to verify ownership
        token_data = await http_request.app.state.token_service.get_token_status(token)

        if not token_data:
            raise HTTPException(
                status_code=404, detail="Processing token not found or expired"
            )

        # Verify token belongs to user
        if token_data.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=403, detail="Access denied: Token belongs to different user"
            )

        # Attempt cancellation
        success = await http_request.app.state.token_service.cancel_processing(token)

        if not success:
            raise HTTPException(status_code=400, detail="Cancellation failed")

        logger.info(
            "Processing cancelled",
            extra={"token": token, "user_id": current_user["uid"]},
        )

        return {
            "message": "Processing cancelled successfully",
            "token": token,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Processing cancellation failed",
            extra={
                "token": token,
                "user_id": current_user.get("uid", "unknown"),
                "error": str(e),
            },
        )

        raise HTTPException(status_code=500, detail="Failed to cancel processing")


@router.get("/history")
async def get_user_receipts(
    http_request: Request,
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """
    Get user's receipt history

    Returns paginated list of processed receipts for the user.
    """
    try:
        logger.info(
            "Receipt history requested",
            extra={"user_id": current_user["uid"], "limit": limit, "offset": offset},
        )

        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 100"
            )

        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")

        # Get receipts from database
        receipts = await http_request.app.state.firestore.get_user_receipts(
            user_id=current_user["uid"], limit=limit, offset=offset
        )

        logger.info(
            "Receipt history retrieved",
            extra={
                "user_id": current_user["uid"],
                "count": len(receipts),
                "limit": limit,
                "offset": offset,
            },
        )

        return {
            "receipts": [receipt.dict() for receipt in receipts],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(receipts),
                "has_more": len(receipts) == limit,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Receipt history retrieval failed",
            extra={"user_id": current_user.get("uid", "unknown"), "error": str(e)},
        )

        raise HTTPException(
            status_code=500, detail="Failed to retrieve receipt history"
        )


@router.get("/{receipt_id}")
async def get_receipt_details(
    receipt_id: str,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed receipt information by ID

    Returns complete receipt data including AI insights.
    """
    try:
        logger.info(
            "Receipt details requested",
            extra={"receipt_id": receipt_id, "user_id": current_user["uid"]},
        )

        # Get receipt from database
        receipt = await http_request.app.state.firestore.get_receipt(receipt_id)

        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        # Note: In a real implementation, we'd need to verify the receipt belongs to the user
        # This would require storing user_id in the receipt document

        logger.info(
            "Receipt details retrieved",
            extra={
                "receipt_id": receipt_id,
                "user_id": current_user["uid"],
                "store_name": receipt.store_info.name,
            },
        )

        return {"receipt": receipt.dict(), "timestamp": datetime.utcnow().isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Receipt details retrieval failed",
            extra={
                "receipt_id": receipt_id,
                "user_id": current_user.get("uid", "unknown"),
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500, detail="Failed to retrieve receipt details"
        )
