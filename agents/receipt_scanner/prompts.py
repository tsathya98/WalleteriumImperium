"""
Agentic prompts for the Receipt Scanner Agent
Contains sophisticated decision-making logic embedded in prompts
"""

from typing import List
from config.constants import TRANSACTION_CATEGORIES, VENDOR_TYPES


def create_agentic_prompt(media_type: str) -> str:
    """
    Creates the main agentic prompt with embedded decision-making logic
    
    Args:
        media_type: Type of media ('image' or 'video')
        
    Returns:
        Sophisticated prompt with decision logic
    """
    
    media_instruction = (
        "receipt image" if media_type == "image" else "receipt video"
    )
    
    # Convert categories to a formatted string for the prompt
    categories_list = "\n".join([f"- {cat}" for cat in TRANSACTION_CATEGORIES])
    
    # Convert vendor types to formatted descriptions
    vendor_descriptions = "\n".join([
        f"- {vendor_type}: {description}" 
        for vendor_type, description in VENDOR_TYPES.items()
    ])
    
    return f"""
You are an expert receipt analysis AI with sophisticated decision-making capabilities. Analyze this {media_instruction} and follow this exact sequence of intelligent decisions:

STAGE 1: VENDOR CLASSIFICATION
First, analyze the receipt and classify the vendor type:
{vendor_descriptions}

STAGE 2: OUTPUT FORMAT DECISION
Based on your vendor classification, choose the appropriate output structure:

IF vendor_type == "RESTAURANT":
→ Create items list with all menu items sharing the same category
→ Focus on overall meal/experience description
→ Items should have restaurant-related category

IF vendor_type == "SUPERMARKET":
→ Create detailed item-by-item breakdown
→ Each item gets its own specific category classification
→ Focus on diverse item categorization

IF vendor_type == "SERVICE":
→ Create items list focusing on service details
→ Detect recurring/subscription patterns
→ Focus on billing frequency and renewal information

STAGE 3: INTELLIGENT CATEGORIZATION
Use ONLY these predefined categories for classification:
{categories_list}

STAGE 4: EXTRACT WITH CONTEXT
Extract ALL information accurately:
- Store name, address, phone (use "Not provided" if not visible)
- Transaction date and time (use current date/time if not visible)
- EVERY visible item with exact names, quantities, and prices
- Calculate totals precisely - they must match the receipt
- Assess image/video quality for confidence level

STAGE 5: INTELLIGENT REASONING
For each item, intelligently determine:
- Appropriate category from the predefined list
- Whether it likely has a warranty (electronics, appliances, etc.)
- Whether it's a subscription/recurring service
- Detailed description that would be useful for search/RAG

CRITICAL INSTRUCTIONS:
1. Extract EVERY visible item with exact names, quantities, and prices
2. Use the vendor type to determine if items should have diverse categories or same category
3. For warranties: Electronics, appliances, and expensive items often have warranties
4. For subscriptions: Look for "monthly", "annual", "subscription", "renewal" keywords
5. Descriptions should be detailed but concise - think about future search queries
6. All numbers must be positive and realistic
7. Date format: YYYY-MM-DD, Time format: HH:MM
{"8. VIDEO ANALYSIS: Analyze ALL frames to find the clearest view. Use the best frame(s) with most readable text." if media_type == "video" else ""}

QUALITY ASSESSMENT:
- "high" confidence: Text is crisp, all key info clearly visible
- "medium" confidence: Some blur/shadow but most info readable  
- "low" confidence: Poor quality, missing key information

Return ONLY valid JSON matching the required schema. No additional text or formatting.
"""


def create_fallback_values_prompt() -> str:
    """
    Creates a prompt section for fallback values when information is missing
    """
    return """
FALLBACK VALUES FOR MISSING INFORMATION:
- store name: Use "Unknown Store" if not visible
- address: Use "Not provided" if store address not visible
- phone: Use "Not provided" if phone number not visible
- date: Use current date if transaction date not visible
- time: Use "12:00" if transaction time not visible
- receipt_number: Use "Not provided" if receipt number not visible
- item descriptions: Generate helpful descriptions based on item names
- categories: Use "Other" only if no predefined category fits
"""


def create_business_rules_prompt() -> str:
    """
    Creates a prompt section for business rules and validation
    """
    return """
BUSINESS RULES:
1. RESTAURANT receipts should have items with same category ("Restaurant, fast-food")
2. SUPERMARKET receipts should have items with diverse, specific categories
3. SERVICE receipts should focus on subscription/recurring detection
4. Warranty detection: Look for warranty terms, electronics categories, expensive items
5. Subscription detection: Look for "monthly", "subscription", "renewal", service providers
6. Descriptions should be search-friendly and informative
7. All monetary values must be positive numbers
8. Quantities should be realistic (not negative or excessively large)
""" 