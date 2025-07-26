"""
Receipt processing API endpoints for Project Raseed
Handles receipt upload, processing, and status tracking
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import base64
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger, log_async_performance
from app.models import (
    ReceiptUploadRequest, ReceiptUploadResponse, 
    ReceiptStatusRequest, ReceiptStatusResponse,
    ProcessingStatus, ProcessingProgress, ProcessingStage,
    ValidationError, APIError
)
from app.services.token_service import token_service
from app.services.firestore_service import firestore_service

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
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
    token = credentials.credentials
    
    # TODO: Implement Firebase JWT verification
    # For demo purposes, return mock user
    return {"uid": "user_123", "email": "user@example.com"}


@router.post("/upload", response_model=ReceiptUploadResponse)
@log_async_performance(logger)
async def upload_receipt(
    request: ReceiptUploadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload receipt image for processing
    
    This endpoint:
    1. Validates the uploaded image
    2. Creates a processing token
    3. Starts background AI processing
    4. Returns immediately with token for status polling
    
    The actual processing happens asynchronously to avoid API gateway timeouts.
    """
    try:
        logger.info("Receipt upload started", extra={
            "user_id": current_user["uid"],
            "image_size_kb": len(request.image_base64) * 3 / 4 / 1024,
            "metadata": request.metadata
        })
        
        # Validate image size
        image_size_mb = len(request.image_base64) * 3 / 4 / 1024 / 1024
        if image_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size: {settings.MAX_IMAGE_SIZE_MB}MB"
            )
        
        # Validate base64 format
        try:
            base64.b64decode(request.image_base64, validate=True)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid base64 image format"
            )
        
        # Create processing token and start background processing
        processing_token = await token_service.create_processing_token(
            user_id=current_user["uid"],
            image_base64=request.image_base64
        )
        
        # Calculate estimated processing time
        estimated_time = min(settings.PROCESSING_TIMEOUT, 30)  # Cap at 30 seconds for UI
        
        response = ReceiptUploadResponse(
            processing_token=processing_token,
            estimated_time=estimated_time,
            status=ProcessingStatus.UPLOADED,
            message="Receipt uploaded successfully, processing started"
        )
        
        logger.info("Receipt upload completed", extra={
            "user_id": current_user["uid"],
            "processing_token": processing_token,
            "estimated_time": estimated_time
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Receipt upload failed", extra={
            "user_id": current_user.get("uid", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to process receipt upload"
        )


@router.get("/status/{token}", response_model=ReceiptStatusResponse)
async def get_processing_status(
    token: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get processing status by token
    
    This endpoint allows the frontend to poll for processing updates.
    It returns the current status, progress, and results when available.
    """
    try:
        logger.debug("Status check requested", extra={
            "token": token,
            "user_id": current_user["uid"]
        })
        
        # Get token data
        token_data = await token_service.get_token_status(token)
        
        if not token_data:
            raise HTTPException(
                status_code=404,
                detail="Processing token not found or expired"
            )
        
        # Verify token belongs to user (security check)
        if token_data.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Token belongs to different user"
            )
        
        # Build response
        response = ReceiptStatusResponse(
            token=token,
            status=token_data.status,
            progress=ProcessingProgress(**token_data.progress),
            result=token_data.result,
            error=token_data.error,
            created_at=token_data.created_at,
            updated_at=token_data.updated_at,
            expires_at=token_data.expires_at
        )
        
        logger.debug("Status check completed", extra={
            "token": token,
            "status": token_data.status.value,
            "progress": token_data.progress.get("percentage", 0)
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Status check failed", extra={
            "token": token,
            "user_id": current_user.get("uid", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to check processing status"
        )


@router.post("/retry/{token}")
async def retry_processing(
    token: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retry failed processing
    
    Allows users to retry processing if it failed due to temporary issues.
    """
    try:
        logger.info("Processing retry requested", extra={
            "token": token,
            "user_id": current_user["uid"]
        })
        
        # Get token data to verify ownership
        token_data = await token_service.get_token_status(token)
        
        if not token_data:
            raise HTTPException(
                status_code=404,
                detail="Processing token not found or expired"
            )
        
        # Verify token belongs to user
        if token_data.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Token belongs to different user"
            )
        
        # Attempt retry
        success = await token_service.retry_failed_processing(token)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Retry not possible (max retries reached or invalid status)"
            )
        
        logger.info("Processing retry initiated", extra={
            "token": token,
            "user_id": current_user["uid"]
        })
        
        return {
            "message": "Processing retry initiated",
            "token": token,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Processing retry failed", extra={
            "token": token,
            "user_id": current_user.get("uid", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retry processing"
        )


@router.delete("/cancel/{token}")
async def cancel_processing(
    token: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel ongoing processing
    
    Allows users to cancel processing that is taking too long.
    """
    try:
        logger.info("Processing cancellation requested", extra={
            "token": token,
            "user_id": current_user["uid"]
        })
        
        # Get token data to verify ownership
        token_data = await token_service.get_token_status(token)
        
        if not token_data:
            raise HTTPException(
                status_code=404,
                detail="Processing token not found or expired"
            )
        
        # Verify token belongs to user
        if token_data.user_id != current_user["uid"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Token belongs to different user"
            )
        
        # Attempt cancellation
        success = await token_service.cancel_processing(token)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Cancellation failed"
            )
        
        logger.info("Processing cancelled", extra={
            "token": token,
            "user_id": current_user["uid"]
        })
        
        return {
            "message": "Processing cancelled successfully",
            "token": token,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Processing cancellation failed", extra={
            "token": token,
            "user_id": current_user.get("uid", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel processing"
        )


@router.get("/history")
async def get_user_receipts(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    Get user's receipt history
    
    Returns paginated list of processed receipts for the user.
    """
    try:
        logger.info("Receipt history requested", extra={
            "user_id": current_user["uid"],
            "limit": limit,
            "offset": offset
        })
        
        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Offset must be non-negative"
            )
        
        # Get receipts from database
        receipts = await firestore_service.get_user_receipts(
            user_id=current_user["uid"],
            limit=limit,
            offset=offset
        )
        
        logger.info("Receipt history retrieved", extra={
            "user_id": current_user["uid"],
            "count": len(receipts),
            "limit": limit,
            "offset": offset
        })
        
        return {
            "receipts": [receipt.dict() for receipt in receipts],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(receipts),
                "has_more": len(receipts) == limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Receipt history retrieval failed", extra={
            "user_id": current_user.get("uid", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve receipt history"
        )


@router.get("/{receipt_id}")
async def get_receipt_details(
    receipt_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed receipt information by ID
    
    Returns complete receipt data including AI insights.
    """
    try:
        logger.info("Receipt details requested", extra={
            "receipt_id": receipt_id,
            "user_id": current_user["uid"]
        })
        
        # Get receipt from database
        receipt = await firestore_service.get_receipt(receipt_id)
        
        if not receipt:
            raise HTTPException(
                status_code=404,
                detail="Receipt not found"
            )
        
        # Note: In a real implementation, we'd need to verify the receipt belongs to the user
        # This would require storing user_id in the receipt document
        
        logger.info("Receipt details retrieved", extra={
            "receipt_id": receipt_id,
            "user_id": current_user["uid"],
            "store_name": receipt.store_info.name
        })
        
        return {
            "receipt": receipt.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Receipt details retrieval failed", extra={
            "receipt_id": receipt_id,
            "user_id": current_user.get("uid", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve receipt details"
        )