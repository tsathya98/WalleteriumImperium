# agents/onboarding_agent/agent.py

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio

import vertexai
from vertexai.generative_models import (
    GenerativeModel, 
    Part, 
    GenerationConfig,
    Tool,
    FunctionDeclaration,
    Content,
    ChatSession
)

from app.core.config import get_settings
from app.services.firestore_service import FirestoreService
from .schemas import UserProfile

logger = logging.getLogger(__name__)
settings = get_settings()


def save_user_profile_data(
    firestore_service: FirestoreService,
    user_id: str,
    profile_data: dict
) -> dict:
    """Save complete user profile data to Firestore - all in one document"""
    try:
        # Prepare complete user data with all assets embedded
        user_data = {
            "uid": user_id,
            "last_seen": datetime.now().isoformat(),
            "persona": profile_data.get("persona"),
            "onboarding_completed": profile_data.get("onboarding_complete", False),
            "financial_goals": profile_data.get("financial_goals", []),
            "spending_habits": profile_data.get("spending_habits"),
            "risk_appetite": profile_data.get("risk_appetite"),
            "investment_interests": profile_data.get("investment_interests", []),
            "has_invested_before": profile_data.get("has_invested_before"),
            "recurring_bills": profile_data.get("recurring_bills", []),
            # Store all assets directly in the main document
            "real_estate_assets": profile_data.get("real_estate_assets", []),
            "gold_assets": profile_data.get("gold_assets", []),
            "stock_assets": profile_data.get("stock_assets", []),
            "vehicle_assets": profile_data.get("vehicle_assets", []),
            "crypto_assets": profile_data.get("crypto_assets", []),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save everything to main document (using sync method for hackathon speed)
        firestore_service.client.collection("wallet_user_collection").document(user_id).set(user_data, merge=True)
        
        logger.info(f"Complete profile with assets saved to main document for user {user_id}")
        return {"status": "success", "message": "Profile saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving profile for user {user_id}: {e}")
        return {"status": "error", "message": str(e)}


def get_complete_user_profile(
    firestore_service: FirestoreService,
    user_id: str
) -> dict:
    """Retrieve complete user profile including assets - now from single document"""
    try:
        # Get complete profile from main document
        user_doc = firestore_service.client.collection("wallet_user_collection").document(user_id).get()
        
        if not user_doc.exists:
            return {"status": "not_found", "profile": None}
            
        profile = user_doc.to_dict()
        
        # All data including assets is now in the main document
        logger.info(f"Successfully retrieved complete profile for user {user_id}")
        return {"status": "success", "profile": profile}
        
    except Exception as e:
        logger.error(f"Error retrieving profile for user {user_id}: {e}")
        return {"status": "error", "profile": None}


async def update_user_profile(
    firestore_service: FirestoreService,
    user_id: str,
    language: str = "en",
    financial_goals: list = None,
    spending_habits: str = None,
    risk_appetite: str = None,
    persona: str = None,
    has_invested_before: bool = None,
    investment_interests: list = None,
    real_estate_assets: List[Dict[str, Any]] = None,
    gold_assets: List[Dict[str, Any]] = None,
    stock_assets: List[Dict[str, Any]] = None,
    vehicle_assets: List[Dict[str, Any]] = None,
    crypto_assets: List[Dict[str, Any]] = None,
    recurring_bills: List[Dict[str, Any]] = None,
    onboarding_complete: bool = False,
) -> Dict[str, Any]:
    """Update user profile with collected information"""
    logger.info(f"Updating profile for user_id: {user_id}")
    
    # Build complete profile data
    profile_data = {
        "user_id": user_id,
        "language": language,
        "financial_goals": financial_goals or [],
        "spending_habits": spending_habits,
        "risk_appetite": risk_appetite,
        "persona": persona,
        "has_invested_before": has_invested_before,
        "investment_interests": investment_interests or [],
        "real_estate_assets": real_estate_assets or [],
        "gold_assets": gold_assets or [],
        "stock_assets": stock_assets or [],
        "vehicle_assets": vehicle_assets or [],
        "crypto_assets": crypto_assets or [],
        "recurring_bills": recurring_bills or [],
        "onboarding_complete": onboarding_complete,
        "updated_at": datetime.now().isoformat()
    }
    
    # Save to Firestore
    save_result = save_user_profile_data(firestore_service, user_id, profile_data)
    
    return {
        "status": save_result["status"],
        "user_id": user_id,
        "onboarding_complete": onboarding_complete,
        "message": save_result.get("message", "Profile updated")
    }


async def generate_complete_profile(
    firestore_service: FirestoreService,
    user_id: str,
    conversation_summary: str
) -> Dict[str, Any]:
    """Generate complete user profile from conversation"""
    logger.info(f"Generating complete profile for user {user_id}")
    
    # For hackathon - create a comprehensive profile based on conversation
    # In production, this would use advanced NLP to extract structured data
    
    conversation = conversation_summary.lower()
    
    # Simple keyword-based extraction for hackathon speed
    profile_data = {
        "user_id": user_id,
        "persona": "Explorer",  # Default
        "financial_goals": [],
        "spending_habits": "casual",
        "risk_appetite": "medium",
        "investment_interests": [],
        "has_invested_before": False,
        "real_estate_assets": [],
        "gold_assets": [],
        "stock_assets": [],
        "vehicle_assets": [],
        "crypto_assets": [],
        "recurring_bills": [],
        "onboarding_complete": True,
        "generated_at": datetime.now().isoformat()
    }
    
    # Persona detection
    if any(word in conversation for word in ["save", "budget", "careful", "track", "plan"]):
        profile_data["persona"] = "Budgetor"
    elif any(word in conversation for word in ["invest", "stock", "portfolio", "grow"]):
        profile_data["persona"] = "Investor"
    elif any(word in conversation for word in ["optimize", "best", "compare", "research"]):
        profile_data["persona"] = "Maximizer"
    elif any(word in conversation for word in ["quick", "fast", "spontaneous", "immediate"]):
        profile_data["persona"] = "Spontaneous"
    
    # Investment interests extraction
    if "house" in conversation or "property" in conversation or "real estate" in conversation:
        profile_data["investment_interests"].append("real_estate")
        if "bought" in conversation or "own" in conversation:
            profile_data["has_invested_before"] = True
            
    if "gold" in conversation or "jewelry" in conversation:
        profile_data["investment_interests"].append("gold")
        if "bought" in conversation or "own" in conversation:
            profile_data["has_invested_before"] = True
            
    if "stock" in conversation or "mutual fund" in conversation or "shares" in conversation:
        profile_data["investment_interests"].append("stocks")
        if "bought" in conversation or "own" in conversation:
            profile_data["has_invested_before"] = True
            
    if "crypto" in conversation or "bitcoin" in conversation:
        profile_data["investment_interests"].append("crypto")
        
    if "car" in conversation or "vehicle" in conversation or "bike" in conversation:
        profile_data["investment_interests"].append("vehicles")
    
    # Goals extraction
    if "travel" in conversation or "tour" in conversation:
        profile_data["financial_goals"].append("Travel fund")
    if "emergency" in conversation:
        profile_data["financial_goals"].append("Emergency fund")
    if "retirement" in conversation:
        profile_data["financial_goals"].append("Retirement planning")
    if "house" in conversation and "buy" in conversation:
        profile_data["financial_goals"].append("Home purchase")
    
    # Save the generated profile
    save_result = save_user_profile_data(firestore_service, user_id, profile_data)
    
    if save_result["status"] == "success":
        return {"status": "success", "profile": profile_data}
    else:
        return {"status": "error", "message": save_result["message"]}


class OnboardingAgent:
    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        self.sessions: Dict[str, ChatSession] = {}
        self.message_counters: Dict[str, int] = {}  # Track message count per session
        self.max_messages = 5  # Maximum exchanges before forced completion
        
        logger.info("Initializing Onboarding Agent with Vertex AI...")
        vertexai.init(project=self.project_id, location=self.location)
        
        # Define function declarations for tools
        update_profile_declaration = FunctionDeclaration(
            name="update_user_profile",
            description="Update user profile with collected information. Call this to save user data during conversation.",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "language": {"type": "string", "description": "User's preferred language"},
                    "financial_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of financial goals"
                    },
                    "spending_habits": {"type": "string", "description": "Spending habits description"},
                    "risk_appetite": {"type": "string", "description": "Risk tolerance (low/medium/high)"},
                    "persona": {"type": "string", "description": "Financial persona (Budgetor/Investor/Explorer/Maximizer/Spontaneous)"},
                    "has_invested_before": {"type": "boolean", "description": "Has investment experience"},
                    "investment_interests": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Investment interests"
                    },
                    "real_estate_assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "size_sqft": {"type": "number"},
                                "purchase_price": {"type": "number"},
                                "purchase_date": {"type": "string"},
                                "location": {"type": "string"}
                            }
                        }
                    },
                    "gold_assets": {
                        "type": "array",
                        "items": {
                            "type": "object", 
                            "properties": {
                                "volume_g": {"type": "number"},
                                "purchase_price_per_g": {"type": "number"},
                                "purchase_date": {"type": "string"}
                            }
                        }
                    },
                    "stock_assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "units_bought": {"type": "number"},
                                "unit_price_purchase": {"type": "number"},
                                "exchange_date": {"type": "string"}
                            }
                        }
                    },
                    "recurring_bills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "amount": {"type": "number"},
                                "due_date": {"type": "number"}
                            }
                        }
                    },
                    "onboarding_complete": {"type": "boolean", "description": "Mark onboarding as complete"}
                }
            }
        )
        
        generate_profile_declaration = FunctionDeclaration(
            name="generate_complete_profile",
            description="Generate complete user profile from conversation. Call this when onboarding is complete.",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "conversation_summary": {"type": "string", "description": "Summary of conversation"}
                }
            }
        )
        
        # Create tools
        self.tools = [
            Tool(function_declarations=[update_profile_declaration, generate_profile_declaration])
        ]
        
        # Initialize model
        self.model = GenerativeModel(
            model_name=self.model_name,
            tools=self.tools,
            generation_config=GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            ),
            system_instruction="""
You are a friendly, expert financial onboarding assistant for Walletarium Imperium. Your goal is to create comprehensive user profiles through natural conversation.

## CRITICAL CONSTRAINT: You have MAXIMUM 5 message exchanges to complete onboarding!

## Your Mission (in 5 exchanges max):
1. **Discover Financial Persona**: Quickly identify if they're a Budgetor, Investor, Explorer, Maximizer, or Spontaneous spender
2. **Catalog Key Assets**: Focus on major investments (property, gold, stocks, crypto)
3. **Understand Goals**: Get their primary financial goal
4. **Complete Profile**: Generate complete profile by exchange 5

## Efficient Questions Strategy:
- Exchange 1: "If you got ₹50,000 unexpectedly, what would you do? Also, do you currently invest in anything?"
- Exchange 2: "What's your biggest financial goal this year? How do you prefer to track spending?"
- Exchange 3: "Do you own property, gold, stocks, or crypto? Any major monthly bills?"
- Exchange 4: Clarify any missing details, confirm persona
- Exchange 5: MUST call generate_complete_profile to finish

## Conversation Style:
- Be efficient but friendly
- Ask compound questions to gather more info quickly
- Show genuine interest but move conversation forward
- Adapt to their language preference

## When to Use Tools:
- Use `update_user_profile` to save information as you collect it (exchanges 2-4)
- MUST use `generate_complete_profile` by exchange 5 at latest
- Mark `onboarding_complete=True` when profile is comprehensive

Remember: You MUST complete onboarding within 5 exchanges. Be efficient!
            """
        )
        
        logger.info("✅ Onboarding Agent initialized successfully")
    
    async def chat(self,
                   firestore_service: FirestoreService,
                   session_id: str,
                   user_id: str,
                   query: str,
                   language: str = "en") -> Dict[str, Any]:
        """Handle chat interaction with user"""
        try:
            logger.info(f"Agent starting chat for session_id: {session_id}")
            
            # Initialize or increment message counter
            if session_id not in self.message_counters:
                self.message_counters[session_id] = 0
            
            self.message_counters[session_id] += 1
            current_exchange = self.message_counters[session_id]
            
            logger.info(f"Exchange {current_exchange}/{self.max_messages} for session {session_id}")
            
            # Get or create chat session
            if session_id not in self.sessions:
                self.sessions[session_id] = self.model.start_chat()
                logger.info(f"Started new chat session for {session_id}")
            
            chat_session = self.sessions[session_id]
            
            # Force completion if we've reached max messages
            if current_exchange >= self.max_messages:
                logger.info(f"Reached max exchanges ({self.max_messages}), forcing completion")
                
                # Generate profile with conversation summary
                conversation_summary = f"User query: {query}. This was exchange {current_exchange}."
                profile_result = await generate_complete_profile(
                    firestore_service, user_id, conversation_summary
                )
                
                return {
                    "text": f"Thank you for sharing! I've created your complete financial profile based on our conversation. Your onboarding is now complete! 🎉",
                    "session_id": session_id,
                    "onboarding_complete": True
                }
            
            # Send user message with exchange context
            context_message = f"Exchange {current_exchange}/{self.max_messages} - User ({language}): {query}"
            if current_exchange == 1:
                context_message += " (This is the first exchange - be efficient!)"
            elif current_exchange == self.max_messages - 1:
                context_message += " (This is the second-to-last exchange - prepare to complete!)"
            
            response = chat_session.send_message(context_message)
            
            # Check for function calls
            onboarding_complete = False
            
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        logger.info(f"Gemini requested function call: {function_name}")
                        logger.info(f"Function args: {function_args}")
                        
                        # Execute function
                        if function_name == "update_user_profile":
                            function_args["user_id"] = user_id
                            function_result = await update_user_profile(
                                firestore_service, **function_args
                            )
                            onboarding_complete = function_args.get("onboarding_complete", False)
                            
                        elif function_name == "generate_complete_profile":
                            function_args["user_id"] = user_id
                            function_result = await generate_complete_profile(
                                firestore_service, **function_args
                            )
                            onboarding_complete = True
                            
                        else:
                            function_result = {"error": f"Unknown function: {function_name}"}
                        
                        # Send function result back to model
                        chat_session.send_message(
                            Part.from_function_response(
                                name=function_name,
                                response=function_result
                            )
                        )
                        
                        # Get final response
                        final_response = chat_session.send_message(
                            "Continue the conversation based on the function result."
                        )
                        
                        return {
                            "text": final_response.text,
                            "session_id": session_id,
                            "onboarding_complete": onboarding_complete
                        }
            
            return {
                "text": response.text,
                "session_id": session_id, 
                "onboarding_complete": onboarding_complete
            }
            
        except Exception as e:
            logger.error(f"Error in onboarding chat: {e}", exc_info=True)
            return {
                "text": "I'm having some technical difficulties. Please try again!",
                "session_id": session_id,
                "onboarding_complete": False
            }


# Global instance
onboarding_agent = OnboardingAgent()

def get_onboarding_agent():
    """Get the global onboarding agent"""
    return onboarding_agent
