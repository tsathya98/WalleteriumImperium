"""
Enhanced Receipt Scanner Agent with Hybrid Agentic Workflow
Implements sophisticated decision-making logic in a single, efficient call
"""

import datetime
import json
import io
from typing import Dict, Any
import time
from PIL import Image

import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

from app.core.config import get_settings

from app.models import ReceiptAnalysis, ItemDetail, WarrantyDetails, RecurringDetails, ProcessingMetadata
from .prompts import create_agentic_prompt, create_fallback_values_prompt, create_business_rules_prompt
from .schemas import get_enhanced_receipt_schema
from .validators import validate_and_fix_result

settings = get_settings()


class EnhancedReceiptScannerAgent:
    """Enhanced Receipt Scanner Agent with Hybrid Agentic Workflow"""

    def __init__(self):
        """Initialize the enhanced agent"""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        self.max_retries = 3
        self.model = None
        print(f"🤖 Initializing Enhanced Receipt Scanner Agent")
        print(f"   Project: {self.project_id}")
        print(f"   Location: {self.location}")
        self._initialize_vertex_ai()

    def _initialize_vertex_ai(self):
        """Initialize Vertex AI and the Gemini model with enhanced schema"""
        try:
            print("🔧 Starting Vertex AI initialization")
            
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            print("✅ Vertex AI initialized successfully")

            # Get the schema and debug it
            schema = get_enhanced_receipt_schema()
            print(f"📋 Schema generated successfully, keys: {list(schema.keys())}")
            
            # Configure generation settings for structured output
            print("⚙️ Creating GenerationConfig")
            generation_config = GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent output
                top_p=0.8,
                top_k=40,
                candidate_count=1,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=schema,
            )
            print("✅ GenerationConfig created successfully")

            # Initialize the model with enhanced schema
            print(f"🚀 Initializing {self.model_name} model")
            self.model = GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )
            print("✅ Model initialized successfully")

            print(f"🎉 Enhanced Receipt Scanner Agent ready!")

        except Exception as e:
            print(f"❌ Failed to initialize Vertex AI: {e}")
            raise

    def analyze_receipt_media(
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
        print(f"DEBUG: Starting analyze_receipt_media - media_type: {media_type!r} (type: {type(media_type)})")
        print(f"DEBUG: user_id: {user_id!r}, retry_count: {retry_count}")
        
        try:
            start_time = datetime.datetime.utcnow()
            
            print(f"🧠 Starting enhanced receipt analysis for user: {user_id}")
            print(f"   Media type: {media_type}")
            print(f"   Media size: {len(media_bytes) / 1024:.1f} KB")
            print(f"   Retry count: {retry_count}")

            # Validate and prepare media from raw bytes
            print(f"DEBUG: About to check media_type: {media_type}")
            if media_type == "image":
                print("DEBUG: Processing as image")
                media_data, mime_type = self._prepare_image_from_bytes(media_bytes)
            elif media_type == "video":
                print("DEBUG: Processing as video")
                media_data, mime_type = self._prepare_video_from_bytes(media_bytes)
            else:
                print(f"DEBUG: Unsupported media_type: {media_type}")
                raise ValueError(f"Unsupported media type: {media_type}")

            print("DEBUG: Media prepared successfully")

            # Create the enhanced agentic prompt
            prompt = self._create_enhanced_prompt(media_type)

            # Prepare the content for Gemini
            contents = [prompt, Part.from_data(data=media_data, mime_type=mime_type)]

            # Generate content with schema enforcement
            print("🤖 Calling Gemini model...")
            response = self.model.generate_content(contents)

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

            print(f"✅ Enha nced receipt analysis completed successfully")
            print(f"   Items extracted: {len(receipt_analysis.items)}")
            print(f"   Total amount: ${receipt_analysis.amount}")
            print(f"   Vendor type: {receipt_analysis.metadata.vendor_type if receipt_analysis.metadata else 'unknown'}")
            print(f"   Confidence: {receipt_analysis.metadata.confidence if receipt_analysis.metadata else 'unknown'}")
            print(f"   Processing time: {processing_time:.1f}s")
            print(f"   Validation errors: {len(validation.errors)}")
            print(f"   Validation warnings: {len(validation.warnings)}")

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
            print(f"❌ JSON parsing failed in enhanced analysis")
            print(f"   User: {user_id}, Retry: {retry_count}")
            print(f"   Error: {e}")
            print(f"   Raw response: {response.text[:500] if 'response' in locals() else 'No response'}")
            raise ValueError(f"Invalid JSON response from AI: {str(e)}")

        except Exception as e:
            print(f"❌ Enhanced receipt analysis failed")
            print(f"   User: {user_id}, Retry: {retry_count}")
            print(f"   Error: {e}")

            # Simple retry logic for hackathon speed
            if retry_count < 2:
                print(f"🔄 Retrying... (attempt {retry_count + 1})")
                time.sleep(2**retry_count)  # Exponential backoff
                return self.analyze_receipt_media(
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
                print(f"📏 Resizing large image from {image.size} to max {max_size}")
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Convert back to bytes
                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", quality=90, optimize=True)
                image_bytes = output_buffer.getvalue()

            return image_bytes, "image/jpeg"

        except Exception as e:
            print(f"❌ Image preparation failed: {e}")
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
                print(f"⚠️ Video too large: {video_size_mb:.1f}MB (max: {max_video_size}MB)")
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

            print(f"🎥 Video prepared for analysis")
            print(f"   Size: {video_size_mb:.1f}MB")
            print(f"   MIME type: {mime_type}")

            return video_bytes, mime_type

        except Exception as e:
            print(f"❌ Video preparation failed: {e}")
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
            # Extract data from AI result (SAME LOGIC AS BEFORE)
            store_info = ai_result.get("store_info", {})
            items_data = ai_result.get("items", [])
            totals = ai_result.get("totals", {})
            classification = ai_result.get("classification", {})
            processing_meta = ai_result.get("processing_metadata", {})

            # Generate receipt ID
            timestamp = int(start_time.timestamp())
            receipt_id = f"{user_id}_{timestamp}"

            # Process time
            processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()

            # Format time string
            time_str = start_time.isoformat() + "Z"

            # Transform items (SAME LOGIC)
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

            # Determine top-level warranty and recurring summaries (SAME LOGIC)
            top_level_warranty = None
            top_level_recurring = None

            # Check if any items have warranties
            warranty_items = [item for item in items if item.warranty]
            if warranty_items:
                # Create a summary warranty
                latest_warranty = max(warranty_items, key=lambda x: x.warranty.validUntil)
                top_level_warranty = WarrantyDetails(
                    validUntil=latest_warranty.warranty.validUntil,
                    provider="Multiple" if len(warranty_items) > 1 else latest_warranty.warranty.provider,
                    coverage=f"{len(warranty_items)} items with warranties"
                )

            # Check if any items have recurring payments
            recurring_items = [item for item in items if item.recurring]
            if recurring_items:
                # Use the first recurring item as template
                first_recurring = recurring_items[0].recurring
                top_level_recurring = RecurringDetails(
                    frequency=first_recurring.frequency,
                    nextBillingDate=first_recurring.nextBillingDate,
                    subscriptionType=first_recurring.subscriptionType,
                    autoRenew=first_recurring.autoRenew
                )

            # Create processing metadata
            metadata = ProcessingMetadata(
                vendor_type=classification.get("vendor_type", "OTHER"),
                confidence=processing_meta.get("confidence", "medium"),
                processing_time_seconds=processing_time,
                model_version=self.model_name
            )

            # Generate intelligent description (SAME LOGIC)
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

            print(f"✅ Successfully transformed AI result to ReceiptAnalysis")
            print(f"   Receipt ID: {receipt_id}")
            print(f"   Store Name: {receipt_analysis.place}")
            print(f"   Amount: ${receipt_analysis.amount}")
            print(f"   Items Count: {len(items)}")
            print(f"   Vendor Type: {metadata.vendor_type}")

            return receipt_analysis

        except Exception as e:
            print(f"❌ Failed to transform AI result")
            print(f"   User: {user_id}")
            print(f"   Error: {e}")
            print(f"   AI Result Keys: {list(ai_result.keys()) if isinstance(ai_result, dict) else 'not_dict'}")
            raise ValueError(f"Failed to transform AI result: {str(e)}")

    def _generate_intelligent_description(
        self, store_info: Dict[str, Any], items: list, classification: Dict[str, Any]
    ) -> str:
        """Generate an intelligent, search-friendly description (SAME LOGIC)"""
        
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

    def health_check(self) -> Dict[str, Any]:
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
                "agent_type": "enhanced_hybrid_agentic_sync",
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"❌ Health check failed: {e}")
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
