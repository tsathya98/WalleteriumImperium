# app/api/onboarding.py
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict

from agents.onboarding_agent import agent as onboarding_agent_module
from agents.onboarding_agent.schemas import OnboardingRequest

router = APIRouter()
logger = logging.getLogger(__name__)

class OnboardingResponse(BaseModel):
    response: str
    session_id: str
    onboarding_complete: bool = False


@router.post("/chat", response_model=OnboardingResponse)
async def chat_with_onboarding_agent(request: Request, body: OnboardingRequest):
    """
    Handles a chat interaction with the onboarding agent.
    If the user's query is empty, it initiates the conversation.
    """
    agent = onboarding_agent_module.get_onboarding_agent()
    session_id = body.session_id
    logger.info(f"Received chat request for session_id: {session_id}, user_id: {body.user_id}")
    
    query = body.query
    if not query:
        # This is the very beginning of the conversation.
        query = "Hello! Please introduce yourself and start the onboarding process."
        logger.info("Empty query on new session. Initiating conversation.")

    try:
        # Retrieve the initialized FirestoreService from application state
        firestore_service = request.app.state.firestore_service
        logger.info(f"Invoking onboarding agent for session_id: {session_id}")
        agent_result = await agent.chat(
            firestore_service=firestore_service,
            session_id=session_id,
            user_id=body.user_id,
            query=query,
            language=body.language
        )
        logger.info(f"Agent returned response for session_id: {session_id}")

        return OnboardingResponse(
            response=agent_result["text"],
            session_id=session_id,
            onboarding_complete=agent_result["onboarding_complete"],
        )

    except Exception as e:
        logger.error(f"Error during chat for session_id: {session_id} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
