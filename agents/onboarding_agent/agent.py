# agents/onboarding_agent/agent.py

import logging
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    Part,
    FunctionDeclaration,
    Content,
    ChatSession,
)
from typing import Dict, Any, List
import datetime

from .prompts import ONBOARDING_INSTRUCTION
from .schemas import UserProfile, RealEstateAsset, GoldAsset, StockAsset, RecurringBill
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# In-memory "database" for user profiles.
user_profiles: Dict[str, UserProfile] = {}


def update_user_profile(
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
    recurring_bills: List[Dict[str, Any]] = None,
    onboarding_complete: bool = False,
) -> Dict[str, Any]:
    """
    Creates or updates a user's profile. Call this with onboarding_complete=True when you have gathered all necessary information.
    """
    logger.info(f"Updating profile for user_id: {user_id}")
    if user_id not in user_profiles:
        user_profiles[user_id] = UserProfile(user_id=user_id, language=language)
        logger.info(f"Created new profile for user_id: {user_id}")

    profile = user_profiles[user_id]

    if financial_goals is not None:
        profile.financial_goals.extend(financial_goals)
    if spending_habits is not None:
        profile.spending_habits = spending_habits
    if risk_appetite is not None:
        profile.risk_appetite = risk_appetite
    if persona is not None:
        profile.persona = persona
    if has_invested_before is not None:
        profile.has_invested_before = has_invested_before
    if investment_interests is not None:
        profile.investment_interests.extend(investment_interests)

    if real_estate_assets:
        for asset_data in real_estate_assets:
            profile.assets.real_estate.append(RealEstateAsset(**asset_data))

    if gold_assets:
        for asset_data in gold_assets:
            profile.assets.gold.append(GoldAsset(**asset_data))

    if stock_assets:
        for asset_data in stock_assets:
            profile.assets.stocks.append(StockAsset(**asset_data))

    if recurring_bills:
        for bill_data in recurring_bills:
            profile.recurring_bills.append(RecurringBill(**bill_data))

    logger.info(
        f"Profile for {user_id} updated. Onboarding complete: {onboarding_complete}"
    )
    return {
        "status": "success",
        "user_id": user_id,
        "profile": profile.dict(),
        "onboarding_complete": onboarding_complete,
    }


class OnboardingAgent:
    def __init__(self):
        settings = get_settings()
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        self.sessions: Dict[str, ChatSession] = {}

        logger.info("Initializing Onboarding Agent...")
        vertexai.init(project=self.project_id, location=self.location)

        update_user_profile_declaration = FunctionDeclaration(
            name="update_user_profile",
            description="Creates or updates a user's profile. Use this to save information. Call with onboarding_complete=True when finished.",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The unique identifier for the user.",
                    },
                    "language": {
                        "type": "string",
                        "description": "The user's preferred language, e.g., 'en' or 'es'.",
                    },
                    "financial_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of the user's financial goals.",
                    },
                    "spending_habits": {
                        "type": "string",
                        "description": "A description of spending habits (e.g., 'meticulous', 'casual').",
                    },
                    "risk_appetite": {
                        "type": "string",
                        "description": "The user's appetite for financial risk (e.g., 'low', 'high').",
                    },
                    "persona": {
                        "type": "string",
                        "description": "The user's inferred persona (e.g., 'Budgetor', 'Investor').",
                    },
                    "has_invested_before": {
                        "type": "boolean",
                        "description": "Whether the user has invested before.",
                    },
                    "investment_interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of asset types the user is interested in.",
                    },
                    "real_estate_assets": {
                        "type": "array",
                        "description": "List of the user's real estate assets.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "size_sqft": {"type": "number", "description": "Size in square feet."},
                                "purchase_price": {"type": "number", "description": "Cost of the property."},
                                "purchase_date": {"type": "string", "description": "Purchase date (YYYY-MM-DD)."}
                            }
                        }
                    },
                    "gold_assets": {
                        "type": "array",
                        "description": "List of the user's gold assets.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "volume_g": {"type": "number", "description": "Weight in grams."},
                                "purchase_price_per_g": {"type": "number", "description": "Cost per gram."},
                                "purchase_date": {"type": "string", "description": "Purchase date (YYYY-MM-DD)."}
                            },
                            "required": ["volume_g"]
                        }
                    },
                    "stock_assets": {
                        "type": "array",
                        "description": "List of the user's stock assets.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string", "description": "The stock ticker symbol."},
                                "units_bought": {"type": "number", "description": "Number of units purchased."},
                                "unit_price_purchase": {"type": "number", "description": "Price per unit at purchase."},
                                "exchange_date": {"type": "string", "description": "Purchase date (YYYY-MM-DD)."}
                            },
                            "required": ["ticker", "units_bought"]
                        }
                    },
                    "recurring_bills": {
                        "type": "array",
                        "description": "List of the user's recurring bills.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Name of the bill (e.g., 'Netflix', 'Rent')."},
                                "amount": {"type": "number", "description": "Cost of the bill."},
                                "due_date": {"type": "integer", "description": "Day of the month the bill is due."}
                            },
                            "required": ["name", "amount"]
                        }
                    },
                    "onboarding_complete": {
                        "type": "boolean",
                        "description": "Set to True only when the entire onboarding process is complete.",
                    },
                },
                "required": ["user_id"],
            },
        )

        self.profile_tool = Tool(
            function_declarations=[update_user_profile_declaration],
        )

        self.model = GenerativeModel(self.model_name, tools=[self.profile_tool])
        logger.info("Onboarding Agent ready!")

    async def chat(
        self, session_id: str, user_id: str, query: str, language: str = "en"
    ):
        logger.info(f"Agent starting chat for session_id: {session_id}")

        if session_id not in self.sessions:
            logger.info(f"Creating new chat session for session_id: {session_id}")
            current_date = datetime.date.today().strftime("%Y-%m-%d")
            initial_prompt = ONBOARDING_INSTRUCTION.format(
                language=language, current_date=current_date
            )
            self.sessions[session_id] = self.model.start_chat(
                 history=[
                    Content(role="user", parts=[Part.from_text(initial_prompt)]),
                    Content(role="model", parts=[Part.from_text("Okay, I am ready to be Wally. I will start the conversation by introducing myself and asking the first question, keeping the user's ID in mind for tool calls: " + user_id)]),
                ]
            )

        chat_session = self.sessions[session_id]

        logger.info(f"Sending message to Gemini for session_id: {session_id}")
        response = chat_session.send_message(query)
        logger.info(f"Received response from Gemini for session_id: {session_id}")

        onboarding_complete = False  # Default to False for each turn

        # FIX: Handle multipart responses properly
        response_parts = response.candidates[0].content.parts
        text_response = None

        # Find and execute the function call first
        for part in response_parts:
            if part.function_call:
                function_call = part.function_call
                logger.info(
                    f"Gemini requested function call: {function_call.name} for session_id: {session_id}"
                )

                args = {key: value for key, value in function_call.args.items()}
                if "user_id" not in args:
                    args["user_id"] = user_id

                logger.info(f"Executing function call with args: {args}")
                result = update_user_profile(**args)
                logger.info(f"Function call result: {result['status']}")

                # Check for the completion flag from the tool's result
                if result.get("onboarding_complete", False):
                    onboarding_complete = True
                    logger.info(f"Onboarding marked as complete for session_id: {session_id}")

                logger.info("Sending function response back to Gemini to get next question...")
                response = chat_session.send_message(
                    Part.from_function_response(name=function_call.name, response={"content": result})
                )
                logger.info("Received final response from Gemini after function call.")
                break  # Assume only one function call per turn

        # Find and return the text response
        for part in response.candidates[0].content.parts:
            if part.text:
                text_response = part.text
                break

        if text_response:
            logger.info(f"Returning text response for session_id: {session_id}")
            return {"text": text_response, "onboarding_complete": onboarding_complete}
        else:
            # This shouldn't happen with our prompt, but just in case
            logger.warning("No text part in response. Returning generic message.")
            return {"text": "Got it! Let's continue.", "onboarding_complete": onboarding_complete}


_agent = None


def get_onboarding_agent() -> "OnboardingAgent":
    global _agent
    if _agent is None:
        _agent = OnboardingAgent()
    return _agent
