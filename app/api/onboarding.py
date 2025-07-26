# app/api/onboarding.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

from agents.onboarding_agent.agent import onboarding_agent, user_profiles
from agents.onboarding_agent.schemas import OnboardingRequest

router = APIRouter()

# In-memory session store.
# In a production environment, this would be replaced with a real session store like Redis.
sessions: Dict[str, str] = {}


class OnboardingResponse(BaseModel):
    response: str
    session_id: str


@router.post("/chat", response_model=OnboardingResponse)
async def chat_with_onboarding_agent(request: OnboardingRequest):
    """
    Handles a chat interaction with the onboarding agent.
    """
    session_id = request.session_id
    conversation_history = sessions.get(session_id, "")
    full_query = f"{conversation_history}\nUser: {request.query}"

    try:
        # Format the instruction with the user's language
        formatted_instruction = onboarding_agent.instruction.format(language=request.language)

        # Create a temporary agent with the formatted instruction
        temp_agent = onboarding_agent.with_instruction(formatted_instruction)

        # Invoke the agent with the full query
        agent_response = await temp_agent.invoke_async(full_query)

        # Update the conversation history
        sessions[session_id] = f"{full_query}\nAgent: {agent_response}"

        return OnboardingResponse(response=agent_response, session_id=session_id)

    except Exception as e:
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