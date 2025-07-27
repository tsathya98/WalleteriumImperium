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
import random

from .prompts import ONBOARDING_INSTRUCTION
from .schemas import UserProfile, RealEstateAsset, GoldAsset, StockAsset, RecurringBill
from app.core.config import get_settings
from app.services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)


async def update_user_profile(
    firestore_service: "FirestoreService",
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
    Creates or updates a user's profile and assets in Firestore.
    """
    logger.info(f"Updating profile and assets for user_id: {user_id} in Firestore.")

    # 1. Save/Update the main user profile in 'wallet_user_collection'
    user_doc_ref = firestore_service.client.collection("wallet_user_collection").document(user_id)

    user_data = {
        "uid": user_id,
        "last_seen": datetime.datetime.now(datetime.timezone.utc),
    }
    if persona:
        user_data["persona"] = persona
    if onboarding_complete is not None:
        user_data["onboarding_completed"] = onboarding_complete

    # Using merge=True to not overwrite existing fields like email, display_name etc.
    await user_doc_ref.set(user_data, merge=True)
    logger.info(f"Updated wallet_user_collection for user {user_id}")

    # 2. Save each asset to 'user_assets' collection
    assets_collection_ref = user_doc_ref.collection("user_assets")

    # Helper to generate a random hex color
    def get_random_color():
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    if real_estate_assets:
        for asset_data in real_estate_assets:
            asset = RealEstateAsset(**asset_data)
            asset_doc = {
                "user_id": user_id,
                "account_name": f"Real Estate {asset.size_sqft} sqft",
                "account_type": "Real Estate",
                "current_balance": asset.purchase_price,
                "created_at": datetime.datetime.fromisoformat(asset.purchase_date).replace(tzinfo=datetime.timezone.utc),
                "account_color": get_random_color(),
                "details": asset.dict()
            }
            await assets_collection_ref.add(asset_doc)
            logger.info(f"Saved Real Estate asset for user {user_id}")

    if gold_assets:
        for asset_data in gold_assets:
            asset = GoldAsset(**asset_data)
            asset_doc = {
                "user_id": user_id,
                "account_name": f"Gold {asset.volume_g}g",
                "account_type": "Gold",
                "current_balance": asset.volume_g * asset.purchase_price_per_g if asset.purchase_price_per_g else 0,
                "created_at": datetime.datetime.fromisoformat(asset.purchase_date).replace(tzinfo=datetime.timezone.utc),
                "account_color": get_random_color(),
                "details": asset.dict()
            }
            await assets_collection_ref.add(asset_doc)
            logger.info(f"Saved Gold asset for user {user_id}")

    if stock_assets:
        for asset_data in stock_assets:
            asset = StockAsset(**asset_data)
            asset_doc = {
                "user_id": user_id,
                "account_name": f"Stock: {asset.ticker}",
                "account_type": "Stocks",
                "current_balance": asset.units_bought * asset.unit_price_purchase,
                "created_at": datetime.datetime.fromisoformat(asset.exchange_date).replace(tzinfo=datetime.timezone.utc),
                "account_color": get_random_color(),
                "details": asset.dict()
            }
            await assets_collection_ref.add(asset_doc)
            logger.info(f"Saved Stock asset for user {user_id}")

    # Note: Recurring bills are not saved to 'user_assets' as per the request.

    logger.info(
        f"Profile and assets for {user_id} updated. Onboarding complete: {onboarding_complete}"
    )
    return {
        "status": "success",
        "user_id": user_id,
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
        self,
        firestore_service: "FirestoreService",
        session_id: str,
        user_id: str,
        query: str,
        language: str = "en",
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
                    Content(role="model", parts=[Part.from_text("Okay, I am Wally. I will now start the conversation with the user (ID: " + user_id + ") by introducing myself and asking a fun, open-ended question about their spending habits.")] ),
                ]
            )

        chat_session = self.sessions[session_id]
        onboarding_complete = False

        # Start the agentic loop
        response = chat_session.send_message(query)
        
        while True:
            function_call = None
            # Check all parts for a function call
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break
            
            if function_call:
                logger.info(f"Gemini requested function call: {function_call.name}")

                args = {key: value for key, value in function_call.args.items()}
                if "user_id" not in args:
                    args["user_id"] = user_id

                logger.info(f"Executing function call with args: {args}")
                result = await update_user_profile(firestore_service=firestore_service, **args)
                logger.info(f"Function call result: {result['status']}")

                if result.get("onboarding_complete", False):
                    onboarding_complete = True
                    logger.info("Onboarding complete flag received from tool.")
                
                logger.info("Sending tool result back to Gemini...")
                response = chat_session.send_message(
                    Part.from_function_response(name=function_call.name, response={"content": result})
                )
            else:
                # If there's no more function calls, the conversation is done for this turn
                logger.info("No more function calls from Gemini. Returning text response.")
                break

        # By the end of the loop, response is guaranteed to be a text-only response
        return {"text": response.text, "onboarding_complete": onboarding_complete}


_agent = None


def get_onboarding_agent() -> "OnboardingAgent":
    global _agent
    if _agent is None:
        _agent = OnboardingAgent()
    return _agent
