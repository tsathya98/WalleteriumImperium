"""
Tools for Receipt Scanner

This module contains utility functions and external integrations used
throughout the receipt processing system.
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime


def generate_receipt_id() -> str:
    """Generate a unique receipt ID."""
    return f"receipt-{uuid.uuid4().hex[:8]}"


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    if currency.upper() == "USD":
        return f"${amount:.2f}"
    return f"{amount:.2f} {currency}"


def validate_receipt_data(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate receipt data structure and completeness."""
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    required_fields = ["receipt_id", "store_details", "transaction_details", "line_items"]
    
    for field in required_fields:
        if field not in receipt_data:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Missing required field: {field}")
    
    return validation_result


def calculate_confidence_score(scores: list) -> float:
    """Calculate overall confidence score from individual scores."""
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


__all__ = [
    "generate_receipt_id",
    "format_currency", 
    "validate_receipt_data",
    "calculate_confidence_score",
] 