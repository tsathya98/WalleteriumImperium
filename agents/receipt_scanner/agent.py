"""
Enhanced Receipt Scanner Agent with Hybrid Agentic Workflow
Implements sophisticated decision-making logic in a single, efficient call
"""

import datetime
import json
import asyncio
from typing import Dict, Any
import io
from PIL import Image

import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import ReceiptAnalysis, ItemDetail, WarrantyDetails, RecurringDetails, ProcessingMetadata
from .prompts import create_agentic_prompt, create_fallback_values_prompt, create_business_rules_prompt
from .schemas import get_enhanced_receipt_schema
from .validators import validate_and_fix_result

settings = get_settings()
logger = get_logger(__name__)


class EnhancedReceiptScannerAgent:
    """Enhanced Receipt Scanner Agent with Hybrid Agentic Workflow"""

    def __init__(self):
        """Initialize the enhanced agent"""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        self.max_retries = 3
        self.model = None
        self._initialize_vertex_ai()

    def _initialize_vertex_ai(self):
        """Initialize Vertex AI and the Gemini model with enhanced schema"""
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)

            # Configure generation settings for structured output
            generation_config = GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent output
                top_p=0.8,
                top_k=40,
                candidate_count=1,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=get_enhanced_receipt_schema(),
            )

            # Initialize the model with our enhanced schema
            self.model = GenerativeModel(
                model_name=self.model_name, 
                generation_config=generation_config
            )

            logger.info(
                "Enhanced Vertex AI initialized successfully",
                extra={
                    "project_id": self.project_id,
                    "location": self.location,
                    "model": self.model_name,
                },
            )

        except Exception as e:
            logger.error("Failed to initialize Vertex AI", extra={"error": str(e)})
            raise

    async def analyze_receipt_media(
        self, media_bytes: bytes, media_type: str, user_id: str, retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Analyze receipt media using enhanced hybrid agentic workflow

        Args:
            media_bytes: Raw bytes of receipt image or video
            media_type: Type of media ('image' or 'video')
            user_id: User ID for logging
            retry_count: Current retry attempt number

        Returns:
            Enhanced structured receipt analysis data
        """
        try:
            start_time = datetime.datetime.utcnow()
            
            logger.info(
                "Starting enhanced receipt analysis",
                extra={
                    "user_id": user_id,
                    "retry_count": retry_count,
                    "media_type": media_type,
                    "media_size_kb": len(media_bytes) / 1024,
                },
            )

            # Validate and prepare media from raw bytes
            if media_type == "image":
                media_data, mime_type = self._prepare_image_from_bytes(media_bytes)
            elif media_type == "video":
                media_data, mime_type = self._prepare_video_from_bytes(media_bytes)
            else:
                raise ValueError(f"Unsupported media type: {media_type}")

            # Create the enhanced agentic prompt
            prompt = self._create_enhanced_prompt(media_type)

            # Prepare the content for Gemini
            contents = [prompt, Part.from_data(data=media_data, mime_type=mime_type)]

            # Generate content with schema enforcement
            response = await asyncio.to_thread(self.model.generate_content, contents)

            if not response.text:
                raise ValueError("Empty response from Gemini")

            # Parse the guaranteed JSON response
            ai_result = json.loads(response.text)

            # Validate and fix the AI result
            validated_result, validation = validate_and_fix_result(ai_result)

            # Transform to our application model
            receipt_analysis = self._transform_to_receipt_analysis(
                validated_result, user_id, start_time
            )

            # Calculate processing time
            processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()

            logger.info(
                "Enhanced receipt analysis completed successfully",
                extra={
                    "user_id": user_id,
                    "items_extracted": len(receipt_analysis.items),
                    "total_amount": receipt_analysis.amount,
                    "vendor_type": receipt_analysis.metadata.vendor_type if receipt_analysis.metadata else "unknown",
                    "confidence": receipt_analysis.metadata.confidence if receipt_analysis.metadata else "unknown",
                    "retry_count": retry_count,
                    "processing_time": processing_time,
                    "validation_errors": len(validation.errors),
                    "validation_warnings": len(validation.warnings),
                },
            )

            return {
                "status": "success",
                "data": receipt_analysis.dict(),
                "processing_time": processing_time,
                "model_version": self.model_name,
                "validation": {
                    "is_valid": validation.is_valid,
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                }
            }

        except json.JSONDecodeError as e:
            logger.error(
                "JSON parsing failed in enhanced analysis",
                extra={
                    "user_id": user_id,
                    "retry_count": retry_count,
                    "error": str(e),
                    "raw_response": response.text if "response" in locals() else None,
                },
            )

            if retry_count < self.max_retries:
                logger.info(
                    "Retrying with enhanced prompt",
                    extra={"user_id": user_id, "retry_count": retry_count + 1},
                )
                await asyncio.sleep(1)  # Brief delay before retry
                return await self.analyze_receipt_media(
                    media_bytes, media_type, user_id, retry_count + 1
                )

            raise ValueError(
                f"Failed to get valid JSON after {self.max_retries} retries"
            )

        except Exception as e:
            logger.error(
                "Enhanced receipt analysis failed",
                extra={"user_id": user_id, "retry_count": retry_count, "error": str(e)},
            )

            if retry_count < self.max_retries and "quota" not in str(e).lower():
                logger.info(
                    "Retrying enhanced analysis",
                    extra={"user_id": user_id, "retry_count": retry_count + 1},
                )
                await asyncio.sleep(2**retry_count)  # Exponential backoff
                return await self.analyze_receipt_media(
                    media_bytes, media_type, user_id, retry_count + 1
                )

            raise

    def _create_enhanced_prompt(self, media_type: str) -> str:
        """Create the complete enhanced agentic prompt"""
        main_prompt = create_agentic_prompt(media_type)
        fallback_prompt = create_fallback_values_prompt()
        business_rules_prompt = create_business_rules_prompt()
        
        return f"{main_prompt}\n\n{fallback_prompt}\n\n{business_rules_prompt}"

    def _prepare_image_from_bytes(self, image_bytes: bytes) -> tuple[bytes, str]:
        """
        Prepare and validate the image from raw bytes for analysis
        """
        try:
            # Validate and potentially resize image
            image = Image.open(io.BytesIO(image_bytes))

            # Resize if too large (Gemini has size limits)
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                logger.info(
                    "Resizing large image",
                    extra={"original_size": image.size, "max_size": max_size},
                )
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Convert back to bytes
                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", quality=90, optimize=True)
                image_bytes = output_buffer.getvalue()

            return image_bytes, "image/jpeg"

        except Exception as e:
            logger.error("Image preparation failed", extra={"error": str(e)})
            raise ValueError(f"Invalid image data: {str(e)}")

    def _prepare_video_from_bytes(self, video_bytes: bytes) -> tuple[bytes, str]:
        """
        Prepare and validate the video from raw bytes for analysis
        """
        try:
            # Validate video size (larger limit for videos)
            video_size_mb = len(video_bytes) / 1024 / 1024
            max_video_size = 100  # 100MB limit for videos

            if video_size_mb > max_video_size:
                logger.warning(
                    "Video too large",
                    extra={"size_mb": video_size_mb, "max_size_mb": max_video_size},
                )
                raise ValueError(
                    f"Video too large: {video_size_mb:.1f}MB. Maximum size: {max_video_size}MB"
                )

            # Determine video format from the first few bytes
            if video_bytes.startswith(b"\x00\x00\x00"):
                mime_type = "video/mp4"
            elif video_bytes.startswith(b"ftypqt"):
                mime_type = "video/quicktime"
            elif video_bytes.startswith(b"RIFF"):
                mime_type = "video/avi"
            else:
                # Default to mp4 for unknown formats
                mime_type = "video/mp4"

            logger.info(
                "Video prepared for analysis",
                extra={"size_mb": video_size_mb, "mime_type": mime_type},
            )

            return video_bytes, mime_type

        except Exception as e:
            logger.error("Video preparation failed", extra={"error": str(e)})
            raise ValueError(f"Invalid video data: {str(e)}")

    def _transform_to_receipt_analysis(
        self, ai_result: Dict[str, Any], user_id: str, start_time: datetime.datetime
    ) -> ReceiptAnalysis:
        """
        Transform validated AI result to ReceiptAnalysis model

        Args:
            ai_result: Validated AI analysis result
            user_id: User ID for receipt_id generation
            start_time: Processing start time

        Returns:
            ReceiptAnalysis object
        """
        try:
            store_info = ai_result.get("store_info", {})
            items_data = ai_result.get("items", [])
            totals = ai_result.get("totals", {})
            classification = ai_result.get("classification", {})
            processing_meta = ai_result.get("processing_metadata", {})

            # Generate receipt ID
            receipt_id = f"{user_id}_{int(start_time.timestamp())}"

            # Transform date and time
            transaction_date = store_info.get("date", start_time.strftime("%Y-%m-%d"))
            transaction_time = store_info.get("time", "12:00")
            
            # Combine date and time into ISO 8601 format
            if transaction_date and transaction_date not in ["Unknown", "Not provided"]:
                if transaction_time and transaction_time not in ["Unknown", "Not provided"]:
                    time_str = f"{transaction_date}T{transaction_time}:00Z"
                else:
                    time_str = f"{transaction_date}T12:00:00Z"
            else:
                time_str = start_time.isoformat() + "Z"

            # Transform items
            items = []
            for item_data in items_data:
                # Transform warranty details
                warranty = None
                if item_data.get("warranty"):
                    warranty_data = item_data["warranty"]
                    warranty = WarrantyDetails(
                        validUntil=warranty_data["validUntil"],
                        provider=warranty_data.get("provider", "Unknown"),
                        coverage=warranty_data.get("coverage")
                    )

                # Transform recurring details
                recurring = None
                if item_data.get("recurring"):
                    recurring_data = item_data["recurring"]
                    recurring = RecurringDetails(
                        frequency=recurring_data["frequency"],
                        nextBillingDate=recurring_data.get("nextBillingDate"),
                        subscriptionType=recurring_data.get("subscriptionType"),
                        autoRenew=recurring_data.get("autoRenew")
                    )

                item = ItemDetail(
                    name=item_data.get("name", "Unknown Item"),
                    quantity=item_data.get("quantity", 1),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price", 0),
                    category=item_data.get("category", "Other"),
                    description=item_data.get("description", ""),
                    warranty=warranty,
                    recurring=recurring
                )
                items.append(item)

            # Determine top-level warranty and recurring summaries
            top_level_warranty = None
            top_level_recurring = None

            # Find the longest warranty for top-level summary
            warranty_items = [item for item in items if item.warranty]
            if warranty_items:
                # Get the warranty with the longest validity
                longest_warranty = max(warranty_items, key=lambda x: x.warranty.validUntil)
                top_level_warranty = WarrantyDetails(
                    validUntil=longest_warranty.warranty.validUntil,
                    provider="Multiple" if len(warranty_items) > 1 else longest_warranty.warranty.provider,
                    coverage=f"{len(warranty_items)} items with warranties"
                )

            # Find subscription details for top-level summary
            recurring_items = [item for item in items if item.recurring]
            if recurring_items:
                # Use the most common frequency
                frequencies = [item.recurring.frequency for item in recurring_items]
                most_common_freq = max(set(frequencies), key=frequencies.count)
                
                top_level_recurring = RecurringDetails(
                    frequency=most_common_freq,
                    subscriptionType=f"{len(recurring_items)} recurring items",
                    autoRenew=None  # Would need more logic to determine
                )

            # Create processing metadata
            processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()
            metadata = ProcessingMetadata(
                vendor_type=classification.get("vendor_type", "OTHER"),
                confidence=processing_meta.get("confidence", "medium"),
                processing_time_seconds=processing_time,
                model_version=self.model_name
            )

            # Generate intelligent description
            description = self._generate_intelligent_description(
                store_info, items, classification
            )

            # Create the final ReceiptAnalysis object
            receipt_analysis = ReceiptAnalysis(
                receipt_id=receipt_id,
                place=store_info.get("name", "Unknown Store"),
                time=time_str,
                amount=float(totals.get("total", 0)),
                transactionType="debit",  # Default assumption
                category=classification.get("overall_category", "Other"),
                description=description,
                importance="medium",  # Could be enhanced with AI logic
                warranty=top_level_warranty,
                recurring=top_level_recurring,
                items=items,
                metadata=metadata,
                processing_time=processing_time
            )

            logger.info(
                "Successfully transformed AI result to ReceiptAnalysis",
                extra={
                    "receipt_id": receipt_id,
                    "store_name": receipt_analysis.place,
                    "amount": receipt_analysis.amount,
                    "items_count": len(items),
                    "vendor_type": metadata.vendor_type,
                },
            )

            return receipt_analysis

        except Exception as e:
            logger.error(
                "Failed to transform AI result",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "ai_result_keys": list(ai_result.keys()) if isinstance(ai_result, dict) else "not_dict",
                },
            )
            raise ValueError(f"Failed to transform AI result: {str(e)}")

    def _generate_intelligent_description(
        self, store_info: Dict[str, Any], items: list, classification: Dict[str, Any]
    ) -> str:
        """Generate an intelligent, search-friendly description"""
        
        store_name = store_info.get("name", "Unknown Store")
        vendor_type = classification.get("vendor_type", "OTHER")
        items_count = len(items)
        
        if vendor_type == "RESTAURANT":
            if items_count == 1:
                return f"{items[0].name} from {store_name}"
            else:
                return f"Meal with {items_count} items from {store_name}"
        
        elif vendor_type == "SUPERMARKET":
            # Get unique categories
            categories = list(set(item.category for item in items if item.category))
            if len(categories) <= 3:
                category_text = ", ".join(categories)
                return f"{items_count} items from {store_name} including {category_text}"
            else:
                return f"{items_count} items from {store_name} across multiple categories"
        
        elif vendor_type == "SERVICE":
            if any(item.recurring for item in items):
                return f"Subscription/service payment to {store_name}"
            else:
                return f"Service payment to {store_name}"
        
        else:
            return f"{items_count} items from {store_name}"

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the enhanced service
        """
        try:
            if not self.model:
                return {"status": "unhealthy", "error": "Model not initialized"}

            return {
                "status": "healthy",
                "model": self.model_name,
                "project_id": self.project_id,
                "location": self.location,
                "agent_type": "enhanced_hybrid_agentic",
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Health check failed", extra={"error": str(e)})
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }


# Service instance
_enhanced_agent = None


def get_enhanced_receipt_scanner_agent() -> EnhancedReceiptScannerAgent:
    """Get the singleton enhanced agent instance"""
    global _enhanced_agent
    if _enhanced_agent is None:
        _enhanced_agent = EnhancedReceiptScannerAgent()
    return _enhanced_agent
