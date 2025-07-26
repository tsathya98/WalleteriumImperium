"""
Enhanced Vertex AI service for receipt analysis using Gemini 2.5 Flash
with guaranteed JSON structure output and agentic retry logic
"""

import json
import base64
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from PIL import Image
import io

import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
from google.cloud import aiplatform

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ReceiptAnalysisSchema:
    """JSON Schema definition for guaranteed structured output from Gemini"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """
        Returns the JSON schema that Gemini must follow for receipt analysis
        This ensures consistent, structured output every time
        """
        return {
            "type": "object",
            "required": ["store_info", "items", "totals", "confidence", "processing_metadata"],
            "properties": {
                "store_info": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "description": "Store or merchant name"},
                        "address": {"type": "string", "description": "Store address if visible"},
                        "phone": {"type": "string", "description": "Phone number if visible"},
                        "date": {"type": "string", "description": "Transaction date (YYYY-MM-DD format)"},
                        "time": {"type": "string", "description": "Transaction time (HH:MM format)"},
                        "receipt_number": {"type": "string", "description": "Receipt/transaction number"}
                    }
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "quantity", "unit_price", "total_price"],
                        "properties": {
                            "name": {"type": "string", "description": "Item name"},
                            "quantity": {"type": "number", "minimum": 0, "description": "Item quantity"},
                            "unit_price": {"type": "number", "minimum": 0, "description": "Price per unit"},
                            "total_price": {"type": "number", "minimum": 0, "description": "Total price for this item"},
                            "category": {
                                "type": "string", 
                                "enum": ["food", "beverage", "household", "personal_care", "electronics", "clothing", "pharmacy", "other"],
                                "description": "Item category"
                            },
                            "tax_applied": {"type": "boolean", "description": "Whether tax was applied to this item"}
                        }
                    }
                },
                "totals": {
                    "type": "object",
                    "required": ["total"],
                    "properties": {
                        "subtotal": {"type": "number", "minimum": 0, "description": "Subtotal amount"},
                        "tax": {"type": "number", "minimum": 0, "description": "Tax amount"},
                        "discount": {"type": "number", "minimum": 0, "description": "Discount amount"},
                        "total": {"type": "number", "minimum": 0, "description": "Final total amount"},
                        "payment_method": {
                            "type": "string",
                            "enum": ["cash", "card", "mobile", "other", "unknown"],
                            "description": "Payment method if visible"
                        }
                    }
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Overall confidence level in the extraction accuracy"
                },
                "processing_metadata": {
                    "type": "object",
                    "required": ["timestamp", "model_version"],
                    "properties": {
                        "timestamp": {"type": "string", "description": "Processing timestamp (ISO 8601)"},
                        "model_version": {"type": "string", "description": "Gemini model version used"},
                        "items_count": {"type": "number", "description": "Number of items extracted"},
                        "image_quality": {
                            "type": "string",
                            "enum": ["excellent", "good", "fair", "poor"],
                            "description": "Assessed image quality"
                        },
                        "retry_count": {"type": "number", "minimum": 0, "description": "Number of processing retries"}
                    }
                }
            }
        }


class VertexAIReceiptService:
    """Enhanced Vertex AI service for receipt analysis using Gemini 2.5 Flash"""
    
    def __init__(self):
        """Initialize the Vertex AI service"""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        self.max_retries = 3
        self.model = None
        self._initialize_vertex_ai()
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI and the Gemini model"""
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
                response_schema=ReceiptAnalysisSchema.get_schema()
            )
            
            # Initialize the model with our schema
            self.model = GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )
            
            logger.info("Vertex AI initialized successfully", extra={
                "project_id": self.project_id,
                "location": self.location,
                "model": self.model_name
            })
            
        except Exception as e:
            logger.error("Failed to initialize Vertex AI", extra={"error": str(e)})
            raise
    
    def _create_optimized_prompt(self) -> str:
        """
        Creates an optimized prompt for receipt analysis
        The prompt is designed to work with the JSON schema for maximum accuracy
        """
        return """
You are an expert receipt analysis AI. Analyze this receipt image and extract ALL information accurately.

CRITICAL INSTRUCTIONS:
1. Extract EVERY visible item with exact names, quantities, and prices
2. Calculate totals precisely - they must match the receipt
3. Categorize items using the provided categories
4. For missing information, use appropriate fallback values (see below)
5. Ensure all numbers are positive and realistic
6. Date format: YYYY-MM-DD, Time format: HH:MM

FALLBACK VALUES FOR MISSING INFORMATION:
- address: Use "Not provided" if store address not visible
- phone: Use "Not provided" if phone number not visible  
- date: Use "Unknown" if transaction date not visible
- time: Use "Unknown" if transaction time not visible
- receipt_number: Use "Not provided" if receipt number not visible
- subtotal: Use 0 if subtotal not visible
- tax: Use 0 if tax amount not visible
- discount: Use 0 if no discount applied
- payment_method: Use "unknown" if payment method not visible

QUALITY ASSESSMENT:
- "high" confidence: Text is crisp, all key info clearly visible
- "medium" confidence: Some blur/shadow but most info readable  
- "low" confidence: Poor quality, missing key information

ITEM CATEGORIES:
- food: Fresh produce, packaged food, frozen items
- beverage: Drinks, alcohol, coffee
- household: Cleaning supplies, paper products, home items
- personal_care: Toiletries, cosmetics, health items
- electronics: Tech devices, batteries, cables
- clothing: Apparel, shoes, accessories
- pharmacy: Medications, medical supplies
- other: Items that don't fit other categories

Return ONLY valid JSON matching the required schema. No additional text or formatting.
"""
    
    async def analyze_receipt_image(
        self, 
        image_base64: str, 
        user_id: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Analyze receipt image using Gemini 2.5 Flash with guaranteed JSON output
        
        Args:
            image_base64: Base64 encoded receipt image
            user_id: User ID for logging
            retry_count: Current retry attempt number
            
        Returns:
            Structured receipt analysis data
        """
        try:
            logger.info("Starting receipt analysis", extra={
                "user_id": user_id,
                "retry_count": retry_count,
                "image_size_kb": len(image_base64) * 3 / 4 / 1024
            })
            
            # Validate and prepare image
            image_data = self._prepare_image(image_base64)
            
            # Create the prompt
            prompt = self._create_optimized_prompt()
            
            # Prepare the content for Gemini
            contents = [
                prompt,
                Part.from_data(data=image_data, mime_type="image/jpeg")
            ]
            
            # Generate content with schema enforcement
            response = await asyncio.to_thread(
                self.model.generate_content, 
                contents
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            # Parse the guaranteed JSON response
            analysis_result = json.loads(response.text)
            
            # Add processing metadata
            analysis_result["processing_metadata"].update({
                "timestamp": datetime.utcnow().isoformat(),
                "model_version": self.model_name,
                "items_count": len(analysis_result.get("items", [])),
                "retry_count": retry_count
            })
            
            # Validate the result
            self._validate_analysis_result(analysis_result)
            
            logger.info("Receipt analysis completed successfully", extra={
                "user_id": user_id,
                "items_extracted": len(analysis_result.get("items", [])),
                "total_amount": analysis_result.get("totals", {}).get("total", 0),
                "confidence": analysis_result.get("confidence", "unknown"),
                "retry_count": retry_count
            })
            
            return {
                "status": "success",
                "data": analysis_result,
                "processing_time": None,  # Will be calculated by caller
                "model_version": self.model_name
            }
            
        except json.JSONDecodeError as e:
            logger.error("JSON parsing failed", extra={
                "user_id": user_id,
                "retry_count": retry_count,
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else None
            })
            
            if retry_count < self.max_retries:
                logger.info("Retrying with enhanced prompt", extra={
                    "user_id": user_id,
                    "retry_count": retry_count + 1
                })
                await asyncio.sleep(1)  # Brief delay before retry
                return await self.analyze_receipt_image(image_base64, user_id, retry_count + 1)
            
            raise ValueError(f"Failed to get valid JSON after {self.max_retries} retries")
            
        except Exception as e:
            logger.error("Receipt analysis failed", extra={
                "user_id": user_id,
                "retry_count": retry_count,
                "error": str(e)
            })
            
            if retry_count < self.max_retries and "quota" not in str(e).lower():
                logger.info("Retrying analysis", extra={
                    "user_id": user_id,
                    "retry_count": retry_count + 1
                })
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.analyze_receipt_image(image_base64, user_id, retry_count + 1)
            
            raise
    
    def _prepare_image(self, image_base64: str) -> bytes:
        """
        Prepare and validate the image for analysis
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Image bytes ready for Gemini
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(image_base64)
            
            # Validate and potentially resize image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize if too large (Gemini has size limits)
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                logger.info("Resizing large image", extra={
                    "original_size": image.size,
                    "max_size": max_size
                })
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert back to bytes
                output_buffer = io.BytesIO()
                image.save(output_buffer, format='JPEG', quality=90, optimize=True)
                image_bytes = output_buffer.getvalue()
            
            return image_bytes
            
        except Exception as e:
            logger.error("Image preparation failed", extra={"error": str(e)})
            raise ValueError(f"Invalid image data: {str(e)}")
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """
        Validate the analysis result for consistency and correctness
        
        Args:
            result: Analysis result to validate
        """
        try:
            # Check required fields
            required_fields = ["store_info", "items", "totals", "confidence"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate store info
            if not result["store_info"].get("name"):
                raise ValueError("Store name is required")
            
            # Validate items
            items = result.get("items", [])
            if not isinstance(items, list):
                raise ValueError("Items must be an array")
            
            # Validate totals consistency
            totals = result.get("totals", {})
            calculated_total = sum(item.get("total_price", 0) for item in items)
            declared_total = totals.get("total", 0)
            
            # Allow small rounding differences
            if abs(calculated_total - declared_total) > 0.02:
                logger.warning("Total mismatch detected", extra={
                    "calculated_total": calculated_total,
                    "declared_total": declared_total,
                    "difference": abs(calculated_total - declared_total)
                })
            
            logger.debug("Analysis result validation passed")
            
        except Exception as e:
            logger.error("Analysis result validation failed", extra={"error": str(e)})
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the Vertex AI service
        
        Returns:
            Health status information
        """
        try:
            # Test basic connectivity
            if not self.model:
                return {"status": "unhealthy", "error": "Model not initialized"}
            
            # Test with a simple request (optional)
            return {
                "status": "healthy",
                "model": self.model_name,
                "project_id": self.project_id,
                "location": self.location,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Health check failed", extra={"error": str(e)})
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Service instance
_vertex_ai_service = None

def get_vertex_ai_service() -> VertexAIReceiptService:
    """Get the singleton Vertex AI service instance"""
    global _vertex_ai_service
    if _vertex_ai_service is None:
        _vertex_ai_service = VertexAIReceiptService()
    return _vertex_ai_service