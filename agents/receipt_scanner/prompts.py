"""
Prompts for the ADK-based Receipt Scanner Agent.
Contains prompts that generate a rich, structured JSON output.
"""

from typing import List
from config.constants import TRANSACTION_CATEGORIES, VENDOR_TYPES


def create_structured_receipt_prompt(media_type: str) -> str:
    """
    Creates a comprehensive prompt for receipt extraction, guiding the AI
    to produce a detailed, structured JSON output based on the ProcessedReceipt model.

    Args:
        media_type: Type of media ('image' or 'video').

    Returns:
        A sophisticated prompt for Gemini, tailored for receipt analysis.
    """
    media_instruction = "receipt image" if media_type == "image" else "receipt video"

    # A high-quality, one-shot example to guide the model's output format.
    one_shot_example = """
**Example Input:** A clear image of a restaurant receipt.
**Example Output:**
```json
{
    "mcp_format": {
        "protocol_version": "1.0",
        "data_type": "processed_receipt",
        "status": "success",
        "timestamp_utc": "2025-07-27T18:30:00Z",
        "agent_id": "receipt_scanner_agent",
        "confidence_score": 0.95
    },
    "receipt_payload": {
        "processing_metadata": {
            "receipt_id": "receipt-b4b1b3b1",
            "source_filename": "example_receipt.jpg",
            "source_type": "IMAGE",
            "processing_timestamp_utc": "2025-07-27T18:30:00Z",
            "processor_model": "gemini-2.5-flash"
        },
        "store_details": {
            "name": "The Corner Bistro",
            "address": "123 Main St, Anytown, USA 12345",
            "phone_number": "555-123-4567",
            "confidence_score": 0.98
        },
        "transaction_details": {
            "date": "2025-07-27",
            "time": "18:15:00",
            "currency": "USD",
            "transaction_id": "TXN-58392"
        },
        "line_items": [
            {
                "description": "Grilled Salmon",
                "quantity": 1.0,
                "unit_price": 25.00,
                "total_price": 25.00,
                "category": "Restaurant, fast-food",
                "confidence_score": 0.97
            },
            {
                "description": "House Salad",
                "quantity": 2.0,
                "unit_price": 8.00,
                "total_price": 16.00,
                "category": "Restaurant, fast-food",
                "confidence_score": 0.96
            }
        ],
        "payment_summary": {
            "subtotal": 41.00,
            "total_tax_amount": 3.28,
            "tip": 8.00,
            "total_amount": 52.28
        },
        "payment_method": {
            "method": "Credit Card",
            "card_type": "Visa",
            "last_4_digits": "1234"
        },
        "special_info": null
    }
}
```
"""

    return f"""
Analyze this {media_instruction} and extract ALL visible information.
Your response MUST be a single, valid JSON object and nothing else. Do not add any text before or after the JSON.

{one_shot_example}

**Your Task:**
Now, analyze the provided receipt and generate the JSON output in the exact same format as the example above.

**CRITICAL INSTRUCTIONS:**

1.  **JSON ONLY:** Your entire output must be the JSON object. No explanations, no apologies, no markdown `json` tags.
2.  **Strict Schema:** Adhere strictly to the JSON structure from the example.
3.  **Categorization:** Use one of these categories for each item: {', '.join(TRANSACTION_CATEGORIES)}
4.  **Accuracy:** Ensure all numbers are correct and calculations are accurate.
5.  **Completeness:** If a field is not on the receipt, use `null`. Do not omit any fields from the schema.
""" 