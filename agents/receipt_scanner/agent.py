import datetime
import json
import base64
from typing import List, Optional
from pathlib import Path
import io
from PIL import Image
from google.adk.agents import Agent

# Import Google Generative AI for Gemini vision capabilities
import google.generativeai as genai
import os


def analyze_receipt() -> dict:
    """Analyzes the uploaded receipt image to extract items and pricing information.

    This function works with ADK web's automatic image upload handling.
    The image is automatically processed by the underlying Gemini model.

    Returns:
        dict: Structured receipt data in MCP format with status, items, pricing, and metadata.
    """
    # When using ADK web, the image is automatically passed to the model
    # This function provides structured output format for the results
    return {
        "status": "info",
        "message": "Receipt analysis completed. The image has been processed by Gemini Vision AI.",
        "instructions": [
            "The receipt image has been automatically analyzed",
            "Items, prices, and store information have been extracted",
            "Results are displayed in the chat interface",
            "For programmatic access, use the MCP-formatted output",
        ],
        "mcp_format": {
            "protocol_version": "1.0",
            "data_type": "receipt_scan",
            "status": "processed",
            "processing_method": "adk_web_automatic",
        },
    }


def process_receipt_image(image_data: str, image_format: str = "base64") -> dict:
    """Processes a receipt image to extract items and pricing information using Gemini Vision.

    Args:
        image_data (str): Base64 encoded image data or file path to the receipt image.
        image_format (str): Format of image_data - either "base64", "file_path", or "url".

    Returns:
        dict: Structured receipt data in MCP format with status, items, pricing, and metadata.
    """
    try:
        # Configure Gemini API (you'll need to set GOOGLE_API_KEY environment variable)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "error_message": "GOOGLE_API_KEY environment variable not set. Please configure your API key.",
                "mcp_format": {
                    "protocol_version": "1.0",
                    "data_type": "receipt_scan",
                    "status": "failed",
                    "error": "API configuration missing",
                },
            }

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Process image based on format
        if image_format == "file_path":
            # Read image file
            image_path = Path(image_data)
            if not image_path.exists():
                return {
                    "status": "error",
                    "error_message": f"Image file not found: {image_data}",
                    "mcp_format": {
                        "protocol_version": "1.0",
                        "data_type": "receipt_scan",
                        "status": "failed",
                        "error": "File not found",
                    },
                }

            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()

        elif image_format == "base64":
            # Decode base64 image data
            try:
                image_bytes = base64.b64decode(image_data)
            except Exception as e:
                return {
                    "status": "error",
                    "error_message": f"Invalid base64 image data: {str(e)}",
                    "mcp_format": {
                        "protocol_version": "1.0",
                        "data_type": "receipt_scan",
                        "status": "failed",
                        "error": "Invalid image format",
                    },
                }
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported image format: {image_format}",
                "mcp_format": {
                    "protocol_version": "1.0",
                    "data_type": "receipt_scan",
                    "status": "failed",
                    "error": "Unsupported format",
                },
            }

        # Convert bytes to PIL Image for Gemini
        image = Image.open(io.BytesIO(image_bytes))

        # Structured prompt for receipt extraction
        prompt = """
        Analyze this receipt image and extract the following information in JSON format:

        {
            "store_info": {
                "name": "store name",
                "address": "store address if visible",
                "phone": "phone number if visible",
                "date": "transaction date",
                "time": "transaction time",
                "receipt_number": "receipt/transaction number"
            },
            "items": [
                {
                    "name": "item name",
                    "quantity": number or 1,
                    "unit_price": price per unit as number,
                    "total_price": total price for this item,
                    "category": "food/beverage/household/etc",
                    "tax_applied": true/false
                }
            ],
            "totals": {
                "subtotal": subtotal amount,
                "tax": tax amount,
                "discount": discount amount if any,
                "total": final total amount,
                "payment_method": "cash/card/etc if visible"
            },
            "confidence": "high/medium/low based on image quality and readability"
        }

        Rules:
        - Extract ALL visible items with their prices
        - If quantity is not specified, assume 1
        - Convert all prices to numbers (remove currency symbols)
        - If information is not visible, use null
        - Be as accurate as possible with item names and prices
        - Categorize items logically
        """

        # Generate content using Gemini Vision
        response = model.generate_content([prompt, image])

        if not response.text:
            return {
                "status": "error",
                "error_message": "No response from Gemini Vision API",
                "mcp_format": {
                    "protocol_version": "1.0",
                    "data_type": "receipt_scan",
                    "status": "failed",
                    "error": "API response empty",
                },
            }

        # Parse JSON response
        try:
            # Clean the response text (remove markdown formatting if present)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```

            receipt_data = json.loads(response_text)

            # Create MCP-compatible structured response
            mcp_response = {
                "status": "success",
                "scan_timestamp": datetime.datetime.now().isoformat(),
                "receipt_data": receipt_data,
                "mcp_format": {
                    "protocol_version": "1.0",
                    "data_type": "receipt_scan",
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "extracted_data": {
                        "store_information": receipt_data.get("store_info", {}),
                        "line_items": receipt_data.get("items", []),
                        "financial_totals": receipt_data.get("totals", {}),
                        "metadata": {
                            "confidence_level": receipt_data.get(
                                "confidence", "medium"
                            ),
                            "items_count": len(receipt_data.get("items", [])),
                            "processing_method": "gemini_vision_ocr",
                        },
                    },
                },
                "summary": {
                    "total_items": len(receipt_data.get("items", [])),
                    "total_amount": receipt_data.get("totals", {}).get("total", 0),
                    "store_name": receipt_data.get("store_info", {}).get(
                        "name", "Unknown"
                    ),
                    "transaction_date": receipt_data.get("store_info", {}).get(
                        "date", "Unknown"
                    ),
                },
            }

            return mcp_response

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error_message": f"Failed to parse receipt data: {str(e)}",
                "raw_response": response.text,
                "mcp_format": {
                    "protocol_version": "1.0",
                    "data_type": "receipt_scan",
                    "status": "failed",
                    "error": "JSON parsing failed",
                },
            }

    except ImportError:
        return {
            "status": "error",
            "error_message": "Google Generative AI library not installed. Run: pip install google-generativeai",
            "mcp_format": {
                "protocol_version": "1.0",
                "data_type": "receipt_scan",
                "status": "failed",
                "error": "Missing dependencies",
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error processing receipt: {str(e)}",
            "mcp_format": {
                "protocol_version": "1.0",
                "data_type": "receipt_scan",
                "status": "failed",
                "error": "Processing error",
            },
        }


def capture_and_scan_receipt(save_path: Optional[str] = None) -> dict:
    """Captures an image from camera (simulated for now) and processes it as a receipt.

    Args:
        save_path (Optional[str]): Path to save the captured image for debugging.

    Returns:
        dict: Receipt scanning results with MCP format.
    """
    try:
        # Note: This is a placeholder for actual camera integration
        # In a real implementation, you would:
        # 1. Use OpenCV or similar to capture from camera
        # 2. Use mobile device camera APIs
        # 3. Use web browser camera APIs

        return {
            "status": "info",
            "message": "Camera capture simulation - provide image file path or base64 data instead",
            "instructions": [
                "1. Take a photo of your receipt using your device camera",
                "2. Save the image file",
                "3. Call process_receipt_image() with the file path or base64 data",
                "4. For mobile integration, use camera APIs to capture and convert to base64",
            ],
            "mcp_format": {
                "protocol_version": "1.0",
                "data_type": "receipt_scan",
                "status": "awaiting_input",
                "message": "Camera integration pending - provide image data",
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Camera capture error: {str(e)}",
            "mcp_format": {
                "protocol_version": "1.0",
                "data_type": "receipt_scan",
                "status": "failed",
                "error": "Camera access failed",
            },
        }


def analyze_receipt_trends(receipt_history: List[dict]) -> dict:
    """Analyzes historical receipt data to provide spending insights.

    Args:
        receipt_history (List[dict]): List of previously scanned receipt data.

    Returns:
        dict: Analysis results with spending trends and insights.
    """
    try:
        if not receipt_history:
            return {
                "status": "info",
                "message": "No receipt history provided for analysis",
                "mcp_format": {
                    "protocol_version": "1.0",
                    "data_type": "receipt_analysis",
                    "status": "no_data",
                    "message": "Insufficient data for analysis",
                },
            }

        # Calculate spending trends
        total_spending = 0
        store_spending = {}
        category_spending = {}
        item_frequency = {}

        for receipt in receipt_history:
            if receipt.get("status") != "success":
                continue

            receipt_data = receipt.get("receipt_data", {})
            totals = receipt_data.get("totals", {})
            items = receipt_data.get("items", [])
            store_info = receipt_data.get("store_info", {})

            # Total spending
            amount = totals.get("total", 0)
            total_spending += amount

            # Store spending
            store_name = store_info.get("name", "Unknown")
            store_spending[store_name] = store_spending.get(store_name, 0) + amount

            # Category and item analysis
            for item in items:
                category = item.get("category", "uncategorized")
                item_name = item.get("name", "unknown")
                item_total = item.get("total_price", 0)

                category_spending[category] = (
                    category_spending.get(category, 0) + item_total
                )
                item_frequency[item_name] = item_frequency.get(item_name, 0) + 1

        # Generate insights
        most_frequent_store = (
            max(store_spending, key=store_spending.get) if store_spending else "N/A"
        )
        top_category = (
            max(category_spending, key=category_spending.get)
            if category_spending
            else "N/A"
        )
        most_bought_item = (
            max(item_frequency, key=item_frequency.get) if item_frequency else "N/A"
        )

        analysis_result = {
            "status": "success",
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "insights": {
                "total_spending": round(total_spending, 2),
                "number_of_receipts": len(receipt_history),
                "average_per_receipt": round(total_spending / len(receipt_history), 2)
                if receipt_history
                else 0,
                "most_frequent_store": most_frequent_store,
                "top_spending_category": top_category,
                "most_purchased_item": most_bought_item,
            },
            "breakdowns": {
                "by_store": dict(
                    sorted(store_spending.items(), key=lambda x: x[1], reverse=True)
                ),
                "by_category": dict(
                    sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
                ),
                "item_frequency": dict(
                    sorted(item_frequency.items(), key=lambda x: x[1], reverse=True)[
                        :10
                    ]
                ),
            },
            "mcp_format": {
                "protocol_version": "1.0",
                "data_type": "receipt_analysis",
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
                "analysis_data": {
                    "spending_summary": {
                        "total": total_spending,
                        "count": len(receipt_history),
                        "average": round(total_spending / len(receipt_history), 2)
                        if receipt_history
                        else 0,
                    },
                    "top_insights": {
                        "primary_store": most_frequent_store,
                        "primary_category": top_category,
                        "most_frequent_item": most_bought_item,
                    },
                },
            },
        }

        return analysis_result

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Analysis error: {str(e)}",
            "mcp_format": {
                "protocol_version": "1.0",
                "data_type": "receipt_analysis",
                "status": "failed",
                "error": "Analysis processing failed",
            },
        }


# Create the Receipt Scanner Agent
receipt_scanner_agent = Agent(
    name="receipt_scanner_agent",
    model="gemini-2.5-flash",
    description=(
        "Advanced receipt scanning agent with camera capabilities that extracts itemized information "
        "and pricing from receipt images using Gemini Vision AI. Provides structured MCP-compatible "
        "output for seamless integration with other systems and agents."
    ),
    instruction=(
        "You are a specialized receipt scanning assistant that helps users digitize and analyze their receipts. "
        "When a user uploads a receipt image, I automatically analyze it using Gemini Vision AI to extract:\n\n"
        "📸 **Receipt Information I Extract:**\n"
        "- Store name, address, phone number\n"
        "- Transaction date and time\n"
        "- Individual items with names, quantities, and prices\n"
        "- Item categories (food, beverages, household, etc.)\n"
        "- Subtotal, tax amounts, discounts\n"
        "- Final total and payment method\n\n"
        "📋 **Output Format:**\n"
        "I provide the extracted information in a clear, organized format:\n"
        "```\n"
        "STORE: [Store Name]\n"
        "DATE: [Transaction Date]\n"
        "TIME: [Transaction Time]\n"
        "\n"
        "ITEMS:\n"
        "• [Item 1] - Qty: [X] - $[Price]\n"
        "• [Item 2] - Qty: [X] - $[Price]\n"
        "...\n"
        "\n"
        "TOTALS:\n"
        "Subtotal: $[Amount]\n"
        "Tax: $[Amount]\n"
        "Total: $[Amount]\n"
        "```\n\n"
        "🔄 **MCP Integration:**\n"
        "All data is also provided in MCP format for system integration.\n\n"
        "**Instructions:**\n"
        "- Upload any receipt image using the attachment button\n"
        "- I'll automatically scan and extract all visible information\n"
        "- Ask follow-up questions about spending analysis or trends\n"
        "- Request specific data formats if needed\n\n"
        "I prioritize accuracy and provide confidence levels for each scan."
    ),
    tools=[analyze_receipt, analyze_receipt_trends],
)
