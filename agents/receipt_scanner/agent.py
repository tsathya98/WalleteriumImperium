"""
Simple but Intelligent Receipt Scanner Agent with Google SDK
Implements sophisticated decision-making logic in clean, efficient calls
"""

import datetime
import json
import io
import time
from typing import Dict, Any
from PIL import Image

import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

from app.core.config import get_settings
from app.models import ReceiptAnalysis, ItemDetail, WarrantyDetails, RecurringDetails, ProcessingMetadata
from .prompts import create_agentic_prompt
from .schemas import get_enhanced_receipt_schema
from .validators import validate_and_fix_result

settings = get_settings()


class SimpleReceiptScannerAgent:
    """Simple but Intelligent Receipt Scanner Agent"""

    def __init__(self):
        """Initialize the agent with Google SDK"""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        
        print(f"🤖 Initializing Simple Receipt Scanner Agent")
        print(f"   Project: {self.project_id}")
        print(f"   Location: {self.location}")
        
        self._initialize_model()

    def _initialize_model(self):
        """Initialize Vertex AI with simple, clean setup"""
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            
            # Simple generation config for structured output
            generation_config = GenerationConfig(
                temperature=0.1,  # Low for consistency
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=get_enhanced_receipt_schema()
            )

            # Initialize model
            self.model = GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )
            
            print("✅ Agent ready!")

        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            raise

    def analyze_receipt(self, media_bytes: bytes, media_type: str, user_id: str) -> Dict[str, Any]:
        """
        Simple but intelligent receipt analysis
        
        Args:
            media_bytes: Raw media bytes
            media_type: 'image' or 'video'
            user_id: User identifier
            
        Returns:
            Complete receipt analysis
        """
        start_time = datetime.datetime.utcnow()
        
        print(f"🧠 Analyzing receipt for user: {user_id}")
        print(f"   Type: {media_type}, Size: {len(media_bytes) / 1024:.1f} KB")

        try:
            # Prepare media (simple and direct)
            media_data, mime_type = self._prepare_media(media_bytes, media_type)
            
            # Create intelligent prompt
            prompt = create_agentic_prompt(media_type)
            
            # Single AI call with amazing logic embedded in prompt
            print("🤖 Making intelligent AI call...")
            response = self.model.generate_content([
                prompt,
                Part.from_data(data=media_data, mime_type=mime_type)
            ])

            if not response.text:
                raise ValueError("Empty AI response")

            # Parse guaranteed JSON
            ai_result = json.loads(response.text)
            
            # Validate and enhance (keep sophisticated validation)
            validated_result, validation = validate_and_fix_result(ai_result)
            
            # Transform to final result (simplified but complete)
            receipt_analysis = self._create_receipt_analysis(
                validated_result, user_id, start_time
            )
            
            processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()
            
            print(f"✅ Analysis completed successfully!")
            print(f"   Items: {len(receipt_analysis.items)}")
            print(f"   Amount: ${receipt_analysis.amount}")
            print(f"   Category: {receipt_analysis.category}")
            print(f"   Time: {processing_time:.1f}s")

            return {
                "status": "success",
                "data": receipt_analysis.dict(),
                "processing_time": processing_time,
                "model_version": self.model_name,
                "validation": {
                    "is_valid": validation.is_valid,
                    "errors": validation.errors,
                    "warnings": validation.warnings
                }
            }

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            # Simple retry logic
            if hasattr(self, '_retry_count'):
                self._retry_count += 1
            else:
                self._retry_count = 1
                
            if self._retry_count <= 2:
                print(f"🔄 Retrying... (attempt {self._retry_count})")
                time.sleep(1)
                return self.analyze_receipt(media_bytes, media_type, user_id)
            
            raise

    def _prepare_media(self, media_bytes: bytes, media_type: str) -> tuple[bytes, str]:
        """Simple media preparation"""
        if media_type == "image":
            return self._prepare_image(media_bytes)
        elif media_type == "video":
            return self._prepare_video(media_bytes)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")

    def _prepare_image(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Prepare image (simple but effective)"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize if too large (Gemini limit)
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", quality=90)
                image_bytes = output_buffer.getvalue()

            return image_bytes, "image/jpeg"

        except Exception as e:
            raise ValueError(f"Invalid image: {e}")

    def _prepare_video(self, video_bytes: bytes) -> tuple[bytes, str]:
        """Prepare video (simple validation)"""
        # Check size limit
        size_mb = len(video_bytes) / 1024 / 1024
        if size_mb > 100:
            raise ValueError(f"Video too large: {size_mb:.1f}MB (max: 100MB)")
        
        # Determine MIME type from content
        if video_bytes.startswith(b"\x00\x00\x00"):
            mime_type = "video/mp4"
        elif video_bytes.startswith(b"ftypqt"):
            mime_type = "video/quicktime"
        else:
            mime_type = "video/mp4"  # Default
            
        return video_bytes, mime_type

    def _create_receipt_analysis(
        self, 
        validated_result: Dict[str, Any], 
        user_id: str, 
        start_time: datetime.datetime
    ) -> ReceiptAnalysis:
        """Transform validated AI result to ReceiptAnalysis (simplified but complete)"""
        
        # Generate receipt ID
        timestamp = int(start_time.timestamp())
        receipt_id = f"{user_id}_{timestamp}"
        
        # Extract data from validated structure (works with existing validators)
        store_info = validated_result.get("store_info", {})
        items_data = validated_result.get("items", [])
        totals = validated_result.get("totals", {})
        classification = validated_result.get("classification", {})
        processing_meta = validated_result.get("processing_metadata", {})
        
        # Extract main data (simplified extraction)
        place = store_info.get("name", "Unknown Store")
        amount = float(totals.get("total", 0))
        category = classification.get("overall_category", "Other")
        
        # Process items (keep sophistication for item details)
        items = []
        for item_data in items_data:
            # Handle warranty
            warranty = None
            if item_data.get("warranty"):
                w = item_data["warranty"]
                warranty = WarrantyDetails(
                    validUntil=w.get("validUntil", ""),
                    provider=w.get("provider", "Unknown"),
                    coverage=w.get("coverage", "")
                )

            # Handle recurring
            recurring = None
            if item_data.get("recurring"):
                r = item_data["recurring"]
                recurring = RecurringDetails(
                    frequency=r.get("frequency", "monthly"),
                    nextBillingDate=r.get("nextBillingDate"),
                    subscriptionType=r.get("subscriptionType"),
                    autoRenew=r.get("autoRenew")
                )

            item = ItemDetail(
                name=item_data.get("name", "Unknown Item"),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("unit_price"),
                total_price=item_data.get("total_price", 0),
                category=item_data.get("category", category),  # Fall back to main category
                description=item_data.get("description", ""),
                warranty=warranty,
                recurring=recurring
            )
            items.append(item)

        # Create top-level warranty/recurring summaries (intelligent logic)
        top_warranty = None
        top_recurring = None
        
        # Check for warranties
        warranty_items = [item for item in items if item.warranty]
        if warranty_items:
            latest = max(warranty_items, key=lambda x: x.warranty.validUntil)
            top_warranty = WarrantyDetails(
                validUntil=latest.warranty.validUntil,
                provider="Multiple" if len(warranty_items) > 1 else latest.warranty.provider,
                coverage=f"{len(warranty_items)} items with warranties"
            )

        # Check for subscriptions
        recurring_items = [item for item in items if item.recurring]
        if recurring_items:
            first = recurring_items[0].recurring
            top_recurring = RecurringDetails(
                frequency=first.frequency,
                nextBillingDate=first.nextBillingDate,
                subscriptionType=first.subscriptionType,
                autoRenew=first.autoRenew
            )

        # Create metadata
        processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        metadata = ProcessingMetadata(
            vendor_type=classification.get("vendor_type", "OTHER"),
            confidence=processing_meta.get("confidence", "medium"),
            processing_time_seconds=processing_time,
            model_version=self.model_name
        )

        # Generate intelligent description
        description = self._generate_description(store_info, items, classification)

        # Create final analysis
        return ReceiptAnalysis(
            receipt_id=receipt_id,
            place=place,
            time=store_info.get("date", start_time.strftime("%Y-%m-%d")) + "T" + store_info.get("time", "12:00") + ":00Z",
            amount=amount,
            transactionType="debit",  # Default assumption
            category=category,
            description=description,
            importance="medium",  # Could be enhanced with AI logic
            warranty=top_warranty,
            recurring=top_recurring,
            items=items,
            metadata=metadata,
            processing_time=processing_time
        )

    def _generate_description(self, store_info: Dict[str, Any], items: list, classification: Dict[str, Any]) -> str:
        """Generate intelligent description (simplified)"""
        store_name = store_info.get("name", "Unknown Store")
        vendor_type = classification.get("vendor_type", "OTHER")
        items_count = len(items)
        
        if vendor_type == "RESTAURANT":
            return f"Meal with {items_count} items from {store_name}"
        elif vendor_type == "SUPERMARKET":
            return f"{items_count} items from {store_name}"
        elif vendor_type == "SERVICE":
            return f"Service payment to {store_name}"
        else:
            return f"Transaction at {store_name}"

    def health_check(self) -> Dict[str, Any]:
        """Simple health check"""
        try:
            return {
                "status": "healthy",
                "model": self.model_name,
                "project_id": self.project_id,
                "agent_type": "simple_intelligent",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }


# Service instance (simple singleton pattern)
_agent = None

def get_receipt_scanner_agent() -> SimpleReceiptScannerAgent:
    """Get the agent instance"""
    global _agent
    if _agent is None:
        _agent = SimpleReceiptScannerAgent()
    return _agent
