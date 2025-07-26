"""
Prompts for the ADK-based Receipt Scanner Agent.
Contains prompts that generate a rich, structured JSON output.
"""

from config.constants import TRANSACTION_CATEGORIES


def create_simplified_prompt(media_type: str) -> str:
    """
    Creates a simplified, powerful prompt that guides the LLM to produce a clean
    JSON output matching the structure in the README.md.

    Args:
        media_type: Type of media ('image' or 'video').

    Returns:
        A direct and effective prompt for Gemini.
    """
    media_instruction = "receipt image" if media_type == "image" else "receipt video"

    one_shot_example = """
**Example Output:**
```json
{
    "receipt_id": "d2116b7d-2edb-46f6-b2ee-9f2b0ba8c270",
    "place": "El Chalan Restaurant",
    "time": "2016-03-12T13:13:00Z",
    "amount": 49.52,
    "transactionType": "debit",
    "category": "Restaurant, fast-food",
    "description": "Peruvian dinner for 2 including appetizers, main courses, and beverages at El Chalan Restaurant",
    "items": [
        {
            "name": "Ceviche",
            "quantity": 1,
            "unit_price": 15.00,
            "total_price": 15.00,
            "category": "Restaurant, fast-food",
            "description": "Fresh fish ceviche with onions"
        },
        {
            "name": "Lomo Saltado",
            "quantity": 1,
            "unit_price": 25.00,
            "total_price": 25.00,
            "category": "Restaurant, fast-food",
            "description": "Beef stir-fry with potatoes"
        }
    ],
    "metadata": {
        "vendor_type": "RESTAURANT",
        "confidence": "high",
        "processing_time_seconds": 12.5,
        "model_version": "gemini-2.5-flash"
    }
}
```
"""

    return f"""
Analyze this {media_instruction} and extract all visible information.
Your response MUST be a single, valid JSON object matching the example format. Do not add any text before or after the JSON.

{one_shot_example}

**Your Task:**
Now, analyze the provided receipt and generate the JSON output in the exact same format as the example.

**CRITICAL INSTRUCTIONS:**

1.  **JSON ONLY:** Your entire output must be the JSON object.
2.  **Strict Schema:** Adhere strictly to the JSON structure from the example.
3.  **Transaction Type:** The `transactionType` field MUST be either "debit" or "credit". If not specified on the receipt, default to "debit".
4.  **Categorization:** Use one of these categories: {', '.join(TRANSACTION_CATEGORIES)}
5.  **Accuracy:** Ensure all numbers are correct. `amount` must be the final total.
6.  **Completeness:** If a field is not on the receipt, use `null` or a sensible default.
"""
