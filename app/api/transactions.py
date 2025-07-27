"""
Simplified Transaction RAG API - Direct Vertex AI RAG Engine
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Body
from agents.transaction_rag_agent.agent import get_rag_agent

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/index")
async def index_transaction(transaction: dict = Body(...)):
    """
    Indexes a single transaction document. The entire JSON object is
    converted to a string and stored as a single chunk in the RAG engine.
    """
    try:
        agent = get_rag_agent()
        result = agent.index_transaction(transaction)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_transactions(request: Request):
    """
    Chat with your transaction data using natural language.
    This endpoint queries the RAG index directly.
    """
    try:
        body = await request.json()
        query = body.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required.")
            
        agent = get_rag_agent()
        response = agent.chat(query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 