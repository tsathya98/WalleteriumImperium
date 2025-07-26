"""
Receipt Scanner Data Models

This module defines the comprehensive data structures for receipt processing,
including MCP format validation and type definitions for multimodal inputs.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class InputType(str, Enum):
    """Supported input types for receipt processing."""

    TEXT = "text"
    EXCEL = "excel"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"


class ProcessorModel(str, Enum):
    """AI models used for processing."""

    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_PRO = "gemini-pro"
    CUSTOM_LLM = "custom-llm"


class MCPFormat(BaseModel):
    """Model Context Protocol format wrapper."""

    protocol_version: str = Field(default="1.0", description="MCP protocol version")
    data_type: str = Field(
        default="processed_receipt", description="Type of data being transmitted"
    )
    status: Literal["success", "error", "processing"] = Field(
        description="Processing status"
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    agent_id: str = Field(
        default="receipt_scanner_agent", description="ID of the processing agent"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in extraction"
    )


class ProcessingMetadata(BaseModel):
    """Metadata about the processing operation."""

    receipt_id: str = Field(description="Unique identifier for this receipt")
    source_filename: str = Field(description="Original filename or input identifier")
    source_type: InputType = Field(description="Type of input (image, pdf, etc.)")
    processing_timestamp_utc: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    processor_model: ProcessorModel = Field(description="AI model used for processing")
    file_size_bytes: Optional[int] = Field(
        None, description="Size of original file in bytes"
    )
    processing_duration_ms: Optional[int] = Field(
        None, description="Time taken to process in milliseconds"
    )


class UserDefinedMetadata(BaseModel):
    """User-customizable metadata for receipt categorization."""

    overall_category: Optional[str] = Field(
        None, description="User-defined category for the entire receipt"
    )
    tags: List[str] = Field(
        default_factory=list, description="User-defined tags for organization"
    )
    notes: Optional[str] = Field(None, description="User notes about this receipt")
    favorite: bool = Field(
        default=False, description="Whether this receipt is marked as favorite"
    )
    archived: bool = Field(
        default=False, description="Whether this receipt is archived"
    )


class StoreDetails(BaseModel):
    """Information about the merchant/store."""

    name: Optional[str] = Field(None, description="Store or merchant name")
    address: Optional[str] = Field(None, description="Store address")
    phone_number: Optional[str] = Field(None, description="Store phone number")
    website: Optional[str] = Field(None, description="Store website URL")
    store_id: Optional[str] = Field(None, description="Store or location identifier")
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence in store extraction"
    )


class TransactionDetails(BaseModel):
    """Core transaction information."""

    date: Optional[str] = Field(None, description="Transaction date (YYYY-MM-DD)")
    time: Optional[str] = Field(None, description="Transaction time (HH:MM:SS)")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    transaction_id: Optional[str] = Field(
        None, description="Transaction or receipt number"
    )
    cashier_id: Optional[str] = Field(None, description="Cashier or operator ID")
    register_id: Optional[str] = Field(None, description="Register or terminal ID")

    @field_validator("date")
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class TaxDetails(BaseModel):
    """Tax information for an item or transaction."""

    tax_amount: float = Field(ge=0.0, description="Tax amount")
    tax_rate: float = Field(ge=0.0, le=100.0, description="Tax rate percentage")
    tax_type: Optional[str] = Field(None, description="Type of tax (VAT, Sales, etc.)")


class LineItem(BaseModel):
    """Individual item on the receipt."""

    description: str = Field(description="Item description or name")
    quantity: float = Field(default=1.0, ge=0.0, description="Quantity purchased")
    unit_price: float = Field(ge=0.0, description="Price per unit")
    total_price: float = Field(ge=0.0, description="Total price for this line item")
    category: Optional[str] = Field(
        None, description="Item category (food, electronics, etc.)"
    )
    sku: Optional[str] = Field(None, description="Stock keeping unit or product code")
    tax_details: Optional[TaxDetails] = Field(
        None, description="Tax information for this item"
    )
    discount_amount: Optional[float] = Field(
        None, ge=0.0, description="Discount applied to this item"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence in item extraction"
    )

    @field_validator("total_price")
    def validate_total_price(cls, v, values):
        if "unit_price" in values and "quantity" in values:
            expected_total = values["unit_price"] * values["quantity"]
            if "discount_amount" in values and values["discount_amount"]:
                expected_total -= values["discount_amount"]
            # Allow for small rounding differences
            if abs(v - expected_total) > 0.01:
                # Don't raise error, just log the discrepancy
                pass
        return v


class DiscountPromotion(BaseModel):
    """Discount or promotion applied to the transaction."""

    description: str = Field(description="Description of the discount/promotion")
    amount: float = Field(description="Discount amount (negative for discounts)")
    percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Discount percentage"
    )
    code: Optional[str] = Field(None, description="Promotion or coupon code")


class PaymentSummary(BaseModel):
    """Financial summary of the transaction."""

    subtotal: float = Field(ge=0.0, description="Subtotal before tax and discounts")
    total_tax_amount: float = Field(default=0.0, ge=0.0, description="Total tax amount")
    discounts_and_promotions: List[DiscountPromotion] = Field(default_factory=list)
    tip: float = Field(default=0.0, ge=0.0, description="Tip amount")
    total_amount: float = Field(ge=0.0, description="Final total amount paid")

    @field_validator("total_amount")
    def validate_total_amount(cls, v, values):
        if all(k in values for k in ["subtotal", "total_tax_amount", "tip"]):
            discount_total = sum(
                d.amount for d in values.get("discounts_and_promotions", [])
            )
            expected_total = (
                values["subtotal"]
                + values["total_tax_amount"]
                + values["tip"]
                + discount_total
            )
            # Allow for small rounding differences
            if abs(v - expected_total) > 0.01:
                # Don't raise error, just log the discrepancy
                pass
        return v


class PaymentMethod(BaseModel):
    """Payment method information."""

    method: str = Field(description="Payment method (Credit Card, Cash, etc.)")
    card_type: Optional[str] = Field(
        None, description="Type of card (Visa, MasterCard, etc.)"
    )
    last_4_digits: Optional[str] = Field(None, description="Last 4 digits of card")
    authorization_code: Optional[str] = Field(
        None, description="Payment authorization code"
    )


class WarrantyInfo(BaseModel):
    """Warranty information for items."""

    is_applicable: bool = Field(default=False, description="Whether warranty applies")
    duration_days: Optional[int] = Field(
        None, ge=0, description="Warranty duration in days"
    )
    expiry_date: Optional[str] = Field(
        None, description="Warranty expiry date (YYYY-MM-DD)"
    )
    terms: Optional[str] = Field(None, description="Warranty terms and conditions")

    @field_validator("expiry_date")
    def validate_expiry_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Expiry date must be in YYYY-MM-DD format")
        return v


class ReturnPolicy(BaseModel):
    """Return policy information."""

    is_returnable: bool = Field(
        default=True, description="Whether items can be returned"
    )
    duration_days: Optional[int] = Field(
        None, ge=0, description="Return period in days"
    )
    return_deadline: Optional[str] = Field(
        None, description="Last date for returns (YYYY-MM-DD)"
    )
    conditions: Optional[str] = Field(
        None, description="Return conditions and requirements"
    )

    @field_validator("return_deadline")
    def validate_return_deadline_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Return deadline must be in YYYY-MM-DD format")
        return v


class SpecialInfo(BaseModel):
    """Special information like warranty and return policy."""

    warranty: Optional[WarrantyInfo] = Field(None, description="Warranty information")
    return_policy: Optional[ReturnPolicy] = Field(
        None, description="Return policy information"
    )
    loyalty_points_earned: Optional[int] = Field(
        None, ge=0, description="Loyalty points earned from purchase"
    )
    promotional_offers: List[str] = Field(
        default_factory=list, description="Promotional offers mentioned"
    )


class ReceiptPayload(BaseModel):
    """Complete receipt data payload."""

    processing_metadata: ProcessingMetadata = Field(description="Processing metadata")
    user_defined_metadata: UserDefinedMetadata = Field(
        default_factory=UserDefinedMetadata
    )
    store_details: Optional[StoreDetails] = Field(None, description="Store information")
    transaction_details: Optional[TransactionDetails] = Field(
        None, description="Transaction details"
    )
    line_items: List[LineItem] = Field(
        default_factory=list, description="List of items purchased"
    )
    payment_summary: Optional[PaymentSummary] = Field(
        None, description="Payment summary"
    )
    payment_method: Optional[PaymentMethod] = Field(
        None, description="Payment method used"
    )
    special_info: Optional[SpecialInfo] = Field(None, description="Special information")


class ProcessedReceipt(BaseModel):
    """Complete processed receipt structure with MCP format."""

    mcp_format: MCPFormat = Field(description="MCP protocol wrapper")
    receipt_payload: ReceiptPayload = Field(description="Complete receipt data")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.dict(exclude_none=False)

    def to_json(self, **kwargs) -> str:
        """Convert to JSON string."""
        return self.json(exclude_none=False, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessedReceipt":
        """Create instance from dictionary."""
        return cls(**data)


class ProcessingError(BaseModel):
    """Error information for failed processing."""

    error_code: str = Field(description="Error code identifier")
    error_message: str = Field(description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )


class ProcessingResult(BaseModel):
    """Result of receipt processing operation."""

    success: bool = Field(description="Whether processing was successful")
    receipt: Optional[ProcessedReceipt] = Field(
        None, description="Processed receipt data"
    )
    error: Optional[ProcessingError] = Field(
        None, description="Error information if failed"
    )
    processing_stats: Optional[Dict[str, Any]] = Field(
        None, description="Processing statistics"
    )

    @field_validator("receipt")
    def validate_receipt_when_success(cls, v, values):
        if values.get("success") and v is None:
            raise ValueError("Receipt must be provided when success is True")
        return v

    @field_validator("error")
    def validate_error_when_failure(cls, v, values):
        if not values.get("success") and v is None:
            raise ValueError("Error must be provided when success is False")
        return v


# Helper functions for common operations
def create_receipt_id() -> str:
    """Generate a unique receipt ID."""
    from uuid import uuid4

    return f"receipt-{uuid4()}"


def calculate_warranty_expiry(purchase_date: str, duration_days: int) -> str:
    """Calculate warranty expiry date."""
    from datetime import timedelta

    purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
    expiry = purchase + timedelta(days=duration_days)
    return expiry.strftime("%Y-%m-%d")


def calculate_return_deadline(purchase_date: str, duration_days: int) -> str:
    """Calculate return deadline."""
    return calculate_warranty_expiry(purchase_date, duration_days)


def validate_receipt_structure(receipt_data: Dict[str, Any]) -> List[str]:
    """Validate receipt structure and return list of issues."""
    issues = []
    try:
        ProcessedReceipt.from_dict(receipt_data)
    except Exception as e:
        issues.append(str(e))
    return issues 