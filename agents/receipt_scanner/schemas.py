"""
Dynamic JSON schemas for the Receipt Scanner Agent
Generates schemas that adapt to our enhanced data structure requirements
"""

from typing import Dict, Any
from .models import ProcessedReceipt


def get_enhanced_receipt_schema() -> Dict[str, Any]:
    """
    Returns the enhanced JSON schema dynamically generated from the ProcessedReceipt model.
    
    Returns:
        JSON schema dictionary for Gemini's response_schema parameter
    """
    
    print("📋 Creating dynamic schema from ProcessedReceipt model")
    
    # Generate the schema directly from the Pydantic model
    schema = ProcessedReceipt.model_json_schema()
    
    # The Pydantic-generated schema is already in the correct format
    # for Gemini, so we can return it directly.
    return schema


def get_validation_schema() -> Dict[str, Any]:
    """
    Returns a simplified schema for validation purposes
    """
    return get_enhanced_receipt_schema()  # Use same schema for now

