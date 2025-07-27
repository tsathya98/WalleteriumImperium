# Transaction RAG System - Setup Guide

## 🚀 Overview

You now have a complete **RAG-powered transaction chatbot** using Vertex AI RAG Engine! This system automatically indexes transactions as searchable chunks and provides natural language access to financial data.

## ✅ What's Been Implemented

### 1. **Transaction RAG Agent** (`agents/transaction_rag_agent/`)
- **Natural Language Queries**: Ask questions about transactions in plain English
- **Auto-Indexing**: Transactions automatically become searchable chunks
- **Real-time Analysis**: Instant insights about spending patterns
- **Vertex AI RAG Engine**: Uses Google's latest RAG technology

### 2. **API Endpoints** (`app/api/transactions.py`)
```bash
POST /api/v1/transactions/chat           # Chat with transactions
POST /api/v1/transactions/index          # Index specific transaction
POST /api/v1/transactions/index/bulk     # Bulk index all transactions
POST /api/v1/transactions/analytics      # AI-powered financial insights
GET  /api/v1/transactions/corpus/info    # RAG corpus information
```

### 3. **Auto-Event Triggers** (Firestore Integration)
- Transactions automatically indexed when created/updated
- Background processing doesn't block main operations
- Real-time transaction data becomes immediately queryable

## 🔧 Quick Setup

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Set Environment Variables**
```bash
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
export VERTEX_AI_LOCATION=us-central1
export VERTEX_AI_MODEL=gemini-2.5-flash
```

### 3. **Enable Required APIs**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable firestore.googleapis.com
```

### 4. **Start the Server**
```bash
python main.py
```

### 5. **Test the System**
```bash
python scripts/test_transaction_rag.py
```

## 🎯 Example Usage

### Chat with Your Transactions
```bash
curl -X POST http://localhost:8080/api/v1/transactions/chat \
-H "Content-Type: application/json" \
-d '{
  "query": "How much did I spend on restaurants last month?",
  "user_id": "user123",
  "session_id": "session-abc-123",
  "language": "en"
}'
```

### Expected Response
```json
{
  "response": "Based on your transaction history, you spent $347.82 on restaurants last month.\n\n**Key Findings:**\n- Your top restaurant was Olive Garden ($89.43 across 3 visits)\n- You dined out 12 times total\n- Average meal cost: $28.99",
  "session_id": "session-abc-123",
  "sources": [
    {
      "title": "Transaction - Olive Garden - $29.81",
      "snippet": "Restaurant transaction at Olive Garden on 2024-10-15"
    }
  ],
  "query_type": "spending_analysis",
  "confidence": 0.9,
  "language": "en"
}
```

## 🤖 Sample Queries You Can Try

### Spending Analysis
```
"How much did I spend on restaurants last month?"
"What was my total spending in groceries this year?"
"Show me my entertainment expenses for the last 3 months"
```

### Category Insights
```
"What are my top spending categories?"
"Break down my expenses by category"
"Which category am I spending the most money on?"
```

### Time Analysis
```
"Compare my spending this month vs last month"
"What's my average monthly spending?"
"Show me my spending trends over the last 6 months"
```

### Merchant Analysis
```
"Where do I shop most frequently?"
"What's my biggest purchase at Starbucks?"
"Show me all transactions at Target"
```

### Smart Search
```
"Find all transactions containing coffee"
"Show me when I bought electronics"
"What food items did I purchase last week?"
```

### Budget Insights
```
"Am I overspending anywhere?"
"What are my biggest expenses?"
"Identify unusual spending patterns"
```

## 📊 System Architecture

```
Transaction Creation → Firestore → Auto-Index → RAG Corpus → Natural Language Queries
```

1. **Transaction Input**: From receipt scanner or manual entry
2. **Auto-Indexing**: Background process converts to searchable chunks
3. **RAG Storage**: Vertex AI RAG Engine stores semantic vectors
4. **Query Processing**: Natural language → Vector search → AI response
5. **Contextual Answers**: Grounded responses with source attribution

## 🔍 How It Works

### Automatic Transaction Indexing
When a new transaction is created:
```
TRANSACTION RECORD:
Store/Vendor: Starbucks
Date/Time: 2024-11-15T10:30:00Z
Amount: $4.65 (debit)
Category: Food & drink

Items purchased:
- Grande Latte: 1x $4.65 (Beverages)

ANALYSIS CONTEXT:
- Daily coffee routine transaction
- Regular merchant visit
- Beverage category spending
```

### RAG Query Processing
1. **User Query**: "How much do I spend on coffee?"
2. **Vector Search**: Finds relevant coffee transactions
3. **AI Analysis**: Gemini analyzes patterns
4. **Grounded Response**: Response with transaction sources

## ⚡ Performance Features

- **Real-time Indexing**: New transactions immediately queryable
- **Fast Responses**: 1-3 seconds for most queries
- **Source Attribution**: Always shows which transactions were used
- **Session Context**: Remembers conversation history
- **Error Recovery**: Graceful handling of edge cases

## 🛠️ Customization

### Custom Query Types
Edit `agents/transaction_rag_agent/prompts.py` to add new query patterns:

```python
TRANSACTION_QUERY_EXAMPLES.append({
    "query": "Show me subscription payments",
    "type": "recurring_analysis",
    "intent": "Find recurring subscription transactions"
})
```

### Custom Response Format
Modify `agents/transaction_rag_agent/schemas.py` to add new response fields:

```python
class TransactionRAGResponse(BaseModel):
    # ... existing fields ...
    custom_insights: Optional[List[str]] = None
```

## 🚨 Troubleshooting

### Common Issues

**1. "No relevant transactions found"**
```bash
# Check if transactions are indexed
curl -X GET http://localhost:8080/api/v1/transactions/corpus/info

# Re-index if needed
curl -X POST http://localhost:8080/api/v1/transactions/index/bulk
```

**2. "RAG corpus not initialized"**
- Ensure Vertex AI permissions are set up
- Check GOOGLE_CLOUD_PROJECT_ID environment variable
- Wait a few minutes for initial corpus creation

**3. "Slow response times"**
- RAG corpus may still be initializing
- Check network connectivity to Vertex AI
- Monitor Firestore query performance

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 📈 Next Steps

### Production Deployment
1. **Cloud Run Deployment**: Deploy to production environment
2. **Authentication**: Add proper user authentication
3. **Rate Limiting**: Implement API rate limits
4. **Monitoring**: Set up logging and alerting

### Enhanced Features
1. **Custom Analytics**: Add business-specific insights
2. **Report Generation**: Automated financial reports
3. **Budget Tracking**: Integration with budgeting tools
4. **Expense Categorization**: ML-powered auto-categorization

### Integration Options
1. **Frontend Integration**: Connect to React/Vue.js apps
2. **Mobile API**: Optimize for mobile applications
3. **Webhook Integration**: Connect to external systems
4. **Export Features**: PDF reports, CSV exports

## 📚 Documentation

- **Full API Docs**: http://localhost:8080/docs
- **Agent README**: `agents/transaction_rag_agent/README.md`
- **Test Script**: `scripts/test_transaction_rag.py`
- **Example Queries**: See API documentation

## 🎉 Success!

Your Transaction RAG system is now ready! You can:

✅ Ask natural language questions about transactions  
✅ Get AI-powered financial insights  
✅ Automatically index new transactions  
✅ Access detailed spending analytics  
✅ Build custom financial applications  

**Try it now**: `python scripts/test_transaction_rag.py`

---

*Built with Vertex AI RAG Engine, Gemini 2.5 Flash, and modern AI technologies* 🚀 