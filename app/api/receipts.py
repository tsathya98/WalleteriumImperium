"""
Simple Receipt Upload API - Single endpoint that accepts files and returns analysis
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import json

from app.core.config import get_settings
from app.core.logging import get_logger
from agents.receipt_scanner.agent import get_receipt_scanner_agent

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(..., description="Receipt image or video file"),
    user_id: str = Form(..., description="User ID"),
):
    """
    Upload receipt file and get analysis results immediately
    
    Simple endpoint that:
    1. Accepts multipart/form-data with a file
    2. Processes the receipt using AI
    3. Returns the analysis results directly
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        file_extension = file.filename.lower().split('.')[-1]
        
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            media_type = "image"
        elif file_extension in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
            media_type = "video"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: jpg, png, mp4, mov"
            )

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / 1024 / 1024

        # Basic size validation
        max_size_mb = 10 if media_type == "image" else 50
        if file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({file_size_mb:.2f}MB). Max: {max_size_mb}MB"
            )

        logger.info(f"Processing {media_type} receipt for user {user_id}, size: {file_size_mb:.2f}MB")

        # Get agent and analyze
        agent = get_receipt_scanner_agent()
        result = agent.analyze_receipt(file_content, media_type, user_id)

        logger.info(f"Receipt analysis completed for user {user_id}")
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Receipt upload failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
