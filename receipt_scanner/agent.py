import datetime, uuid
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any
from .sub_agents.multimodal_processor import multimodal_processor_agent
from .sub_agents.gemini_processor import gemini_processor_agent  
from .sub_agents.llm_enricher import llm_enricher_agent
from .sub_agents.storage import storage_agent
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from .models import ProcessingResult


def set_session(callback_context: CallbackContext):
    """
    Sets a unique ID and timestamp in the callback context's state.
    This function is called before the receipt_processing_agent executes.
    """
    callback_context.state["unique_id"] = str(uuid.uuid4())
    callback_context.state["timestamp"] = datetime.datetime.now(
        ZoneInfo("UTC")
    ).isoformat()


async def save_receipt_to_database(
    store_name: str,
    total_amount: float,
    transaction_date: str,
    items: List[Dict[str, Any]],
    store_address: Optional[str] = None,
    receipt_number: Optional[str] = None,
    payment_method: Optional[str] = None,
    currency: str = "USD",
    user_category: Optional[str] = None,
    user_tags: Optional[List[str]] = None
) -> dict:
    """
    Save receipt data to the database after analysis.
    
    Args:
        store_name: Name of the store/merchant
        total_amount: Final total amount paid
        transaction_date: Date of transaction (YYYY-MM-DD format)
        items: List of items purchased with details
        store_address: Store address (optional)
        receipt_number: Receipt/transaction number (optional)
        payment_method: Payment method used (optional)
        currency: Currency code (default: USD)
        user_category: User-defined category (optional)
        user_tags: User-defined tags (optional)
        
    Returns:
        dict: Storage result with status and information
    """
    try:
        from .models import (
            ProcessedReceipt, MCPFormat, ReceiptPayload, ProcessingMetadata,
            StoreDetails, TransactionDetails, LineItem, PaymentSummary,
            PaymentMethod, UserDefinedMetadata, ProcessorModel, InputType,
            create_receipt_id
        )
        from .sub_agents.storage import store_receipt
        
        # Create receipt ID
        receipt_id = create_receipt_id()
        
        # Create processing metadata
        metadata = ProcessingMetadata(
            receipt_id=receipt_id,
            source_filename="manual_analysis",
            source_type=InputType.IMAGE,
            processor_model=ProcessorModel.GEMINI_2_5_FLASH,
        )
        
        # Create store details
        store_details = StoreDetails(
            name=store_name,
            address=store_address,
            confidence_score=0.9
        )
        
        # Parse transaction date
        try:
            parsed_date = datetime.datetime.strptime(transaction_date, "%Y-%m-%d")
            transaction_details = TransactionDetails(
                date=parsed_date.strftime("%Y-%m-%d"),
                time=parsed_date.strftime("%H:%M:%S") if parsed_date.hour or parsed_date.minute else None,
                currency=currency,
                transaction_id=receipt_number
            )
        except:
            # Fallback to current date if parsing fails
            now = datetime.datetime.now()
            transaction_details = TransactionDetails(
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                currency=currency,
                transaction_id=receipt_number
            )
        
        # Create line items
        line_items = []
        for item in items:
            line_item = LineItem(
                description=item.get("description", "Unknown Item"),
                quantity=float(item.get("quantity", 1)),
                unit_price=float(item.get("unit_price", 0)),
                total_price=float(item.get("total_price", 0)),
                category=item.get("category", "other"),
                confidence_score=0.8
            )
            line_items.append(line_item)
        
        # Create payment summary
        subtotal = sum(item.total_price for item in line_items)
        payment_summary = PaymentSummary(
            subtotal=subtotal,
            total_amount=total_amount
        )
        
        # Create payment method
        payment_method_obj = PaymentMethod(
            method=payment_method or "Unknown"
        )
        
        # Create user metadata
        user_metadata = UserDefinedMetadata(
            overall_category=user_category,
            tags=user_tags or []
        )
        
        # Create receipt payload
        receipt_payload = ReceiptPayload(
            processing_metadata=metadata,
            store_details=store_details,
            transaction_details=transaction_details,
            line_items=line_items,
            payment_summary=payment_summary,
            payment_method=payment_method_obj,
            user_defined_metadata=user_metadata
        )
        
        # Create MCP format
        mcp_format = MCPFormat(
            status="success",
            confidence_score=0.8
        )
        
        # Create processed receipt
        processed_receipt = ProcessedReceipt(
            mcp_format=mcp_format,
            receipt_payload=receipt_payload
        )
        
        # Store the receipt
        storage_result = await store_receipt(processed_receipt)
        
        if storage_result.get("success"):
            return {
                "status": "success",
                "message": f"Receipt saved successfully! Receipt ID: {receipt_id}",
                "receipt_id": receipt_id,
                "storage_location": storage_result.get("storage_location")
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to save receipt: {storage_result.get('error')}",
                "receipt_id": receipt_id
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error saving receipt: {str(e)}",
            "receipt_id": None
        }


# This agent handles comprehensive receipt processing with direct image analysis
receipt_processing_agent = Agent(
    name="receipt_processing_agent",
    model="gemini-2.5-flash",
    description=(
        "Comprehensive receipt processing agent that can analyze any input type including images, videos, text, PDFs, and Excel files. "
        "Uses Gemini 2.5 Flash Vision AI for direct image analysis and can save processed data to database."
    ),
    instruction=(
        "You are a comprehensive receipt processing agent with advanced vision AI capabilities. Your role is to:\n\n"
        
        "**For Images and Visual Content:**\n"
        "- DIRECTLY analyze receipt images using your built-in vision capabilities\n"
        "- Extract ALL visible information including store details, items, prices, taxes, totals\n"
        "- Provide structured, detailed analysis in a clear format\n"
        "- Categorize items logically (food, household, electronics, etc.)\n"
        "- Calculate totals and verify mathematical accuracy\n"
        "- OFFER to save the receipt data to the database after analysis\n\n"
        
        "**For General Questions:**\n"
        "- Explain your comprehensive receipt analysis capabilities\n"
        "- Describe what information you can extract from different input types\n\n"
        
        "**Your Capabilities:**\n"
        "- **Images & Videos**: Direct Vision AI analysis with Gemini 2.5 Flash for high-accuracy text extraction\n"
        "- **PDFs & Text**: Advanced OCR and LLM enrichment for structured data extraction\n"
        "- **Excel/CSV**: Parse and categorize structured receipt data\n"
        "- **Storage & Analytics**: Can save processed receipts to database with search and analytics capabilities\n\n"
        
        "**What You Extract from Receipts:**\n"
        "- **Store Information**: Name, address, phone, date, time, store ID\n"
        "- **Transaction Details**: Receipt number, cashier, register, payment method\n"
        "- **Itemized Purchases**: Product names, quantities, unit prices, total prices, categories\n"
        "- **Financial Summary**: Subtotals, taxes (with rates), discounts, promotions, final total\n"
        "- **Special Information**: Warranty details, return policies, loyalty points\n\n"
        
        "**When analyzing receipt images:**\n"
        "1. Examine the image carefully for ALL visible text and numbers\n"
        "2. Extract store name, address, and transaction details at the top\n"
        "3. List EVERY item with description, quantity, and price\n"
        "4. Categorize each item appropriately\n"
        "5. Calculate and verify subtotals, taxes, and final totals\n"
        "6. Note any discounts, promotions, or special offers\n"
        "7. Present the information in a clear, organized format\n"
        "8. **ALWAYS ask if the user wants to save the receipt to the database**\n\n"
        
        "**Output Format for Receipt Analysis:**\n"
        "Present your analysis in this structured format:\n\n"
        "```\n"
        "## 🧾 RECEIPT ANALYSIS\n\n"
        "### 🏪 Store Information\n"
        "- **Name**: [Store Name]\n"
        "- **Address**: [Full Address]\n"
        "- **Date**: [YYYY-MM-DD]\n"
        "- **Time**: [HH:MM:SS]\n"
        "- **Receipt #**: [Transaction ID]\n\n"
        "### 🛒 Itemized Purchases\n"
        "| Item | Qty | Unit Price | Total | Category |\n"
        "|------|-----|------------|-------|----------|\n"
        "[List all items here]\n\n"
        "### 💰 Financial Summary\n"
        "- **Subtotal**: $X.XX\n"
        "- **Tax**: $X.XX (X.X%)\n"
        "- **Discounts**: $X.XX\n"
        "- **Final Total**: $X.XX\n"
        "- **Payment Method**: [Method]\n\n"
        "### 📋 Additional Details\n"
        "[Any promotions, warranties, return policies, etc.]\n"
        "```\n\n"
        
        "**After providing the analysis, ALWAYS ask:**\n"
        "\"Would you like me to save this receipt to the database for future tracking and analytics?\"\n\n"
        
        "**When the user wants to save the receipt:**\n"
        "Use the save_receipt_to_database tool with the extracted information. The tool requires:\n"
        "- store_name: The store/merchant name\n"
        "- total_amount: The final total (as a number, no currency symbol)\n"
        "- transaction_date: Date in YYYY-MM-DD format\n"
        "- items: Array of items with description, quantity, unit_price, total_price, category\n"
        "- Optional: store_address, receipt_number, payment_method, currency, user_category, user_tags\n\n"
        
        "Always be thorough, accurate, and helpful in your analysis!"
    ),
    tools=[save_receipt_to_database],
    before_agent_callback=set_session,
)

root_agent = receipt_processing_agent 