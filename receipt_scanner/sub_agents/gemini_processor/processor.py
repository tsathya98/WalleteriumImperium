"""
Gemini 2.5 Flash Integration for Receipt Processing

This module provides integration with Google's Gemini 2.5 Flash model for
processing images and videos to extract receipt information using vision AI.
"""

import os
import json
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import io
from PIL import Image

try:
    import google.generativeai as genai

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from ...models import (
    ProcessedReceipt,
    MCPFormat,
    ReceiptPayload,
    ProcessingMetadata,
    UserDefinedMetadata,
    StoreDetails,
    TransactionDetails,
    LineItem,
    PaymentSummary,
    PaymentMethod,
    SpecialInfo,
    WarrantyInfo,
    ReturnPolicy,
    TaxDetails,
    DiscountPromotion,
    ProcessorModel,
    InputType,
    calculate_warranty_expiry,
    calculate_return_deadline,
)


class GeminiVisionProcessor:
    """Processor for images and videos using Gemini 2.5 Flash."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini processor."""
        if not HAS_GEMINI:
            raise ImportError("google-generativeai library not installed")

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def process_image(
        self, image_data: Union[str, bytes], filename: str, metadata: ProcessingMetadata
    ) -> ProcessedReceipt:
        """Process a single image and extract receipt information."""
        try:
            # Prepare image for Gemini
            if isinstance(image_data, str):
                # Base64 string
                image_bytes = base64.b64decode(image_data)
            else:
                # Raw bytes
                image_bytes = image_data

            # Create PIL Image for Gemini
            image = Image.open(io.BytesIO(image_bytes))

            # Generate content with structured prompt
            prompt = self._create_receipt_extraction_prompt()

            start_time = datetime.now()
            response = self.model.generate_content([prompt, image])
            end_time = datetime.now()

            # Update processing duration
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            metadata.processing_duration_ms = duration_ms
            metadata.processor_model = ProcessorModel.GEMINI_2_5_FLASH

            if not response.text:
                return self._create_error_response(
                    metadata, "No response from Gemini Vision API"
                )

            # Parse the JSON response
            receipt_data = self._parse_gemini_response(response.text)

            # Create structured receipt
            processed_receipt = self._create_processed_receipt(receipt_data, metadata)

            return processed_receipt

        except Exception as e:
            return self._create_error_response(
                metadata, f"Image processing failed: {str(e)}"
            )

    async def process_video(
        self, frames: List[Dict[str, Any]], filename: str, metadata: ProcessingMetadata
    ) -> ProcessedReceipt:
        """Process video frames and extract receipt information."""
        try:
            if not frames:
                return self._create_error_response(
                    metadata, "No frames extracted from video"
                )

            # Process the best frame or combine information from multiple frames
            best_result = None
            highest_confidence = 0.0

            for i, frame_data in enumerate(frames[:3]):  # Process up to 3 frames
                try:
                    frame_base64 = frame_data.get("frame_base64", "")
                    if not frame_base64:
                        continue

                    # Create frame-specific metadata
                    frame_metadata = ProcessingMetadata(
                        receipt_id=metadata.receipt_id,
                        source_filename=f"{filename}_frame_{frame_data.get('frame_number', i)}",
                        source_type=InputType.VIDEO,
                        processor_model=ProcessorModel.GEMINI_2_5_FLASH,
                    )

                    # Process this frame
                    frame_result = await self.process_image(
                        frame_base64, frame_metadata.source_filename, frame_metadata
                    )

                    # Check if this frame has better results
                    frame_confidence = frame_result.mcp_format.confidence_score
                    if frame_confidence > highest_confidence:
                        highest_confidence = frame_confidence
                        best_result = frame_result
                        best_result.receipt_payload.processing_metadata = metadata

                except Exception:
                    continue  # Skip problematic frames

            if best_result:
                # Update metadata to reflect video processing
                best_result.receipt_payload.processing_metadata.source_filename = (
                    filename
                )
                best_result.receipt_payload.processing_metadata.source_type = (
                    InputType.VIDEO
                )
                return best_result
            else:
                return self._create_error_response(
                    metadata,
                    "Could not extract receipt information from any video frame",
                )

        except Exception as e:
            return self._create_error_response(
                metadata, f"Video processing failed: {str(e)}"
            )

    def _create_receipt_extraction_prompt(self) -> str:
        """Create a comprehensive prompt for receipt extraction."""
        return """
Analyze this receipt image and extract ALL visible information in the following exact JSON format.
Be extremely thorough and accurate. If information is not visible, use null.

Extract information for this JSON structure:

{
    "store_info": {
        "name": "exact store name as shown",
        "address": "complete address if visible",
        "phone_number": "phone number if visible",
        "website": "website URL if visible",
        "store_id": "store/location ID if visible",
        "confidence_score": 0.0-1.0
    },
    "transaction_details": {
        "date": "YYYY-MM-DD format",
        "time": "HH:MM:SS format",
        "currency": "currency code (USD, EUR, etc.)",
        "transaction_id": "receipt/transaction number",
        "cashier_id": "cashier ID if visible",
        "register_id": "register/terminal ID if visible"
    },
    "line_items": [
        {
            "description": "exact item description",
            "quantity": 1.0,
            "unit_price": 0.00,
            "total_price": 0.00,
            "category": "inferred category (food, electronics, clothing, etc.)",
            "sku": "product code/SKU if visible",
            "tax_details": {
                "tax_amount": 0.00,
                "tax_rate": 0.0,
                "tax_type": "VAT/Sales/etc"
            },
            "discount_amount": 0.00,
            "confidence_score": 0.0-1.0
        }
    ],
    "payment_summary": {
        "subtotal": 0.00,
        "total_tax_amount": 0.00,
        "discounts_and_promotions": [
            {
                "description": "discount description",
                "amount": -0.00,
                "percentage": 0.0,
                "code": "promo code if any"
            }
        ],
        "tip": 0.00,
        "total_amount": 0.00
    },
    "payment_method": {
        "method": "Credit Card/Cash/Debit/etc",
        "card_type": "Visa/MasterCard/etc",
        "last_4_digits": "1234",
        "authorization_code": "auth code if visible"
    },
    "special_info": {
        "warranty": {
            "is_applicable": false,
            "duration_days": null,
            "terms": "warranty terms if mentioned"
        },
        "return_policy": {
            "is_returnable": true,
            "duration_days": null,
            "conditions": "return conditions if mentioned"
        },
        "loyalty_points_earned": null,
        "promotional_offers": []
    },
    "extraction_metadata": {
        "confidence_level": "high/medium/low",
        "image_quality": "excellent/good/fair/poor",
        "text_clarity": "clear/readable/difficult/unclear",
        "completeness": "complete/partial/minimal"
    }
}

CRITICAL INSTRUCTIONS:
1. Extract ALL visible items with exact descriptions and prices
2. Categorize items logically (food, beverage, household, electronics, clothing, etc.)
3. Calculate totals accurately - ensure line items sum to subtotal
4. If quantity is not shown, assume 1
5. Convert all prices to numbers (remove currency symbols)
6. Provide confidence scores based on text clarity and visibility
7. For categories, infer from item names (e.g., "Milk" = "food", "T-shirt" = "clothing")
8. Extract ALL tax information visible
9. Identify any discounts, promotions, or special offers
10. Look for warranty information, return policies, or loyalty program details

Return ONLY the JSON object, no additional text or formatting.
"""

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini's JSON response."""
        try:
            # Clean the response text
            response_text = response_text.strip()

            # Remove markdown formatting if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON
            receipt_data = json.loads(response_text)

            # Validate required fields
            if not isinstance(receipt_data, dict):
                raise ValueError("Response is not a valid JSON object")

            return receipt_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing response: {str(e)}")

    def _create_processed_receipt(
        self, receipt_data: Dict[str, Any], metadata: ProcessingMetadata
    ) -> ProcessedReceipt:
        """Create a ProcessedReceipt from extracted data."""
        try:
            # Extract confidence and quality metrics
            extraction_meta = receipt_data.get("extraction_metadata", {})
            confidence_level = extraction_meta.get("confidence_level", "medium")

            # Map confidence level to score
            confidence_map = {"high": 0.95, "medium": 0.75, "low": 0.50}
            confidence_score = confidence_map.get(confidence_level, 0.75)

            # Create store details
            store_info = receipt_data.get("store_info", {})
            store_details = None
            if any(store_info.values()):
                store_details = StoreDetails(
                    name=store_info.get("name"),
                    address=store_info.get("address"),
                    phone_number=store_info.get("phone_number"),
                    website=store_info.get("website"),
                    store_id=store_info.get("store_id"),
                    confidence_score=store_info.get(
                        "confidence_score", confidence_score
                    ),
                )

            # Create transaction details
            trans_info = receipt_data.get("transaction_details", {})
            transaction_details = None
            if any(trans_info.values()):
                transaction_details = TransactionDetails(
                    date=trans_info.get("date"),
                    time=trans_info.get("time"),
                    currency=trans_info.get("currency", "USD"),
                    transaction_id=trans_info.get("transaction_id"),
                    cashier_id=trans_info.get("cashier_id"),
                    register_id=trans_info.get("register_id"),
                )

            # Create line items
            line_items = []
            items_data = receipt_data.get("line_items", [])
            for item_data in items_data:
                if not item_data.get("description"):
                    continue

                # Create tax details if present
                tax_details = None
                tax_info = item_data.get("tax_details")
                if tax_info and isinstance(tax_info, dict):
                    tax_details = TaxDetails(
                        tax_amount=tax_info.get("tax_amount", 0.0),
                        tax_rate=tax_info.get("tax_rate", 0.0),
                        tax_type=tax_info.get("tax_type"),
                    )

                line_item = LineItem(
                    description=item_data["description"],
                    quantity=item_data.get("quantity", 1.0),
                    unit_price=item_data.get("unit_price", 0.0),
                    total_price=item_data.get("total_price", 0.0),
                    category=item_data.get("category"),
                    sku=item_data.get("sku"),
                    tax_details=tax_details,
                    discount_amount=item_data.get("discount_amount"),
                    confidence_score=item_data.get(
                        "confidence_score", confidence_score
                    ),
                )
                line_items.append(line_item)

            # Create payment summary
            payment_info = receipt_data.get("payment_summary", {})
            payment_summary = None
            if any(payment_info.values()):
                # Create discounts and promotions
                discounts = []
                discounts_data = payment_info.get("discounts_and_promotions", [])
                for discount_data in discounts_data:
                    if isinstance(discount_data, dict) and discount_data.get(
                        "description"
                    ):
                        discount = DiscountPromotion(
                            description=discount_data["description"],
                            amount=discount_data.get("amount", 0.0),
                            percentage=discount_data.get("percentage"),
                            code=discount_data.get("code"),
                        )
                        discounts.append(discount)

                payment_summary = PaymentSummary(
                    subtotal=payment_info.get("subtotal", 0.0),
                    total_tax_amount=payment_info.get("total_tax_amount", 0.0),
                    discounts_and_promotions=discounts,
                    tip=payment_info.get("tip", 0.0),
                    total_amount=payment_info.get("total_amount", 0.0),
                )

            # Create payment method
            pay_method_info = receipt_data.get("payment_method", {})
            payment_method = None
            if pay_method_info.get("method"):
                payment_method = PaymentMethod(
                    method=pay_method_info["method"],
                    card_type=pay_method_info.get("card_type"),
                    last_4_digits=pay_method_info.get("last_4_digits"),
                    authorization_code=pay_method_info.get("authorization_code"),
                )

            # Create special info
            special_data = receipt_data.get("special_info", {})
            special_info = None
            if any(special_data.values()):
                # Create warranty info
                warranty = None
                warranty_data = special_data.get("warranty", {})
                if isinstance(warranty_data, dict) and warranty_data:
                    warranty = WarrantyInfo(
                        is_applicable=warranty_data.get("is_applicable", False),
                        duration_days=warranty_data.get("duration_days"),
                        expiry_date=None,  # Will be calculated if needed
                        terms=warranty_data.get("terms"),
                    )

                    # Calculate expiry date if we have purchase date and duration
                    if (
                        warranty.is_applicable
                        and warranty.duration_days
                        and transaction_details
                        and transaction_details.date
                    ):
                        try:
                            warranty.expiry_date = calculate_warranty_expiry(
                                transaction_details.date, warranty.duration_days
                            )
                        except Exception:
                            pass  # Keep expiry_date as None if calculation fails

                # Create return policy
                return_policy = None
                return_data = special_data.get("return_policy", {})
                if isinstance(return_data, dict) and return_data:
                    return_policy = ReturnPolicy(
                        is_returnable=return_data.get("is_returnable", True),
                        duration_days=return_data.get("duration_days"),
                        return_deadline=None,  # Will be calculated if needed
                        conditions=return_data.get("conditions"),
                    )

                    # Calculate return deadline if we have purchase date and duration
                    if (
                        return_policy.duration_days
                        and transaction_details
                        and transaction_details.date
                    ):
                        try:
                            return_policy.return_deadline = calculate_return_deadline(
                                transaction_details.date, return_policy.duration_days
                            )
                        except Exception:
                            pass  # Keep return_deadline as None if calculation fails

                special_info = SpecialInfo(
                    warranty=warranty,
                    return_policy=return_policy,
                    loyalty_points_earned=special_data.get("loyalty_points_earned"),
                    promotional_offers=special_data.get("promotional_offers", []),
                )

            # Create MCP format
            mcp_format = MCPFormat(status="success", confidence_score=confidence_score)

            # Create receipt payload
            receipt_payload = ReceiptPayload(
                processing_metadata=metadata,
                user_defined_metadata=UserDefinedMetadata(),
                store_details=store_details,
                transaction_details=transaction_details,
                line_items=line_items,
                payment_summary=payment_summary,
                payment_method=payment_method,
                special_info=special_info,
            )

            return ProcessedReceipt(
                mcp_format=mcp_format, receipt_payload=receipt_payload
            )

        except Exception as e:
            return self._create_error_response(
                metadata, f"Failed to create structured receipt: {str(e)}"
            )

    def _create_error_response(
        self, metadata: ProcessingMetadata, error_message: str
    ) -> ProcessedReceipt:
        """Create an error response with proper structure."""
        mcp_format = MCPFormat(status="error", confidence_score=0.0)

        # Create minimal receipt payload for error case
        receipt_payload = ReceiptPayload(
            processing_metadata=metadata,
            user_defined_metadata=UserDefinedMetadata(
                notes=f"Processing error: {error_message}"
            ),
        )

        return ProcessedReceipt(mcp_format=mcp_format, receipt_payload=receipt_payload)


# Utility functions
def create_gemini_processor(api_key: Optional[str] = None) -> GeminiVisionProcessor:
    """Create a configured Gemini Vision processor."""
    return GeminiVisionProcessor(api_key)


def validate_gemini_setup() -> Dict[str, Any]:
    """Validate Gemini setup and return status."""
    result = {
        "library_available": HAS_GEMINI,
        "api_key_set": bool(os.getenv("GOOGLE_API_KEY")),
        "ready": False,
        "errors": [],
    }

    if not result["library_available"]:
        result["errors"].append("google-generativeai library not installed")

    if not result["api_key_set"]:
        result["errors"].append("GOOGLE_API_KEY environment variable not set")

    result["ready"] = result["library_available"] and result["api_key_set"]

    return result


async def test_gemini_connection(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connection to Gemini API."""
    try:
        processor = create_gemini_processor(api_key)

        # Create a simple test image (1x1 white pixel)
        from PIL import Image

        test_image = Image.new("RGB", (1, 1), color="white")
        buffer = io.BytesIO()
        test_image.save(buffer, format="PNG")
        test_image_bytes = buffer.getvalue()

        # Try a simple request
        response = processor.model.generate_content(
            ["Describe this image briefly.", Image.open(io.BytesIO(test_image_bytes))]
        )

        return {
            "success": True,
            "message": "Connection successful",
            "response_received": bool(response.text),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
