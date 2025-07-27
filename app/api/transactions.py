"""
Minimal Viable Transaction RAG API
"""
from fastapi import APIRouter, HTTPException, Request
from agents.transaction_rag_agent.agent import get_rag_agent

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/chat")
async def chat_with_transactions(request: Request):
    """
    Chat with your transaction data using natural language.
    This endpoint queries a pre-configured RAG index.
    """
    try:
        body = await request.json()
        query = body.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty.")
            
        agent = get_rag_agent()
        response = agent.chat(query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 