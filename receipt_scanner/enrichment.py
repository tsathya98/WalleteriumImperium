"""
LLM-based Data Enrichment for Receipt Processing

This module provides LLM-powered enrichment for receipt data extracted from
non-image sources (PDF, Excel, text) to add categories, confidence scores,
and structured information that matches the robust receipt format.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import google.generativeai as genai

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from .models import (
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
    calculate_warranty_expiry,
    calculate_return_deadline,
)


class LLMDataEnricher:
    """LLM-powered data enrichment for non-image receipt sources."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro"):
        """Initialize LLM enricher."""
        if not HAS_GEMINI:
            raise ImportError("google-generativeai library not installed")

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

    async def enrich_text_data(
        self,
        raw_text: str,
        extracted_info: Dict[str, Any],
        metadata: ProcessingMetadata,
    ) -> ProcessedReceipt:
        """Enrich text-based receipt data using LLM analysis."""
        try:
            prompt = self._create_text_enrichment_prompt(raw_text, extracted_info)

            start_time = datetime.now()
            response = self.model.generate_content(prompt)
            end_time = datetime.now()

            # Update processing metadata
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            metadata.processing_duration_ms = duration_ms
            metadata.processor_model = ProcessorModel.CUSTOM_LLM

            if not response.text:
                return self._create_error_response(
                    metadata, "No response from LLM enrichment"
                )

            # Parse and structure the response
            enriched_data = self._parse_llm_response(response.text)

            # Create structured receipt
            processed_receipt = self._create_enriched_receipt(enriched_data, metadata)

            return processed_receipt

        except Exception as e:
            return self._create_error_response(
                metadata, f"Text enrichment failed: {str(e)}"
            )

    async def enrich_excel_data(
        self, excel_info: Dict[str, Any], metadata: ProcessingMetadata
    ) -> ProcessedReceipt:
        """Enrich Excel-based receipt data using LLM analysis."""
        try:
            prompt = self._create_excel_enrichment_prompt(excel_info)

            start_time = datetime.now()
            response = self.model.generate_content(prompt)
            end_time = datetime.now()

            # Update processing metadata
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            metadata.processing_duration_ms = duration_ms
            metadata.processor_model = ProcessorModel.CUSTOM_LLM

            if not response.text:
                return self._create_error_response(
                    metadata, "No response from LLM enrichment"
                )

            # Parse and structure the response
            enriched_data = self._parse_llm_response(response.text)

            # Create structured receipt
            processed_receipt = self._create_enriched_receipt(enriched_data, metadata)

            return processed_receipt

        except Exception as e:
            return self._create_error_response(
                metadata, f"Excel enrichment failed: {str(e)}"
            )

    async def enrich_pdf_data(
        self,
        pdf_text: str,
        extracted_info: Dict[str, Any],
        metadata: ProcessingMetadata,
    ) -> ProcessedReceipt:
        """Enrich PDF-based receipt data using LLM analysis."""
        try:
            prompt = self._create_pdf_enrichment_prompt(pdf_text, extracted_info)

            start_time = datetime.now()
            response = self.model.generate_content(prompt)
            end_time = datetime.now()

            # Update processing metadata
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            metadata.processing_duration_ms = duration_ms
            metadata.processor_model = ProcessorModel.CUSTOM_LLM

            if not response.text:
                return self._create_error_response(
                    metadata, "No response from LLM enrichment"
                )

            # Parse and structure the response
            enriched_data = self._parse_llm_response(response.text)

            # Create structured receipt
            processed_receipt = self._create_enriched_receipt(enriched_data, metadata)

            return processed_receipt

        except Exception as e:
            return self._create_error_response(
                metadata, f"PDF enrichment failed: {str(e)}"
            )

    def _create_text_enrichment_prompt(
        self, raw_text: str, extracted_info: Dict[str, Any]
    ) -> str:
        """Create prompt for enriching text-based receipt data."""
        return f"""
Analyze the following receipt text and extracted information to create a comprehensive receipt structure.
The text may be from OCR, manual entry, or text file. Enrich the data with categories, confidence scores, and missing information.

RAW TEXT:
{raw_text}

EXTRACTED INFORMATION:
{json.dumps(extracted_info, indent=2)}

Your task is to analyze this information and return a comprehensive JSON structure with the following requirements:

1. **Item Categorization**: Categorize each item into logical categories:
   - food (groceries, prepared food, snacks)
   - beverage (drinks, alcohol, coffee)
   - household (cleaning supplies, toiletries, home goods)
   - electronics (devices, accessories, batteries)
   - clothing (apparel, shoes, accessories)
   - health (pharmacy, medical, supplements)
   - automotive (car parts, gas, maintenance)
   - entertainment (books, games, movies)
   - office (supplies, stationery, software)
   - other (miscellaneous items)

2. **Confidence Scoring**: Assign confidence scores (0.0-1.0) based on:
   - Text clarity and completeness
   - Logical consistency of prices and items
   - Presence of required receipt elements

3. **Data Completion**: Fill in missing information where possible:
   - Infer store type from items purchased
   - Estimate tax rates if not provided
   - Calculate missing totals if possible

Return the following JSON structure:

{
    "store_info": {
        "name": "store name or inferred from context",
        "address": "address if available",
        "phone_number": "phone if available",
        "website": null,
        "store_id": null,
        "confidence_score": 0.0-1.0
    },
    "transaction_details": {
        "date": "YYYY-MM-DD format if available",
        "time": "HH:MM:SS format if available",
        "currency": "USD or inferred currency",
        "transaction_id": "transaction ID if available",
        "cashier_id": null,
        "register_id": null
    },
    "line_items": [
        {
            "description": "item description",
            "quantity": 1.0,
            "unit_price": 0.00,
            "total_price": 0.00,
            "category": "one of the categories above",
            "sku": null,
            "tax_details": {
                "tax_amount": 0.00,
                "tax_rate": 0.0,
                "tax_type": "Sales"
            },
            "discount_amount": null,
            "confidence_score": 0.0-1.0
        }
    ],
    "payment_summary": {
        "subtotal": 0.00,
        "total_tax_amount": 0.00,
        "discounts_and_promotions": [],
        "tip": 0.00,
        "total_amount": 0.00
    },
    "payment_method": {
        "method": "inferred or unknown",
        "card_type": null,
        "last_4_digits": null,
        "authorization_code": null
    },
    "special_info": {
        "warranty": {
            "is_applicable": false,
            "duration_days": null,
            "terms": null
        },
        "return_policy": {
            "is_returnable": true,
            "duration_days": 30,
            "conditions": null
        },
        "loyalty_points_earned": null,
        "promotional_offers": []
    },
    "enrichment_metadata": {
        "confidence_level": "high/medium/low",
        "data_completeness": "complete/partial/minimal",
        "enrichment_method": "text_llm_analysis",
        "issues_detected": []
    }
}

IMPORTANT:
- Be conservative with confidence scores for text-based input
- If prices don't add up correctly, note this in issues_detected
- Categorize items based on their names and common usage
- Use standard assumptions (e.g., 30-day return policy) when information is missing
- Return ONLY the JSON object, no additional text

"""

    def _create_excel_enrichment_prompt(self, excel_info: Dict[str, Any]) -> str:
        """Create prompt for enriching Excel-based receipt data."""
        return f"""
Analyze the following Excel/CSV data to create a comprehensive receipt structure.
The data may contain items, prices, and other receipt information in structured format.

EXCEL DATA INFORMATION:
{json.dumps(excel_info, indent=2)}

Your task is to transform this structured data into a comprehensive receipt format with enrichment:

1. **Item Analysis**:
   - Identify columns that represent items, prices, quantities
   - Categorize items into logical categories
   - Detect any patterns in the data structure

2. **Data Validation**:
   - Check mathematical accuracy of totals
   - Identify missing or inconsistent data
   - Validate data types and formats

3. **Enrichment**:
   - Add categories for each item
   - Calculate confidence scores based on data quality
   - Infer missing receipt elements

Return the same JSON structure as requested for text enrichment, but with:
- Higher confidence scores due to structured data
- Better mathematical validation
- More accurate categorization based on clear item descriptions

Categories to use:
food, beverage, household, electronics, clothing, health, automotive, entertainment, office, other

Mark enrichment_method as "excel_llm_analysis" and provide higher confidence scores (0.7-0.95) since Excel data is typically more structured and accurate.

Return ONLY the JSON object, no additional text.
"""

    def _create_pdf_enrichment_prompt(
        self, pdf_text: str, extracted_info: Dict[str, Any]
    ) -> str:
        """Create prompt for enriching PDF-based receipt data."""
        return f"""
Analyze the following PDF text and extracted information to create a comprehensive receipt structure.
PDF text extraction may have formatting issues, OCR errors, or partial content.

PDF TEXT CONTENT:
{pdf_text[:2000]}...  # Truncated for prompt efficiency

EXTRACTED INFORMATION:
{json.dumps(extracted_info, indent=2)}

Your task is to clean, structure, and enrich this PDF-extracted receipt data:

1. **Text Cleaning**:
   - Correct obvious OCR errors (e.g., "0" vs "O", "5" vs "S")
   - Handle formatting issues from PDF extraction
   - Identify and separate different sections of the receipt

2. **Data Extraction**:
   - Find itemized purchases with prices
   - Locate store information, dates, totals
   - Identify tax information and payment details

3. **Enrichment & Categorization**:
   - Categorize items appropriately
   - Add confidence scores (moderate, since PDF can have OCR issues)
   - Fill in missing standard information

Return the same JSON structure as text enrichment, but:
- Mark enrichment_method as "pdf_llm_analysis"
- Use moderate confidence scores (0.6-0.85) due to potential OCR issues
- Include any detected OCR or formatting issues in issues_detected array

Categories: food, beverage, household, electronics, clothing, health, automotive, entertainment, office, other

Return ONLY the JSON object, no additional text.
"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate LLM enrichment response."""
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
            enriched_data = json.loads(response_text)

            # Validate structure
            if not isinstance(enriched_data, dict):
                raise ValueError("Response is not a valid JSON object")

            return enriched_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing response: {str(e)}")

    def _create_enriched_receipt(
        self, enriched_data: Dict[str, Any], metadata: ProcessingMetadata
    ) -> ProcessedReceipt:
        """Create a ProcessedReceipt from enriched LLM data."""
        try:
            # Extract enrichment metadata
            enrichment_meta = enriched_data.get("enrichment_metadata", {})
            confidence_level = enrichment_meta.get("confidence_level", "medium")

            # Map confidence level to score (slightly lower for non-vision processing)
            confidence_map = {"high": 0.85, "medium": 0.65, "low": 0.40}
            confidence_score = confidence_map.get(confidence_level, 0.65)

            # Create store details
            store_info = enriched_data.get("store_info", {})
            store_details = None
            if any(v for v in store_info.values() if v is not None):
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
            trans_info = enriched_data.get("transaction_details", {})
            transaction_details = None
            if any(v for v in trans_info.values() if v is not None):
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
            items_data = enriched_data.get("line_items", [])
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
                        tax_type=tax_info.get("tax_type", "Sales"),
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
            payment_info = enriched_data.get("payment_summary", {})
            payment_summary = None
            if any(v for v in payment_info.values() if v not in [None, [], 0]):
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
            pay_method_info = enriched_data.get("payment_method", {})
            payment_method = None
            if pay_method_info.get("method"):
                payment_method = PaymentMethod(
                    method=pay_method_info["method"],
                    card_type=pay_method_info.get("card_type"),
                    last_4_digits=pay_method_info.get("last_4_digits"),
                    authorization_code=pay_method_info.get("authorization_code"),
                )

            # Create special info
            special_data = enriched_data.get("special_info", {})
            special_info = None
            if any(v for v in special_data.values() if v not in [None, [], {}]):
                # Create warranty info
                warranty = None
                warranty_data = special_data.get("warranty", {})
                if isinstance(warranty_data, dict) and warranty_data:
                    warranty = WarrantyInfo(
                        is_applicable=warranty_data.get("is_applicable", False),
                        duration_days=warranty_data.get("duration_days"),
                        expiry_date=None,
                        terms=warranty_data.get("terms"),
                    )

                    # Calculate expiry date if possible
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
                            pass

                # Create return policy
                return_policy = None
                return_data = special_data.get("return_policy", {})
                if isinstance(return_data, dict) and return_data:
                    return_policy = ReturnPolicy(
                        is_returnable=return_data.get("is_returnable", True),
                        duration_days=return_data.get("duration_days"),
                        return_deadline=None,
                        conditions=return_data.get("conditions"),
                    )

                    # Calculate return deadline if possible
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
                            pass

                special_info = SpecialInfo(
                    warranty=warranty,
                    return_policy=return_policy,
                    loyalty_points_earned=special_data.get("loyalty_points_earned"),
                    promotional_offers=special_data.get("promotional_offers", []),
                )

            # Create MCP format
            mcp_format = MCPFormat(status="success", confidence_score=confidence_score)

            # Add enrichment information to user metadata
            user_metadata = UserDefinedMetadata()
            if enrichment_meta:
                notes_parts = []
                if enrichment_meta.get("data_completeness"):
                    notes_parts.append(
                        f"Completeness: {enrichment_meta['data_completeness']}"
                    )
                if enrichment_meta.get("issues_detected"):
                    notes_parts.append(
                        f"Issues: {', '.join(enrichment_meta['issues_detected'])}"
                    )
                if notes_parts:
                    user_metadata.notes = "LLM Enrichment - " + "; ".join(notes_parts)

            # Create receipt payload
            receipt_payload = ReceiptPayload(
                processing_metadata=metadata,
                user_defined_metadata=user_metadata,
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
                metadata, f"Failed to create enriched receipt: {str(e)}"
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
                notes=f"Enrichment error: {error_message}"
            ),
        )

        return ProcessedReceipt(mcp_format=mcp_format, receipt_payload=receipt_payload)


# Utility functions
def create_llm_enricher(
    api_key: Optional[str] = None, model: str = "gemini-1.5-pro"
) -> LLMDataEnricher:
    """Create a configured LLM data enricher."""
    return LLMDataEnricher(api_key, model)


def validate_enrichment_setup() -> Dict[str, Any]:
    """Validate LLM enrichment setup."""
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
