# app/api/onboarding.py
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

from agents.onboarding_agent.agent import get_onboarding_agent, user_profiles
from agents.onboarding_agent.schemas import OnboardingRequest

router = APIRouter()
logger = logging.getLogger(__name__)

class OnboardingResponse(BaseModel):
    response: str
    session_id: str
    onboarding_complete: bool = False


@router.post("/chat", response_model=OnboardingResponse)
async def chat_with_onboarding_agent(request: OnboardingRequest):
    """
    Handles a chat interaction with the onboarding agent.
    If the user's query is empty, it initiates the conversation.
    """
    agent = get_onboarding_agent()
    session_id = request.session_id
    logger.info(f"Received chat request for session_id: {session_id}, user_id: {request.user_id}")
    
    query = request.query
    if not query:
        # This is the very beginning of the conversation.
        query = "Hello! Please introduce yourself and start the onboarding process."
        logger.info("Empty query on new session. Initiating conversation.")

    try:
        logger.info(f"Invoking onboarding agent for session_id: {session_id}")
        agent_result = await agent.chat(
            session_id=session_id,
            user_id=request.user_id,
            query=query,
            language=request.language
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


@router.get("/profile/{user_id}")
def get_user_profile(user_id: str):
    """
    Retrieves a user's profile.
    """
    if user_id in user_profiles:
        return user_profiles[user_id]
    else:
        raise HTTPException(status_code=404, detail="User not found")
