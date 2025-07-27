"""
Minimal Viable Transaction RAG API
"""
from fastapi import APIRouter, HTTPException, Request
from agents.transaction_rag_agent.agent import get_rag_agent

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/chat")
async def chat_with_transactions(request: Request):
    """
    Basic chatbot that takes a query and returns a response using RAG
    """
    try:
        body = await request.json()
        query = body.get("query", "")
        
        if not query:
            return {"response": "Please provide a query."}
            
        agent = get_rag_agent()
        response = agent.chat(query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 