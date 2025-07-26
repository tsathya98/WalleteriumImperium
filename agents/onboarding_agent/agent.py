# agents/onboarding_agent/agent.py

from google.adk.agents import Agent
from google.adk.tools import tool
from typing import Dict, Any, List

from .prompts import ONBOARDING_INSTRUCTION
from .schemas import (
    UserProfile,
    RealEstateAsset,
    GoldAsset,
    StockAsset,
    RecurringBill,
)

# In-memory "database" for user profiles.
# In a production environment, this would be replaced with a real database like Firestore.
user_profiles: Dict[str, UserProfile] = {}


@tool
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
) -> Dict[str, Any]:
    """
    Creates or updates a user's profile in the database.
    Use this tool to save the user's information as you gather it.
    You can add assets and recurring bills by providing a list of their details.
    """
    if user_id not in user_profiles:
        user_profiles[user_id] = UserProfile(user_id=user_id, language=language)

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

    return {"status": "success", "user_id": user_id, "profile": profile.dict()}


onboarding_agent = Agent(
    name="onboarding_agent",
    model="gemini-2.5-flash",
    description="A conversational agent for onboarding users and creating financial profiles.",
    instruction=ONBOARDING_INSTRUCTION,
    tools=[update_user_profile],
)
