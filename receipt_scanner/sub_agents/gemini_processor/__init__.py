"""
Gemini Processor Sub-Agent

This sub-agent handles image and video processing using Gemini 2.5 Flash Vision AI.
It processes visual content to extract receipt information.
"""

from google.adk.agents import Agent
from typing import Dict, Any, List, Optional
from ...models import ProcessedReceipt, ProcessingMetadata
from .processor import GeminiVisionProcessor


def create_gemini_processor() -> GeminiVisionProcessor:
    """Factory function to create Gemini vision processor."""
    return GeminiVisionProcessor()


# Gemini Vision Processor Agent
gemini_processor_agent = Agent(
    name="gemini_processor",
    model="gemini-2.5-flash",
    description=(
        "Processes images and videos using Gemini 2.5 Flash Vision AI "
        "to extract receipt information from visual content."
    ),
    instruction=(
        "You are a vision AI processor specialized in receipt analysis. "
        "Your job is to:\n"
        "1. Analyze images to extract receipt information\n"
        "2. Process video frames to identify receipt content\n"
        "3. Extract structured data including store details, items, prices, taxes\n"
        "4. Provide confidence scores for extracted information\n\n"
        "You excel at:\n"
        "- Reading text from receipt images with high accuracy\n"
        "- Identifying and categorizing purchased items\n"
        "- Extracting financial information (prices, taxes, totals)\n"
        "- Understanding receipt layouts and structures\n"
        "- Processing both clear and blurry receipt images"
    ),
)


async def process_image(
    image_base64: str,
    filename: str, 
    metadata: ProcessingMetadata
) -> ProcessedReceipt:
    """
    Process image using Gemini Vision AI.
    
    Args:
        image_base64: Base64 encoded image data
        filename: Original filename
        metadata: Processing metadata
        
    Returns:
        Processed receipt with extracted information
    """
    processor = create_gemini_processor()
    return await processor.process_image(image_base64, filename, metadata)


async def process_video(
    frames: List[Dict[str, Any]],
    filename: str,
    metadata: ProcessingMetadata
) -> ProcessedReceipt:
    """
    Process video frames using Gemini Vision AI.
    
    Args:
        frames: Extracted video frames with base64 data
        filename: Original filename
        metadata: Processing metadata
        
    Returns:
        Processed receipt with extracted information
    """
    processor = create_gemini_processor()
    return await processor.process_video(frames, filename, metadata) 