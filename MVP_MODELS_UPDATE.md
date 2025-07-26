# 🚀 MVP Models Update Plan

## Current vs New Structure Comparison

### OLD (Complex AI-focused):
```python
class ProcessingResult(BaseModel):
    receipt_id: str
    confidence_score: float
    store_info: StoreInfo  # Complex nested object
    items: List[ReceiptItem]  # Complex item structure
    totals: ReceiptTotals
    ai_insights: AIInsights  # Heavy AI processing
    processing_time: float
    ocr_confidence: float
    language_detected: str
```

### NEW (MVP-focused):
```python
class ReceiptAnalysis(BaseModel):
    place: str                    # Store/merchant name
    category: Optional[str]       # User-defined category  
    description: Optional[str]    # Free-form notes
    time: str                    # ISO 8601 timestamp
    amount: float                # Transaction amount
    transactionType: str         # "credit" or "debit"
    importance: Optional[str]    # "low", "medium", "high"
    warranty: Optional[bool]     # Has warranty?
    recurring: Optional[bool]    # Is subscription?
    
    # Optional nested objects
    subscription: Optional[SubscriptionDetails]
    warrantyDetails: Optional[WarrantyDetails]
```

## Benefits of New Structure:

1. **🎯 Focus**: Only essential fields for receipt tracking
2. **⚡ Fast**: No complex AI processing required
3. **🧪 Testable**: Easy to create realistic mock data
4. **🔄 Iterative**: Can enhance with AI later
5. **📱 Mobile-friendly**: Simpler JSON for Flutter frontend

## Implementation Steps:

1. ✅ Update Pydantic models to match new structure
2. ✅ Create realistic mock receipt generator
3. ✅ Simplify API endpoints to return new format  
4. ✅ Update token-based processing for MVP
5. ✅ Create comprehensive test data
6. ✅ Validate end-to-end functionality

## Mock Data Strategy:

- **Indian Market Focus**: Realistic store names, categories, amounts
- **Variety**: Different transaction types, categories, amounts
- **Edge Cases**: Subscriptions, warranties, high-importance items
- **Realistic Timing**: Proper timestamp handling
- **Cultural Context**: Indian retail patterns and pricing