# scripts/populate_investor_profile.py

from datetime import datetime
from google.cloud import firestore

def save_user_profile_data(
    firestore_client: firestore.Client,
    user_id: str,
    profile_data: dict
):
    """Save complete user profile data to Firestore, same as in agent.py"""
    try:
        user_doc_ref = firestore_client.collection("wallet_user_collection").document(user_id)

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
            "recurring_bills": profile_data.get("recurring_bills", [])
        }

        user_doc_ref.set(user_data, merge=True)
        print(f"✅ Saved main profile for user {user_id}")

        assets_collection_ref = user_doc_ref.collection("user_assets")
        asset_types = ['real_estate_assets', 'gold_assets', 'stock_assets', 'vehicle_assets', 'crypto_assets']
        
        for asset_type in asset_types:
            assets = profile_data.get(asset_type, [])
            if assets:
                for asset in assets:
                    asset_doc = {
                        "user_id": user_id,
                        "asset_type": asset_type.replace('_assets', ''),
                        "data": asset,
                        "created_at": datetime.now().isoformat()
                    }
                    assets_collection_ref.add(asset_doc)
                    print(f"✅ Saved asset of type {asset_type} for user {user_id}")
        
        print(f"🎉 Complete profile saved for user {user_id}")
        return {"status": "success", "message": "Profile saved successfully"}

    except Exception as e:
        print(f"❌ Error saving profile for user {user_id}: {e}")
        return {"status": "error", "message": str(e)}

def populate_profiles():
    """Populates specific user profiles in Firestore."""
    
    try:
        client = firestore.Client(project="walleterium")
    except Exception as e:
        print("Could not create Firestore client. Make sure Google Cloud credentials are set up.")
        print(e)
        return

    # User 1: Investor Profile
    user_id_1 = "111"
    profile_data_1 = {
        "persona": "Investor",
        "onboarding_complete": True,
        "financial_goals": ["Travel to Europe"],
        "spending_habits": "moderate",
        "risk_appetite": "medium",
        "investment_interests": ["stocks", "mutual_funds"],
        "has_invested_before": True,
        "recurring_bills": [
            {
                "name": "Rent",
                "amount": 25500,
                "due_date": 1
            }
        ],
        "real_estate_assets": [],
        "gold_assets": [],
        "stock_assets": [],
        "vehicle_assets": [],
        "crypto_assets": [],
    }

    print(f"🚀 Populating profile for user_id: {user_id_1}")
    save_user_profile_data(client, user_id_1, profile_data_1)
    
    # User 2: Budgetor Profile
    user_id_2 = "1111"
    profile_data_2 = {
        "persona": "Budgetor",
        "onboarding_complete": True,
        "financial_goals": ["Save for a down payment on a car", "Build an emergency fund"],
        "spending_habits": "frugal",
        "risk_appetite": "low",
        "investment_interests": ["fixed_deposits", "savings_accounts"],
        "has_invested_before": False,
        "recurring_bills": [
            { "name": "Phone Bill", "amount": 500, "due_date": 15 },
            { "name": "Internet Bill", "amount": 800, "due_date": 10 }
        ],
        "real_estate_assets": [],
        "gold_assets": [],
        "stock_assets": [],
        "vehicle_assets": [],
        "crypto_assets": [],
    }
    
    print(f"🚀 Populating profile for user_id: {user_id_2}")
    save_user_profile_data(client, user_id_2, profile_data_2)
    
    print("✅ Done.")

if __name__ == "__main__":
    populate_profiles() 