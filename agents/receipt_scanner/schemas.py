"""
Dynamic JSON schemas for the Receipt Scanner Agent
Generates schemas that adapt to our enhanced data structure requirements
"""

from typing import Dict, Any
from config.constants import TRANSACTION_CATEGORIES


def get_enhanced_receipt_schema() -> Dict[str, Any]:
    """
    Returns the enhanced JSON schema that works with existing validators
    
    Returns:
        JSON schema dictionary for Gemini's response_schema parameter
    """
    
    print("📋 Creating schema to work with existing validation system")
    
    return {
        "type": "object",
        "required": [
            "store_info",
            "items", 
            "totals",
            "classification",
            "processing_metadata"
        ],
        "properties": {
            "store_info": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Store or merchant name"
                    },
                    "address": {
                        "type": "string",
                        "description": "Store address (use 'Not provided' if not visible)"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Store phone number (use 'Not provided' if not visible)"
                    },
                    "date": {
                        "type": "string",
                        "description": "Transaction date (YYYY-MM-DD format)"
                    },
                    "time": {
                        "type": "string",
                        "description": "Transaction time (HH:MM format)"
                    }
                }
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
                            "enum": TRANSACTION_CATEGORIES,
                            "description": "Item category"
                        },
                        "description": {
                            "type": "string",
                            "description": "Item description"
                        },
                        "warranty": {
                            "type": ["object", "null"],
                            "properties": {
                                "validUntil": {"type": "string"},
                                "provider": {"type": "string"},
                                "coverage": {"type": "string"}
                            },
                            "description": "Item warranty if applicable"
                        },
                        "recurring": {
                            "type": ["object", "null"],
                            "properties": {
                                "frequency": {"type": "string"},
                                "nextBillingDate": {"type": "string"},
                                "subscriptionType": {"type": "string"},
                                "autoRenew": {"type": "boolean"}
                            },
                            "description": "Item recurring info if applicable"
                        }
                    }
                }
            },
            "totals": {
                "type": "object",
                "required": ["total"],
                "properties": {
                    "subtotal": {
                        "type": "number",
                        "description": "Subtotal amount"
                    },
                    "tax": {
                        "type": "number",
                        "description": "Tax amount"
                    },
                    "discount": {
                        "type": "number",
                        "description": "Discount amount"
                    },
                    "total": {
                        "type": "number",
                        "description": "Total transaction amount"
                    }
                }
            },
            "classification": {
                "type": "object",
                "required": ["vendor_type", "overall_category"],
                "properties": {
                    "vendor_type": {
                        "type": "string",
                        "enum": ["RESTAURANT", "SUPERMARKET", "SERVICE", "OTHER"],
                        "description": "Type of vendor"
                    },
                    "overall_category": {
                        "type": "string",
                        "enum": TRANSACTION_CATEGORIES,
                        "description": "Overall transaction category"
                    },
                    "has_warranties": {
                        "type": "boolean",
                        "description": "Whether any items have warranties"
                    },
                    "has_subscriptions": {
                        "type": "boolean",
                        "description": "Whether any items are subscriptions"
                    }
                }
            },
            "processing_metadata": {
                "type": "object",
                "required": ["confidence"],
                "properties": {
                    "confidence": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Analysis confidence level"
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

