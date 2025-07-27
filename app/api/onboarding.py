# app/api/onboarding.py
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Optional

from agents.onboarding_agent import agent as onboarding_agent_module
from agents.onboarding_agent.schemas import OnboardingRequest

router = APIRouter()
logger = logging.getLogger(__name__)

class OnboardingResponse(BaseModel):
    response: str
    session_id: str
    onboarding_complete: bool = False


class ProfileResponse(BaseModel):
    status: str
    profile: Optional[Dict] = None
    message: Optional[str] = None


@router.post("/chat", response_model=OnboardingResponse)
async def chat_with_onboarding_agent(request: Request, body: OnboardingRequest):
    """
    Handles a chat interaction with the onboarding agent system.
    Uses Google ADK agents with orchestrator pattern for comprehensive profiling.
    """
    agent_system = onboarding_agent_module.get_onboarding_agent()
    session_id = body.session_id
    logger.info(f"Received chat request for session_id: {session_id}, user_id: {body.user_id}")
    
    query = body.query
    if not query:
        # Start the onboarding conversation
        query = "Hello! I'm ready to start my financial onboarding. Please help me create my profile."
        logger.info("Empty query on new session. Initiating onboarding conversation.")

    try:
        # Retrieve the initialized FirestoreService from application state
        firestore_service = request.app.state.firestore_service
        logger.info(f"Invoking onboarding agent system for session_id: {session_id}")
        
        agent_result = await agent_system.chat(
            firestore_service=firestore_service,
            session_id=session_id,
            user_id=body.user_id,
            query=query,
            language=body.language
        )
        
        logger.info(f"Agent system returned response for session_id: {session_id}")

        return OnboardingResponse(
            response=agent_result["text"],
            session_id=session_id,
            onboarding_complete=agent_result["onboarding_complete"],
        )

    except Exception as e:
        logger.error(f"Error during chat for session_id: {session_id} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_user_profile(request: Request, user_id: str):
    """
    Retrieves the complete user profile including all assets and preferences.
    Returns structured JSON profile for frontend consumption.
    """
    try:
        firestore_service = request.app.state.firestore_service
        logger.info(f"Retrieving complete profile for user_id: {user_id}")
        
        # Get complete profile using the agent function
        profile_result = onboarding_agent_module.get_complete_user_profile(
            firestore_service, user_id
        )
        
        if profile_result["status"] == "success":
            logger.info(f"Successfully retrieved profile for user {user_id}")
            return ProfileResponse(
                status="success",
                profile=profile_result["profile"]
            )
        elif profile_result["status"] == "not_found":
            logger.info(f"No profile found for user {user_id}")
            return ProfileResponse(
                status="not_found",
                message="User profile not found. Please complete onboarding first."
            )
        else:
            logger.error(f"Error retrieving profile for user {user_id}")
            return ProfileResponse(
                status="error",
                message="Failed to retrieve user profile"
            )
            
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/{user_id}/regenerate", response_model=ProfileResponse)
async def regenerate_user_profile(request: Request, user_id: str):
    """
    Regenerates user profile from conversation history.
    Useful for updating profile after onboarding completion.
    """
    try:
        firestore_service = request.app.state.firestore_service
        logger.info(f"Regenerating profile for user_id: {user_id}")
        
        # For hackathon - simple regeneration
        # In production, would analyze full conversation history
        sample_profile = {
            "user_id": user_id,
            "persona": "Explorer",
            "financial_goals": ["Save for emergency fund", "Start investing"],
            "spending_habits": "casual",
            "risk_appetite": "medium",
            "investment_interests": ["stocks", "real_estate"],
            "has_invested_before": False,
            "real_estate_assets": [],
            "gold_assets": [],
            "stock_assets": [],
            "recurring_bills": [],
            "onboarding_complete": True,
            "regenerated_at": "2025-01-27T12:00:00Z"
        }
        
        # Save regenerated profile
        save_result = onboarding_agent_module.save_user_profile_data(
            firestore_service, user_id, sample_profile
        )
        
        if save_result["status"] == "success":
            return ProfileResponse(
                status="success", 
                profile=sample_profile,
                message="Profile regenerated successfully"
            )
        else:
            return ProfileResponse(
                status="error",
                message="Failed to regenerate profile"
            )
            
    except Exception as e:
        logger.error(f"Error regenerating profile for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
