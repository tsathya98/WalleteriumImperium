"""
Dynamic JSON schemas for the Receipt Scanner Agent
Generates schemas that adapt to our enhanced data structure requirements
"""

from typing import Dict, Any
from config.constants import TRANSACTION_CATEGORIES, VENDOR_TYPES


def get_enhanced_receipt_schema() -> Dict[str, Any]:
    """
    Returns the enhanced JSON schema for receipt analysis with agentic decision-making
    
    Returns:
        JSON schema dictionary for Gemini's response_schema parameter
    """
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
                        "description": "Store address if visible, 'Not provided' otherwise"
                    },
                    "phone": {
                        "type": "string", 
                        "description": "Phone number if visible, 'Not provided' otherwise"
                    },
                    "date": {
                        "type": "string",
                        "description": "Transaction date (YYYY-MM-DD format)"
                    },
                    "time": {
                        "type": "string",
                        "description": "Transaction time (HH:MM format)"
                    },
                    "receipt_number": {
                        "type": "string",
                        "description": "Receipt/transaction number if visible"
                    }
                }
            },
            "items": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["name", "quantity", "total_price", "category"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Item name exactly as shown on receipt"
                        },
                        "quantity": {
                            "type": "number",
                            "minimum": 0,
                            "description": "Item quantity"
                        },
                        "unit_price": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "description": "Price per unit if available"
                        },
                        "total_price": {
                            "type": "number", 
                            "minimum": 0,
                            "description": "Total price for this item"
                        },
                        "category": {
                            "type": "string",
                            "enum": TRANSACTION_CATEGORIES,
                            "description": "Item category from predefined list"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed item description for search/RAG purposes"
                        },
                        "warranty": {
                            "type": ["object", "null"],
                            "properties": {
                                "validUntil": {
                                    "type": "string",
                                    "description": "Warranty expiry date (ISO 8601)"
                                },
                                "provider": {
                                    "type": "string",
                                    "description": "Warranty provider (Manufacturer/Store/etc.)"
                                },
                                "coverage": {
                                    "type": "string",
                                    "description": "Coverage description"
                                }
                            },
                            "required": ["validUntil", "provider"],
                            "description": "Warranty details if item has warranty"
                        },
                        "recurring": {
                            "type": ["object", "null"],
                            "properties": {
                                "frequency": {
                                    "type": "string",
                                    "description": "Billing frequency (monthly, yearly, etc.)"
                                },
                                "nextBillingDate": {
                                    "type": ["string", "null"],
                                    "description": "Next billing date (ISO 8601)"
                                },
                                "subscriptionType": {
                                    "type": ["string", "null"],
                                    "description": "Type of subscription"
                                },
                                "autoRenew": {
                                    "type": ["boolean", "null"],
                                    "description": "Auto-renewal status"
                                }
                            },
                            "required": ["frequency"],
                            "description": "Subscription details if item is recurring"
                        }
                    }
                }
            },
            "totals": {
                "type": "object",
                "required": ["total"],
                "properties": {
                    "subtotal": {
                        "type": ["number", "null"],
                        "minimum": 0,
                        "description": "Subtotal amount"
                    },
                    "tax": {
                        "type": ["number", "null"],
                        "minimum": 0,
                        "description": "Tax amount"
                    },
                    "discount": {
                        "type": ["number", "null"], 
                        "minimum": 0,
                        "description": "Discount amount"
                    },
                    "total": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Final total amount"
                    },
                    "payment_method": {
                        "type": ["string", "null"],
                        "enum": ["cash", "card", "mobile", "other", "unknown", None],
                        "description": "Payment method if visible"
                    }
                }
            },
            "classification": {
                "type": "object",
                "required": ["vendor_type", "overall_category", "reasoning"],
                "properties": {
                    "vendor_type": {
                        "type": "string",
                        "enum": list(VENDOR_TYPES.keys()),
                        "description": "AI-classified vendor type"
                    },
                    "overall_category": {
                        "type": "string",
                        "enum": TRANSACTION_CATEGORIES,
                        "description": "Overall transaction category"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of vendor type classification"
                    },
                    "has_warranties": {
                        "type": "boolean",
                        "description": "True if any items have warranties"
                    },
                    "has_subscriptions": {
                        "type": "boolean", 
                        "description": "True if any items are subscriptions"
                    }
                }
            },
            "processing_metadata": {
                "type": "object",
                "required": ["confidence", "image_quality"],
                "properties": {
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Overall confidence in extraction accuracy"
                    },
                    "image_quality": {
                        "type": "string",
                        "enum": ["excellent", "good", "fair", "poor"],
                        "description": "Assessed image/video quality"
                    },
                    "items_count": {
                        "type": "number",
                        "description": "Number of items extracted"
                    },
                    "extraction_notes": {
                        "type": ["string", "null"],
                        "description": "Any notes about extraction challenges"
                    }
                }
            }
        }
    }

