"""
Multimodal Input Processors for Receipt Scanner

This module provides processors for different input types including:
- Text input processing
- Excel/CSV file processing
- PDF document processing
- Image processing (JPEG, PNG, etc.)
- Video processing (MP4, MOV, etc.)

Each processor extracts relevant data and prepares it for AI model analysis.
"""
import cv2
import os
import io
import base64
import tempfile
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import mimetypes
import pandas as pd
from PIL import Image
import fitz

from .models import InputType, ProcessingMetadata, ProcessorModel, create_receipt_id


class InputProcessor:
    """Base class for all input processors."""

    def __init__(self):
        self.supported_types = []

    def can_process(self, input_type: InputType) -> bool:
        """Check if this processor can handle the given input type."""
        return input_type in self.supported_types

    async def process(
        self, data: Union[str, bytes], filename: str, **kwargs
    ) -> Dict[str, Any]:
        """Process the input data and return structured information."""
        raise NotImplementedError("Subclasses must implement process method")

    def _create_metadata(
        self, filename: str, input_type: InputType, file_size: Optional[int] = None
    ) -> ProcessingMetadata:
        """Create processing metadata for the input."""
        return ProcessingMetadata(
            receipt_id=create_receipt_id(),
            source_filename=filename,
            source_type=input_type,
            processor_model=ProcessorModel.CUSTOM_LLM,  # Will be updated by specific processors
            file_size_bytes=file_size,
        )


class TextProcessor(InputProcessor):
    """Processor for plain text input."""

    def __init__(self):
        super().__init__()
        self.supported_types = [InputType.TEXT]

    async def process(
        self, data: Union[str, bytes], filename: str, **kwargs
    ) -> Dict[str, Any]:
        """Process text input and extract receipt-like information."""
        if isinstance(data, bytes):
            text_content = data.decode("utf-8", errors="ignore")
        else:
            text_content = data

        file_size = len(text_content.encode("utf-8"))
        metadata = self._create_metadata(filename, InputType.TEXT, file_size)

        # Extract potential receipt information from text
        extracted_info = self._extract_text_info(text_content)

        return {
            "success": True,
            "metadata": metadata,
            "extracted_content": {
                "raw_text": text_content,
                "structured_data": extracted_info,
                "processing_method": "text_analysis",
            },
            "requires_llm_enrichment": True,
            "confidence_score": 0.6,  # Text processing has medium confidence
        }

    def _extract_text_info(self, text: str) -> Dict[str, Any]:
        """Extract structured information from text content."""
        import re

        # Basic patterns for receipt information
        patterns = {
            "total_amount": r"(?:total|amount|sum)[\s:$]*(\d+\.?\d*)",
            "date": r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})",
            "store_name": r"^([A-Za-z\s&]+)(?=\n|\r)",
            "phone": r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            "address": r"(\d+\s+[A-Za-z\s,]+)",
            "items": r"(.+?)\s+\$?(\d+\.?\d*)",
        }

        extracted = {}

        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                if key == "items":
                    extracted[key] = [
                        {"description": m[0].strip(), "price": float(m[1])}
                        for m in matches
                    ]
                else:
                    extracted[key] = matches[0] if len(matches) == 1 else matches

        return extracted


class ExcelProcessor(InputProcessor):
    """Processor for Excel and CSV files."""

    def __init__(self):
        super().__init__()
        self.supported_types = [InputType.EXCEL]

    async def process(
        self, data: Union[str, bytes], filename: str, **kwargs
    ) -> Dict[str, Any]:
        """Process Excel/CSV file and extract receipt information."""
        try:
            # Determine file type
            file_ext = Path(filename).suffix.lower()

            if isinstance(data, str):
                # Assume it's a file path
                df = self._read_file(data, file_ext)
                file_size = os.path.getsize(data) if os.path.exists(data) else None
            else:
                # Assume it's file content as bytes
                df = self._read_bytes(data, file_ext)
                file_size = len(data)

            metadata = self._create_metadata(filename, InputType.EXCEL, file_size)

            # Extract receipt information from DataFrame
            extracted_info = self._extract_excel_info(df)

            return {
                "success": True,
                "metadata": metadata,
                "extracted_content": {
                    "dataframe_info": {
                        "shape": df.shape,
                        "columns": df.columns.tolist(),
                        "sample_data": df.head().to_dict("records"),
                    },
                    "structured_data": extracted_info,
                    "processing_method": "excel_analysis",
                },
                "requires_llm_enrichment": True,
                "confidence_score": 0.8,  # Excel has structured data, higher confidence
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Excel processing failed: {str(e)}",
                "requires_llm_enrichment": False,
            }

    def _read_file(self, file_path: str, file_ext: str) -> pd.DataFrame:
        """Read file based on extension."""
        if file_ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        elif file_ext == ".csv":
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")

    def _read_bytes(self, data: bytes, file_ext: str) -> pd.DataFrame:
        """Read bytes data based on file extension."""
        buffer = io.BytesIO(data)

        if file_ext in [".xlsx", ".xls"]:
            return pd.read_excel(buffer)
        elif file_ext == ".csv":
            return pd.read_csv(buffer)
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")

    def _extract_excel_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract receipt-like information from DataFrame."""
        extracted = {
            "potential_items": [],
            "potential_totals": [],
            "summary_stats": df.describe().to_dict()
            if df.select_dtypes(include=["number"]).shape[1] > 0
            else {},
        }

        # Look for columns that might contain item descriptions and prices
        for col in df.columns:
            col_lower = col.lower()
            if any(
                keyword in col_lower
                for keyword in ["item", "product", "description", "name"]
            ):
                extracted["potential_items"].extend(
                    df[col].dropna().astype(str).tolist()
                )
            elif any(
                keyword in col_lower for keyword in ["price", "amount", "cost", "total"]
            ):
                numeric_values = pd.to_numeric(df[col], errors="coerce").dropna()
                extracted["potential_totals"].extend(numeric_values.tolist())

        return extracted


class PDFProcessor(InputProcessor):
    """
    Processor for PDF documents using PyMuPDF (fitz).

    PyMuPDF advantages over PyPDF2/pdfplumber:
    - 5-10x faster performance
    - Better text extraction accuracy
    - Superior handling of complex layouts
    - Lower memory footprint
    - Better Unicode support
    - Can extract tables and images
    """

    def __init__(self):
        super().__init__()
        self.supported_types = [InputType.PDF]

    async def process(
        self, data: Union[str, bytes], filename: str, **kwargs
    ) -> Dict[str, Any]:
        """Process PDF file and extract text content."""
        try:
            if isinstance(data, str):
                # File path
                with open(data, "rb") as file:
                    pdf_content = file.read()
                file_size = os.path.getsize(data) if os.path.exists(data) else None
            else:
                # Bytes data
                pdf_content = data
                file_size = len(data)

            metadata = self._create_metadata(filename, InputType.PDF, file_size)

            # Extract text using multiple methods
            extracted_text = self._extract_pdf_text(pdf_content)

            # Process extracted text similar to TextProcessor
            text_processor = TextProcessor()
            text_result = await text_processor.process(extracted_text, filename)

            return {
                "success": True,
                "metadata": metadata,
                "extracted_content": {
                    "raw_text": extracted_text,
                    "structured_data": text_result.get("extracted_content", {}).get(
                        "structured_data", {}
                    ),
                    "processing_method": "pdf_text_extraction",
                    "text_length": len(extracted_text),
                },
                "requires_llm_enrichment": True,
                "confidence_score": 0.7,  # PDF extraction has good confidence
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}",
                "requires_llm_enrichment": False,
            }

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF using PyMuPDF (superior performance and accuracy)."""
        text_content = []

        try:
            # Open PDF document with PyMuPDF
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]

                # Extract text with better formatting preservation
                page_text = page.get_text()

                if page_text.strip():
                    text_content.append(page_text)

                # PyMuPDF bonus: Extract tables and images if needed
                # tables = page.find_tables()  # For future table extraction
                # images = page.get_images()    # For future image extraction

            pdf_document.close()

        except Exception:
            # Fallback: try to extract as plain text
            try:
                pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
                for page_num in range(pdf_document.page_count):
                    page = pdf_document[page_num]
                    # Use simpler text extraction as fallback
                    page_text = page.get_text("text")
                    if page_text.strip():
                        text_content.append(page_text)
                pdf_document.close()
            except Exception:
                pass

        return (
            "\n".join(text_content)
            if text_content
            else "Could not extract text from PDF"
        )


class ImageProcessor(InputProcessor):
    """Processor for image files."""

    def __init__(self):
        super().__init__()
        self.supported_types = [InputType.IMAGE]

    async def process(
        self, data: Union[str, bytes], filename: str, **kwargs
    ) -> Dict[str, Any]:
        """Process image file and prepare for Gemini Vision processing."""
        try:
            if isinstance(data, str):
                # File path
                async with aiofiles.open(data, "rb") as file:
                    image_content = await file.read()
                file_size = os.path.getsize(data) if os.path.exists(data) else None
            else:
                # Bytes data
                image_content = data
                file_size = len(data)

            metadata = self._create_metadata(filename, InputType.IMAGE, file_size)
            metadata.processor_model = ProcessorModel.GEMINI_2_5_FLASH

            # Validate and process image
            image_info = self._process_image(image_content)

            # Convert to base64 for API calls
            image_base64 = base64.b64encode(image_content).decode("utf-8")

            return {
                "success": True,
                "metadata": metadata,
                "extracted_content": {
                    "image_base64": image_base64,
                    "image_info": image_info,
                    "processing_method": "image_vision_ai",
                },
                "requires_llm_enrichment": False,  # Gemini Vision can handle directly
                "confidence_score": 0.95,  # Vision AI has high confidence for images
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Image processing failed: {str(e)}",
                "requires_llm_enrichment": False,
            }

    def _process_image(self, image_content: bytes) -> Dict[str, Any]:
        """Process image and extract metadata."""
        image = Image.open(io.BytesIO(image_content))

        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "has_transparency": image.mode in ("RGBA", "LA")
            or "transparency" in image.info,
        }


class VideoProcessor(InputProcessor):
    """Processor for video files."""

    def __init__(self):
        super().__init__()
        self.supported_types = [InputType.VIDEO]

    async def process(
        self, data: Union[str, bytes], filename: str, **kwargs
    ) -> Dict[str, Any]:
        """Process video file and extract frames for analysis."""
        try:
            # Save video to temporary file for OpenCV processing
            if isinstance(data, str):
                video_path = data
                file_size = os.path.getsize(data) if os.path.exists(data) else None
            else:
                # Create temporary file asynchronously
                fd, temp_path = tempfile.mkstemp(suffix=".mp4")
                try:
                    # Close the file descriptor and use aiofiles to write
                    os.close(fd)
                    async with aiofiles.open(temp_path, "wb") as temp_file:
                        await temp_file.write(data)
                    video_path = temp_path
                except Exception:
                    # Clean up if writing fails
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
                file_size = len(data)

            metadata = self._create_metadata(filename, InputType.VIDEO, file_size)
            metadata.processor_model = ProcessorModel.GEMINI_2_5_FLASH

            # Extract frames from video
            frames_info = self._extract_video_frames(video_path)

            # Clean up temporary file if created
            if isinstance(data, bytes) and os.path.exists(video_path):
                os.unlink(video_path)

            return {
                "success": True,
                "metadata": metadata,
                "extracted_content": {
                    "frames": frames_info["frames"],
                    "video_info": frames_info["video_info"],
                    "processing_method": "video_frame_extraction",
                },
                "requires_llm_enrichment": False,  # Gemini Vision can handle frames
                "confidence_score": 0.85,  # Video processing has good confidence
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Video processing failed: {str(e)}",
                "requires_llm_enrichment": False,
            }

    def _extract_video_frames(
        self, video_path: str, max_frames: int = 5
    ) -> Dict[str, Any]:
        """Extract representative frames from video."""
        cap = cv2.VideoCapture(video_path)

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        frames = []

        if frame_count > 0:
            # Extract frames at regular intervals
            interval = max(1, frame_count // max_frames)

            for i in range(0, frame_count, interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret:
                    # Convert frame to JPEG bytes
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_bytes = buffer.tobytes()
                    frame_base64 = base64.b64encode(frame_bytes).decode("utf-8")

                    frames.append(
                        {
                            "frame_number": i,
                            "timestamp": i / fps if fps > 0 else 0,
                            "frame_base64": frame_base64,
                        }
                    )

                if len(frames) >= max_frames:
                    break

        cap.release()

        return {
            "frames": frames,
            "video_info": {
                "fps": fps,
                "frame_count": frame_count,
                "duration_seconds": duration,
                "extracted_frames": len(frames),
            },
        }


class MultimodalProcessor:
    """Main processor that handles all input types."""

    def __init__(self):
        self.processors = {
            InputType.TEXT: TextProcessor(),
            InputType.EXCEL: ExcelProcessor(),
            InputType.PDF: PDFProcessor(),
            InputType.IMAGE: ImageProcessor(),
            InputType.VIDEO: VideoProcessor(),
        }

    def detect_input_type(
        self, filename: str, data: Union[str, bytes] = None
    ) -> InputType:
        """Detect input type based on filename and optionally data content."""
        file_ext = Path(filename).suffix.lower()

        # Image extensions
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        if file_ext in image_exts:
            return InputType.IMAGE

        # Video extensions
        video_exts = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"}
        if file_ext in video_exts:
            return InputType.VIDEO

        # Document extensions
        pdf_exts = {".pdf"}
        if file_ext in pdf_exts:
            return InputType.PDF

        # Spreadsheet extensions
        excel_exts = {".xlsx", ".xls", ".csv"}
        if file_ext in excel_exts:
            return InputType.EXCEL

        # Default to text for unknown or text extensions
        text_exts = {".txt", ".text", ""}
        if file_ext in text_exts or not file_ext:
            return InputType.TEXT

        # If we can't determine from extension, try MIME type
        if data:
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                if mime_type.startswith("image/"):
                    return InputType.IMAGE
                elif mime_type.startswith("video/"):
                    return InputType.VIDEO
                elif mime_type == "application/pdf":
                    return InputType.PDF
                elif mime_type in [
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ]:
                    return InputType.EXCEL

        # Final fallback
        return InputType.TEXT

    async def process_input(
        self,
        data: Union[str, bytes],
        filename: str,
        input_type: Optional[InputType] = None,
    ) -> Dict[str, Any]:
        """Process input of any supported type."""
        if input_type is None:
            input_type = self.detect_input_type(filename, data)

        processor = self.processors.get(input_type)
        if not processor:
            return {
                "success": False,
                "error": f"No processor available for input type: {input_type}",
                "requires_llm_enrichment": False,
            }

        start_time = datetime.now()
        result = await processor.process(data, filename)
        end_time = datetime.now()

        # Add processing duration
        if result.get("success") and "metadata" in result:
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            result["metadata"].processing_duration_ms = duration_ms

        return result

    def get_supported_types(self) -> List[InputType]:
        """Get list of supported input types."""
        return list(self.processors.keys())

    def get_processor_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available processors."""
        info = {}
        for input_type, processor in self.processors.items():
            info[input_type.value] = {
                "class_name": processor.__class__.__name__,
                "supported_types": [t.value for t in processor.supported_types],
            }
        return info


# Utility functions
def create_multimodal_processor() -> MultimodalProcessor:
    """Create a configured multimodal processor instance."""
    return MultimodalProcessor()
