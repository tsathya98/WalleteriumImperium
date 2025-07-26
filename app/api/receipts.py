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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    DEPRECATED: This function is no longer used for hackathon simplicity.
    A simple user_id string is passed from the frontend instead.
    """
    # This entire function is bypassed for the hackathon.
    # In a production app, this is where you would validate a real JWT token.
    return {"uid": "mock_user_for_testing_only"}


@router.post("/upload", response_model=ReceiptUploadResponse, status_code=202)
@log_async_performance(logger)
async def upload_receipt(
    file: UploadFile = File(..., description="Receipt image or video file"),
    user_id: str = Form(..., description="User ID from the frontend"),
    metadata: Optional[str] = Form(
        default="{}", description="Optional metadata as JSON string"
    ),
    http_request: Request = None,
):
    """
    Upload receipt image/video. This is the primary endpoint.
    It takes a user_id directly from the form for simplicity.
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="A non-empty user_id is required.")
        
        user_id = user_id.strip()

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

        # Validate user_id
        if not user_id or len(user_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        user_id = user_id.strip()

        logger.info(
            "Receipt upload started",
            extra={
                "user_id": user_id,
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
        processing_token = await http_request.app.state.token_service.create_processing_token(
            user_id=user_id,
            media_bytes=file_content,  # Pass raw bytes directly
            media_type=media_type,
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
            estimated_time=15, # Simplified for hackathon
            status=ProcessingStatus.UPLOADED,
            message="Receipt uploaded successfully, processing started",
        )

        logger.info(
            "Receipt upload completed",
            extra={
                "user_id": user_id,
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
            extra={"user_id": user_id if "user_id" in locals() else "unknown", "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to process receipt upload")


@router.get("/status/{token}", response_model=ReceiptStatusResponse)
async def get_processing_status(token: str, http_request: Request):
    """
    Get processing status by token. No authentication required.
    """
    try:
        logger.debug("Status check requested", extra={"token": token})

        token_data = await http_request.app.state.token_service.get_token_status(token)

        if not token_data:
            raise HTTPException(status_code=404, detail="Token not found or expired")

        # Public endpoint - no user verification needed for hackathon
        
        return ReceiptStatusResponse(**token_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed for token {token}", exc_info=True)
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
        token_data = await http_request.app.state.token_service.get_token_status(
            token
        )

        if not token_data:
            raise HTTPException(
                status_code=404, detail="Processing token not found or expired"
            )

        # Verify token belongs to user
        if token_data["user_id"] != current_user["uid"]:
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
        token_data = await http_request.app.state.token_service.get_token_status(
            token
        )

        if not token_data:
            raise HTTPException(
                status_code=404, detail="Processing token not found or expired"
            )

        # Verify token belongs to user
        if token_data["user_id"] != current_user["uid"]:
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


@router.get("/history/{user_id}")
async def get_user_receipts(
    user_id: str,
    http_request: Request,
    limit: int = 20,
    offset: int = 0,
):
    """
    Get a user's receipt history by their user_id.
    """
    try:
        logger.info(
            "Receipt history requested",
            extra={"user_id": user_id, "limit": limit, "offset": offset},
        )
        
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="A non-empty user_id is required.")

        receipts = await http_request.app.state.firestore.get_user_receipts(
            user_id=user_id.strip(), limit=limit, offset=offset
        )
        
        return {
            "receipts": [receipt.dict() for receipt in receipts],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(receipts),
                "has_more": len(receipts) == limit,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Receipt history retrieval failed for user {user_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve receipt history")


@router.get("/{receipt_id}")
async def get_receipt_details(receipt_id: str, http_request: Request):
    """
    Get detailed receipt information by its ID. Public access.
    """
    try:
        logger.info("Receipt details requested", extra={"receipt_id": receipt_id})

        receipt = await http_request.app.state.firestore.get_receipt(receipt_id)

        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        return {"receipt": receipt.dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Receipt details retrieval failed for {receipt_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve receipt details")
