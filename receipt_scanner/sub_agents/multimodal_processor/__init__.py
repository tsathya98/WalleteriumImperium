"""
Multimodal Processor Sub-Agent

This sub-agent handles the initial processing of various input types including:
- Text input processing
- Excel/CSV file processing
- PDF document processing  
- Image processing
- Video processing
"""

from google.adk.agents import Agent
from typing import Dict, Any, Optional, Union
from ...models import InputType, ProcessingMetadata
from .processor import MultimodalProcessor


def create_multimodal_processor() -> MultimodalProcessor:
    """Factory function to create multimodal processor."""
    return MultimodalProcessor()


# Multimodal Processor Agent
multimodal_processor_agent = Agent(
    name="multimodal_processor",
    model="gemini-2.5-flash", 
    description=(
        "Processes input of any supported type (text, Excel, PDF, image, video) "
        "and extracts content for further AI processing."
    ),
    instruction=(
        "You are a multimodal input processor that handles different file types. "
        "Your job is to:\n"
        "1. Detect the input type based on filename and content\n"
        "2. Extract relevant data using the appropriate processor\n"
        "3. Return structured metadata and content for further processing\n\n"
        "Supported input types:\n"
        "- Images: Extract image data for vision AI processing\n"
        "- Videos: Extract frames for vision AI analysis\n"
        "- PDFs: Extract text content using OCR\n"
        "- Excel/CSV: Parse structured data\n"
        "- Text: Process raw text content"
    ),
)


async def process_input(
    data: Union[str, bytes], 
    filename: str, 
    input_type: Optional[InputType] = None
) -> Dict[str, Any]:
    """
    Process input using the multimodal processor.
    
    Args:
        data: Input data (file path or bytes)
        filename: Original filename
        input_type: Optional input type override
        
    Returns:
        Processing result with metadata and extracted content
    """
    processor = create_multimodal_processor()
    return await processor.process_input(data, filename, input_type) 