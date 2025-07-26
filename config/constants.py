"""
Centralized constants for the application
"""

# List of allowed transaction categories for AI processing
# This list serves as the single source of truth for categorization.
TRANSACTION_CATEGORIES = [
    # Expenses
    "Groceries",
    "Restaurant, fast-food",
    "Clothes & shoes",
    "Jewels & accessories",
    "Health & beauty",
    "Gifts",
    "Kids, toys",
    "Pharmacy",
    "Doctor",
    "Rent",
    "Mortgage",
    "Maintenance, repairs",
    "Electricity & Gas",
    "Public transport, Taxi",

    # Investments & Savings
    "Investment: Realty",
    "Investment: Vehicles",
    "Investment: Financial investments / Savings",
    "Investment: House/land/etc.",

    # Leisure & Entertainment
    "Vacation",
    "Software, apps, games (onetime/subscription)",
    "Subscriptions: TV, streaming (entertainment)",

    # Subscriptions & Bills
    "Subscription: Phone, Internet recharge",
    "Insurances",
    "Loans, Interests",

    # Transportation
    "Fuel",
    "Parking",

    # Income
    "Income: Fixed (recurring)",
    "Income: Variable",
    
    # Other
    "Other"
]

# Vendor type classifications for AI decision making
VENDOR_TYPES = {
    "RESTAURANT": "Places where you order prepared food (restaurants, cafes, fast food)",
    "SUPERMARKET": "Places where you buy individual items (grocery stores, pharmacies, hardware stores)",
    "SERVICE": "Service providers (utilities, repairs, subscriptions)",
    "OTHER": "Everything else"
}
