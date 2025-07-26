"""
Centralized constants for the application
"""

# List of allowed transaction categories for AI processing
# This list serves as the single source of truth for categorization.
TRANSACTION_CATEGORIES = [
    # Daily Expenses
    "Groceries",
    "Restaurant, fast-food",
    "Clothes & shoes",
    "Jewels & accessories",
    "Health & beauty",
    "Gifts",
    "Kids, toys",
    "Pharmacy",
    "Doctor",
    
    # Housing & Utilities
    "Rent",
    "Mortgage",
    "Maintenance, repairs",
    "Electricity & Gas",
    
    # Transportation
    "Public transport, Taxi",
    "Fuel",
    "Parking",
    
    # Subscriptions & Services
    "Subscription: Phone, Internet recharge",
    "Subscriptions: TV, streaming (entertainment)",
    "Software, apps, games (onetime/subscription)",
    "Insurances",
    "Loans, Interests",
    
    # Investments
    "Investment: Realty",
    "Investment: Vehicles", 
    "Investment: Financial investments / Savings",
    "Investment: House/land/etc.",
    
    # Leisure
    "Vacation",
    
    # Income
    "Income: Fixed (recurring)",
    "Income: Variable",
    
    # Fallback
    "Other"
]

# Vendor type classifications for AI decision making
VENDOR_TYPES = {
    "RESTAURANT": "Places where you order prepared food (restaurants, cafes, fast food)",
    "SUPERMARKET": "Places where you buy individual items (grocery stores, pharmacies, hardware stores)",
    "SERVICE": "Service providers (utilities, repairs, subscriptions)",
    "OTHER": "Everything else"
}
