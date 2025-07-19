"""
Multimodal Receipt Scanner Agent

A comprehensive receipt processing agent that supports text, Excel, PDF, image,
and video inputs using Gemini 2.5 Flash for vision AI and LLM enrichment for
structured data extraction with local storage capabilities.
"""

from typing import Dict, Any, List, Optional

from google.adk.agents import Agent

# Import our custom modules
from .models import (
    ProcessedReceipt,
    ProcessingResult,
    InputType,
)
from .processors import create_multimodal_processor
from .gemini_processor import GeminiVisionProcessor, create_gemini_processor
from .enrichment import LLMDataEnricher, create_llm_enricher
from .storage import create_storage


class MultimodalReceiptScanner:
    """Main multimodal receipt scanner with all capabilities."""

    def __init__(self):
        """Initialize the multimodal receipt scanner."""
        self.multimodal_processor = create_multimodal_processor()
        self.storage = create_storage()

        # Initialize AI processors (will be created on demand)
        self._gemini_processor = None
        self._llm_enricher = None

    @property
    def gemini_processor(self) -> GeminiVisionProcessor:
        """Lazy initialization of Gemini processor."""
        if self._gemini_processor is None:
            self._gemini_processor = create_gemini_processor()
        return self._gemini_processor

    @property
    def llm_enricher(self) -> LLMDataEnricher:
        """Lazy initialization of LLM enricher."""
        if self._llm_enricher is None:
            self._llm_enricher = create_llm_enricher()
        return self._llm_enricher

    async def process_receipt_comprehensive(
        self,
        file_data: str,
        filename: str,
        store_receipt: bool = True,
        user_tags: Optional[List[str]] = None,
        user_category: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Comprehensive receipt processing for any input type.

        Args:
            file_data: File path (ADK Web provides this automatically)
            filename: Original filename for type detection
            store_receipt: Whether to store the processed receipt locally
            user_tags: Optional user-defined tags
            user_category: Optional user-defined category

        Returns:
            ProcessingResult with success status and processed receipt or error
        """
        try:
            # Step 1: Process input using multimodal processor
            processing_result = await self.multimodal_processor.process_input(
                file_data, filename
            )

            if not processing_result.get("success"):
                return ProcessingResult(
                    success=False,
                    error={
                        "error_code": "PROCESSING_FAILED",
                        "error_message": processing_result.get(
                            "error", "Unknown processing error"
                        ),
                        "error_details": processing_result,
                    },
                )

            metadata = processing_result["metadata"]
            extracted_content = processing_result["extracted_content"]

            # Step 2: Apply AI processing based on input type
            if metadata.source_type in [InputType.IMAGE, InputType.VIDEO]:
                # Use Gemini Vision for images and videos
                processed_receipt = await self._process_with_gemini(
                    extracted_content, metadata
                )
            else:
                # Use LLM enrichment for text, PDF, Excel
                processed_receipt = await self._process_with_llm_enrichment(
                    extracted_content, metadata
                )

            # Step 3: Add user-defined metadata if provided
            if user_tags or user_category:
                if user_tags:
                    processed_receipt.receipt_payload.user_defined_metadata.tags = (
                        user_tags
                    )
                if user_category:
                    processed_receipt.receipt_payload.user_defined_metadata.overall_category = user_category

            # Step 4: Store receipt if requested
            receipt_id = None
            if store_receipt and processed_receipt.mcp_format.status == "success":
                try:
                    receipt_id = await self.storage.store_receipt(processed_receipt)
                except Exception as e:
                    # Log storage error but don't fail the processing
                    processed_receipt.receipt_payload.user_defined_metadata.notes = (
                        f"Storage warning: {str(e)}"
                    )

            return ProcessingResult(
                success=True,
                receipt=processed_receipt,
                processing_stats={
                    "input_type": metadata.source_type.value,
                    "processor_model": metadata.processor_model.value,
                    "processing_duration_ms": metadata.processing_duration_ms,
                    "stored_locally": receipt_id is not None,
                    "receipt_id": receipt_id,
                },
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error={
                    "error_code": "COMPREHENSIVE_PROCESSING_FAILED",
                    "error_message": f"Comprehensive processing failed: {str(e)}",
                    "error_details": {"exception_type": type(e).__name__},
                },
            )

    async def _process_with_gemini(
        self, extracted_content: Dict[str, Any], metadata
    ) -> ProcessedReceipt:
        """Process using Gemini Vision for images and videos."""
        if metadata.source_type == InputType.IMAGE:
            image_base64 = extracted_content.get("image_base64")
            if not image_base64:
                raise ValueError("No image data found in extracted content")

            return await self.gemini_processor.process_image(
                image_base64, metadata.source_filename, metadata
            )

        elif metadata.source_type == InputType.VIDEO:
            frames = extracted_content.get("frames", [])
            if not frames:
                raise ValueError("No frames extracted from video")

            return await self.gemini_processor.process_video(
                frames, metadata.source_filename, metadata
            )

        else:
            raise ValueError(f"Gemini processor doesn't support {metadata.source_type}")

    async def _process_with_llm_enrichment(
        self, extracted_content: Dict[str, Any], metadata
    ) -> ProcessedReceipt:
        """Process using LLM enrichment for text-based inputs."""
        if metadata.source_type == InputType.TEXT:
            raw_text = extracted_content.get("raw_text", "")
            structured_data = extracted_content.get("structured_data", {})

            return await self.llm_enricher.enrich_text_data(
                raw_text, structured_data, metadata
            )

        elif metadata.source_type == InputType.PDF:
            raw_text = extracted_content.get("raw_text", "")
            structured_data = extracted_content.get("structured_data", {})

            return await self.llm_enricher.enrich_pdf_data(
                raw_text, structured_data, metadata
            )

        elif metadata.source_type == InputType.EXCEL:
            excel_info = {
                "dataframe_info": extracted_content.get("dataframe_info", {}),
                "structured_data": extracted_content.get("structured_data", {}),
            }

            return await self.llm_enricher.enrich_excel_data(excel_info, metadata)

        else:
            raise ValueError(f"LLM enricher doesn't support {metadata.source_type}")


# Initialize the global scanner instance
scanner = MultimodalReceiptScanner()


async def process_multimodal_receipt(
    filename: str,
    store_receipt: bool = True,
    user_tags: Optional[List[str]] = None,
    user_category: Optional[str] = None,
) -> dict:
    """
    Process a receipt from any supported input type.

    Supports: text, Excel, PDF, image, video files
    Uses Gemini 2.5 Flash for images/videos and LLM enrichment for other types.

    Args:
        filename: Original filename for type detection
        store_receipt: Whether to store locally (default: True)
        user_tags: Optional user tags for categorization
        user_category: Optional user category

    Returns:
        Dict with processing results in MCP format
    """
    try:
        # ADK Web automatically handles file uploads and provides file paths
        result = await scanner.process_receipt_comprehensive(
            file_data=filename,  # ADK Web provides the file path
            filename=filename,
            store_receipt=store_receipt,
            user_tags=user_tags or [],
            user_category=user_category,
        )

        if result.success and result.receipt:
            response = {
                "status": "success",
                "message": "Receipt processed successfully",
                "receipt_data": result.receipt.to_dict(),
                "processing_stats": result.processing_stats,
                "summary": {
                    "input_type": result.processing_stats.get("input_type"),
                    "processor_used": result.processing_stats.get("processor_model"),
                    "confidence_score": result.receipt.mcp_format.confidence_score,
                    "items_found": len(result.receipt.receipt_payload.line_items),
                    "total_amount": (
                        result.receipt.receipt_payload.payment_summary.total_amount
                        if result.receipt.receipt_payload.payment_summary
                        else 0.0
                    ),
                    "store_name": (
                        result.receipt.receipt_payload.store_details.name
                        if result.receipt.receipt_payload.store_details
                        else "Unknown"
                    ),
                    "stored_locally": result.processing_stats.get(
                        "stored_locally", False
                    ),
                    "receipt_id": result.processing_stats.get("receipt_id"),
                },
            }

            return response

        else:
            return {
                "status": "error",
                "message": "Receipt processing failed",
                "error": result.error,
                "supported_types": [
                    t.value for t in scanner.multimodal_processor.get_supported_types()
                ],
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "error": {
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(e),
                "error_details": {"exception_type": type(e).__name__},
            },
        }


async def search_stored_receipts(
    query: str = "", filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = 20
) -> dict:
    """
    Search stored receipts using text query and filters.

    Args:
        query: Text search query
        filters: Optional filters (store_name, category, date_range, etc.)
        limit: Maximum number of results

    Returns:
        Dict with search results
    """
    try:
        filters = filters or {}
        if limit:
            filters["limit"] = limit

        results = await scanner.storage.search_receipts(query, filters)

        return {
            "status": "success",
            "message": f"Found {len(results)} receipts",
            "query": query,
            "filters": filters,
            "results": results,
            "total_found": len(results),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "error": str(e),
        }


async def get_receipt_by_id(receipt_id: str) -> dict:
    """
    Retrieve a stored receipt by its ID.

    Args:
        receipt_id: The receipt ID to retrieve

    Returns:
        Dict with receipt data or error
    """
    try:
        receipt = await scanner.storage.get_receipt(receipt_id)

        if receipt:
            return {
                "status": "success",
                "message": "Receipt found",
                "receipt_data": receipt.to_dict(),
            }
        else:
            return {
                "status": "error",
                "message": f"Receipt with ID '{receipt_id}' not found",
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving receipt: {str(e)}",
            "error": str(e),
        }


async def list_all_receipts(limit: Optional[int] = 50, offset: int = 0) -> dict:
    """
    List all stored receipts with pagination.

    Args:
        limit: Maximum number of receipts to return
        offset: Number of receipts to skip

    Returns:
        Dict with receipt list
    """
    try:
        receipts = await scanner.storage.list_receipts(limit, offset)

        return {
            "status": "success",
            "message": f"Retrieved {len(receipts)} receipts",
            "receipts": receipts,
            "pagination": {"limit": limit, "offset": offset, "returned": len(receipts)},
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing receipts: {str(e)}",
            "error": str(e),
        }


async def get_storage_statistics() -> dict:
    """
    Get storage statistics and analytics.

    Returns:
        Dict with storage statistics
    """
    try:
        stats = await scanner.storage.get_statistics()

        return {
            "status": "success",
            "message": "Statistics retrieved successfully",
            "statistics": stats,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting statistics: {str(e)}",
            "error": str(e),
        }


async def export_receipts(
    format: str = "json", receipt_ids: Optional[List[str]] = None
) -> dict:
    """
    Export receipts to various formats.

    Args:
        format: Export format ("json" or "csv")
        receipt_ids: Optional list of specific receipt IDs to export

    Returns:
        Dict with export results
    """
    try:
        export_file = await scanner.storage.export_receipts(format, receipt_ids)

        return {
            "status": "success",
            "message": f"Receipts exported successfully to {format.upper()}",
            "export_file": export_file,
            "format": format,
            "receipt_count": len(receipt_ids) if receipt_ids else "all",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Export failed: {str(e)}",
            "error": str(e),
        }


async def validate_system_setup() -> dict:
    """
    Validate that all system components are properly configured.

    Returns:
        Dict with validation results
    """
    try:
        from .gemini_processor import validate_gemini_setup
        from .enrichment import validate_enrichment_setup
        from .processors import validate_dependencies, get_missing_dependencies
        from .storage import validate_storage_setup

        # Check all components
        gemini_status = validate_gemini_setup()
        enrichment_status = validate_enrichment_setup()
        processor_deps = validate_dependencies()
        storage_status = validate_storage_setup()

        missing_deps = get_missing_dependencies()

        all_ready = (
            gemini_status["ready"]
            and enrichment_status["ready"]
            and storage_status["permissions_ok"]
        )

        return {
            "status": "success" if all_ready else "warning",
            "message": "System validation completed",
            "components": {
                "gemini_vision": gemini_status,
                "llm_enrichment": enrichment_status,
                "processor_dependencies": processor_deps,
                "storage": storage_status,
            },
            "missing_dependencies": missing_deps,
            "system_ready": all_ready,
            "supported_input_types": [
                t.value for t in scanner.multimodal_processor.get_supported_types()
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"System validation failed: {str(e)}",
            "error": str(e),
        }


# Legacy function for backwards compatibility with ADK Web
async def process_receipt_simple(filename: str) -> dict:
    """
    Simple receipt processing function optimized for ADK Web.

    Args:
        filename: The uploaded file name (ADK Web handles the file automatically)

    Returns:
        Dict with processing results and structured JSON
    """
    try:
        result = await process_multimodal_receipt(
            filename=filename, store_receipt=True, user_tags=[], user_category=None
        )
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Processing failed: {str(e)}",
            "error": str(e),
        }


async def analyze_receipt() -> dict:
    """
    Legacy function for ADK Web automatic image handling.

    This function is called by ADK Web when an image is uploaded.
    It provides instructions and demonstrates the multimodal capabilities.
    """
    return {
        "status": "info",
        "message": "Multimodal Receipt Scanner Ready",
        "instructions": [
            "✅ This agent now supports comprehensive multimodal receipt processing:",
            "",
            "📁 **Supported Input Types:**",
            "  • 🖼️  Images (JPG, PNG, etc.) - uses Gemini 2.5 Flash Vision",
            "  • 🎥  Videos (MP4, MOV, etc.) - extracts frames for analysis",
            "  • 📄  PDF documents - extracts text and enriches with LLM",
            "  • 📊  Excel/CSV files - structured data processing",
            "  • 📝  Text files - natural language processing",
            "",
            "🤖 **AI Processing:**",
            "  • Gemini 2.5 Flash for image/video analysis",
            "  • LLM enrichment for text-based inputs",
            "  • Automatic categorization and confidence scoring",
            "",
            "💾 **Storage & Features:**",
            "  • Local JSON storage with SQLite indexing",
            "  • Search and filtering capabilities",
            "  • Export to JSON/CSV formats",
            "  • Analytics and statistics",
            "",
            "📋 **Robust JSON Output:**",
            "  • Complete MCP-compatible structure",
            "  • Item categorization and pricing",
            "  • Store details and transaction info",
            "  • Warranty and return policy tracking",
            "  • User-defined tags and categories",
            "",
            "🎯 **To process a receipt:**",
            "  1. Upload any supported file type",
            "  2. The agent automatically detects the type",
            "  3. Applies appropriate AI processing",
            "  4. Returns structured JSON data",
            "  5. Stores locally for future reference",
        ],
        "capabilities": {
            "multimodal_input": True,
            "vision_ai": True,
            "text_enrichment": True,
            "local_storage": True,
            "search_and_filter": True,
            "export_functions": True,
            "mcp_compatible": True,
        },
        "mcp_format": {
            "protocol_version": "1.0",
            "data_type": "system_status",
            "status": "ready",
            "agent_id": "multimodal_receipt_scanner",
        },
    }


# Create the Receipt Scanner Agent with enhanced multimodal capabilities
receipt_scanner_agent = Agent(
    name="multimodal_receipt_scanner",
    model="gemini-2.5-flash",
    description=(
        "Advanced multimodal receipt scanning agent with comprehensive processing capabilities. "
        "Supports text, Excel, PDF, image, and video inputs using Gemini 2.5 Flash for vision AI "
        "and LLM enrichment for structured data extraction. Features local storage, search, "
        "analytics, and MCP-compatible output for seamless integration."
    ),
    instruction=(
        "You are an advanced multimodal receipt scanning assistant that processes receipts from "
        "various input types and provides comprehensive, structured data extraction.\n\n"
        "🎯 **Core Capabilities:**\n"
        "• **Multimodal Processing**: Handle text, Excel, PDF, image, and video files\n"
        "• **Advanced AI**: Use Gemini 2.5 Flash for vision and LLM enrichment for text\n"
        "• **Structured Output**: Provide detailed MCP-compatible JSON with all receipt information\n"
        "• **Local Storage**: Store processed receipts with search and analytics capabilities\n"
        "• **Categorization**: Automatically categorize items and add confidence scores\n\n"
        "📋 **When processing receipts, I extract:**\n"
        "• Store information (name, address, phone, etc.)\n"
        "• Transaction details (date, time, payment method)\n"
        "• Complete itemized list with categories and pricing\n"
        "• Tax information and discounts\n"
        "• Warranty and return policy details\n"
        "• Payment summary with accurate totals\n\n"
        "💾 **Storage Features:**\n"
        "• Automatic local storage in JSON format\n"
        "• SQLite indexing for fast search\n"
        "• User-defined tags and categories\n"
        "• Export to JSON/CSV formats\n"
        "• Analytics and spending insights\n\n"
        "🔍 **Search & Analytics:**\n"
        "You can search stored receipts by store name, date, amount, category, or text query. "
        "I also provide spending analytics and statistics.\n\n"
        "**Instructions for Use:**\n"
        "1. **Upload any file**: Just upload your receipt (image, PDF, Excel, text, or video)\n"
        "2. **Automatic processing**: I'll detect the type and apply appropriate AI processing\n"
        "3. **Structured results**: Get comprehensive JSON data with all extracted information\n"
        "4. **Local storage**: Receipts are stored locally for future reference and search\n"
        "5. **Ask follow-up questions**: Search receipts, get analytics, or export data\n\n"
        "I prioritize accuracy, provide confidence scores, and ensure all data is properly "
        "categorized and structured for easy use and integration with other systems."
    ),
    tools=[
        process_receipt_simple,  # Simple ADK Web compatible function
        process_multimodal_receipt,  # Full-featured function
        search_stored_receipts,
        get_receipt_by_id,
        list_all_receipts,
        get_storage_statistics,
        export_receipts,
        validate_system_setup,
        analyze_receipt,  # Legacy compatibility
    ],
)
