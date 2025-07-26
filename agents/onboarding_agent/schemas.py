from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any

class RealEstateAsset(BaseModel):
    size_sqft: Optional[float] = Field(None, description="Size of the property in square feet.")
    purchase_price: Optional[float] = Field(None, description="The purchase price of the property.")
    purchase_date: Optional[str] = Field(None, description="The date the property was purchased.")

class GoldAsset(BaseModel):
    volume_g: float = Field(..., description="The volume of gold in grams.")
    purchase_price_per_g: Optional[float] = Field(None, description="The purchase price per gram.")
    purchase_date: Optional[str] = Field(None, description="The date the gold was purchased.")

class StockAsset(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol.")
    units_bought: float = Field(..., description="The number of units bought.")
    unit_price_purchase: Optional[float] = Field(None, description="The purchase price per unit.")
    exchange_date: Optional[str] = Field(None, description="The date of the transaction.")

class RecurringBill(BaseModel):
    name: str = Field(..., description="The name of the recurring bill (e.g., Netflix, Rent).")
    amount: float = Field(..., description="The amount of the bill.")
    due_date: Optional[int] = Field(None, description="The day of the month the bill is due.")

class UserAssets(BaseModel):
    real_estate: List[RealEstateAsset] = []
    gold: List[GoldAsset] = []
    stocks: List[StockAsset] = []
    # Add other asset types here in the future (e.g., crypto, art)
    other: Dict[str, Any] = {}

class UserProfile(BaseModel):
    """
    Represents a user's financial profile.
    """
    user_id: str = Field(..., description="The unique identifier for the user.")
    language: str = Field("en", description="The user's preferred language.")
    financial_goals: List[str] = Field([], description="A list of the user's financial goals.")
    spending_habits: Optional[str] = Field(None, description="A description of the user's spending habits (e.g., meticulous, casual, spontaneous).")
    risk_appetite: Optional[str] = Field(None, description="The user's appetite for financial risk (e.g., low, medium, high).")
    persona: Optional[str] = Field(None, description="The assigned persona for the user (e.g., Budgetor, Investor, Explorer).")
    has_invested_before: Optional[bool] = Field(None, description="Whether the user has invested in assets before.")
    investment_interests: List[str] = Field([], description="A list of asset types the user is interested in (e.g., real estate, stocks, crypto).")
    assets: UserAssets = Field(default_factory=UserAssets, description="A collection of the user's assets.")
    recurring_bills: List[RecurringBill] = Field([], description="A list of the user's recurring bills.")


class OnboardingRequest(BaseModel):
    """
    Represents a request to the onboarding chat API.
    """
    user_id: str = Field(..., description="The unique identifier for the user.")
    query: str = Field(..., description="The user's message.")
    language: str = Field("en", description="The language of the conversation.")
    session_id: str = Field(..., description="A unique identifier for the conversation session.") 