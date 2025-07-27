# Transaction RAG Agent - Simplified

A simplified AI agent that provides vector search capabilities for transaction data using Vertex AI RAG.

## Features

- **Chat API**: Query transaction data using natural language
- **Index Rebuild API**: Rebuild vector embeddings for all transactions
- **Simple Architecture**: Each transaction becomes one vector chunk for optimal search

## APIs

### 1. Chat with Transactions
```
POST /transactions/chat
```

Ask questions about your transaction data in natural language:

**Request:**
```json
{
  "user_id": "user123", 
  "query": "How much did I spend on restaurants last month?"
}
```

**Response:**
```json
{
  "response": "Based on your transaction history, you spent $347.82 on restaurants last month...",
  "sources": [
    {
      "title": "Transaction - Olive Garden - $29.43",
      "snippet": "Transaction at Olive Garden\nAmount: $29.43\nDate: 2024-01-15..."
    }
  ],
  "user_id": "user123",
  "error": null
}
```

### 2. Rebuild Transaction Index
```
POST /transactions/rebuild-index
```

Rebuild the entire vector index from the `transactions` collection:

**Request:**
```json
{
  "batch_size": 50
}
```

**Response:**
```json
{
  "total_transactions": 150,
  "successfully_indexed": 148,
  "failed": 2,
  "success_rate": 0.987,
  "corpus_id": "abc123...",
  "message": "Index rebuild completed in 45.2s. Successfully indexed 148/150 transactions."
}
```

## How it Works

1. **Indexing**: Each transaction from Firestore becomes a single vector chunk
2. **Vector Search**: User queries are matched against transaction vectors using Vertex AI RAG
3. **Response Generation**: AI generates responses based on retrieved relevant transactions

## Transaction Chunk Format

Each transaction is formatted as a simple, searchable chunk:

```
Transaction at Walmart
Amount: $45.67
Date: 2024-01-15 14:30:00
Category: Groceries
Description: Weekly grocery shopping

Items:
- Milk: 1x $3.99
- Bread: 2x $2.50
- Apples: 1x $4.99

Transaction details: Spent $45.67 at Walmart on 2024-01-15 14:30:00. Categorized as Groceries.
```

## Example Queries

- "How much did I spend on restaurants last month?"
- "What are my top spending categories?"
- "Show me my largest transactions"
- "Where do I shop most frequently?"
- "Find transactions containing coffee purchases"

## Setup

The agent automatically:
- Creates a RAG corpus in Vertex AI
- Initializes the generative model with RAG retrieval
- Handles authentication and project configuration

No additional configuration needed beyond the standard app settings. 