"""
Dynamic JSON schemas for the Receipt Scanner Agent
Generates schemas that adapt to our enhanced data structure requirements
"""

from typing import Dict, Any


def get_enhanced_receipt_schema() -> Dict[str, Any]:
    """
    Returns the enhanced JSON schema for receipt analysis matching the ReceiptAnalysis model
    
    Returns:
        JSON schema dictionary for Gemini's response_schema parameter
    """
    
    print("📋 Creating simplified schema to match ReceiptAnalysis model")
    
    return {
        "type": "object",
        "required": [
            "receipt_id",
            "place", 
            "time",
            "amount",
            "transactionType",
            "category",
            "description",
            "importance",
            "warranty",
            "recurring",
            "items",
            "metadata"
        ],
        "properties": {
            "receipt_id": {
                "type": "string",
                "description": "Unique receipt identifier"
            },
            "place": {
                "type": "string",
                "description": "Store or merchant name"
            },
            "time": {
                "type": "string",
                "description": "Transaction timestamp in ISO format"
            },
            "amount": {
                "type": "number",
                "description": "Total transaction amount"
            },
            "transactionType": {
                "type": "string",
                "enum": ["debit", "credit"],
                "description": "Transaction type"
            },
            "category": {
                "type": "string",
                "enum": ["Restaurant", "Groceries", "Electronics", "Pharmacy", "Clothing", "Gas", "Other"],
                "description": "Overall transaction category"
            },
            "description": {
                "type": "string",
                "description": "Brief description of the transaction"
            },
            "importance": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Transaction importance level"
            },
            "warranty": {
                "type": ["object", "null"],
                "description": "Warranty information if applicable"
            },
            "recurring": {
                "type": ["object", "null"],
                "description": "Recurring payment information if applicable"
            },
            "items": {
                "type": "array",
                "description": "List of items from receipt",
                "items": {
                    "type": "object",
                    "required": ["name", "quantity", "total_price", "category"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Item name"
                        },
                        "quantity": {
                            "type": "number",
                            "description": "Item quantity"
                        },
                        "unit_price": {
                            "type": ["number", "null"],
                            "description": "Price per unit"
                        },
                        "total_price": {
                            "type": "number",
                            "description": "Total price for this item"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["Restaurant", "Groceries", "Electronics", "Pharmacy", "Clothing", "Gas", "Other"],
                            "description": "Item category"
                        },
                        "description": {
                            "type": "string",
                            "description": "Item description"
                        },
                        "warranty": {
                            "type": ["object", "null"],
                            "description": "Item warranty if applicable"
                        },
                        "recurring": {
                            "type": ["object", "null"],
                            "description": "Item recurring info if applicable"
                        }
                    }
                }
            },
            "metadata": {
                "type": "object",
                "required": ["vendor_type", "confidence"],
                "properties": {
                    "vendor_type": {
                        "type": "string",
                        "enum": ["RESTAURANT", "SUPERMARKET", "SERVICE", "OTHER"],
                        "description": "Type of vendor"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Analysis confidence level"
                    },
                    "processing_time_seconds": {
                        "type": "number",
                        "description": "Processing time"
                    },
                    "model_version": {
                        "type": "string",
                        "description": "AI model version used"
                    }
                }
            }
        }
    }


def get_validation_schema() -> Dict[str, Any]:
    """
    Returns a simplified schema for validation purposes
    """
    return get_enhanced_receipt_schema()  # Use same schema for now

