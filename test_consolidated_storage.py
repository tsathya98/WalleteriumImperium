#!/usr/bin/env python3
"""
Test script to verify consolidated storage approach for onboarding agent
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_consolidated_storage():
    """Test the consolidated storage functionality"""
    try:
        from app.services.firestore_service import FirestoreService
        from agents.onboarding_agent.agent import save_user_profile_data, get_complete_user_profile
        
        # Initialize Firestore service
        firestore_service = FirestoreService()
        await firestore_service.initialize()
        
        # Test data
        test_user_id = "test_consolidated_user_123"
        test_profile_data = {
            "persona": "Investor",
            "onboarding_complete": True,
            "financial_goals": ["Retirement planning", "Travel fund"],
            "spending_habits": "moderate",
            "risk_appetite": "medium",
            "investment_interests": ["stocks", "real_estate"],
            "has_invested_before": True,
            "recurring_bills": [
                {"name": "Rent", "amount": 25000, "due_date": 1},
                {"name": "Internet", "amount": 1500, "due_date": 15}
            ],
            "real_estate_assets": [
                {
                    "size_sqft": 1200,
                    "purchase_price": 5000000,
                    "purchase_date": "2022-03-15",
                    "location": "Mumbai"
                }
            ],
            "gold_assets": [
                {
                    "volume_g": 50,
                    "purchase_price_per_g": 5800,
                    "purchase_date": "2023-01-10"
                }
            ],
            "stock_assets": [
                {
                    "ticker": "RELIANCE",
                    "units_bought": 10,
                    "unit_price_purchase": 2800,
                    "exchange_date": "2023-06-20"
                }
            ],
            "vehicle_assets": [
                {
                    "type": "Car",
                    "model": "Honda City",
                    "purchase_price": 1200000,
                    "purchase_date": "2021-12-01"
                }
            ],
            "crypto_assets": [
                {
                    "symbol": "BTC",
                    "amount": 0.1,
                    "purchase_price": 5000000,
                    "purchase_date": "2023-11-15"
                }
            ]
        }
        
        logger.info("🔄 Testing consolidated storage...")
        
        # Test saving profile
        save_result = save_user_profile_data(firestore_service, test_user_id, test_profile_data)
        logger.info(f"Save result: {save_result}")
        
        if save_result["status"] != "success":
            logger.error("❌ Failed to save profile")
            return False
            
        # Test retrieving profile
        get_result = get_complete_user_profile(firestore_service, test_user_id)
        logger.info(f"Get result status: {get_result['status']}")
        
        if get_result["status"] != "success":
            logger.error("❌ Failed to retrieve profile")
            return False
            
        profile = get_result["profile"]
        
        # Verify all data is present
        required_fields = [
            "uid", "persona", "onboarding_completed", "financial_goals",
            "spending_habits", "risk_appetite", "investment_interests",
            "has_invested_before", "recurring_bills", "real_estate_assets",
            "gold_assets", "stock_assets", "vehicle_assets", "crypto_assets"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in profile:
                missing_fields.append(field)
                
        if missing_fields:
            logger.error(f"❌ Missing fields in retrieved profile: {missing_fields}")
            return False
            
        # Verify assets data integrity
        assert len(profile["real_estate_assets"]) == 1
        assert len(profile["gold_assets"]) == 1
        assert len(profile["stock_assets"]) == 1
        assert len(profile["vehicle_assets"]) == 1
        assert len(profile["crypto_assets"]) == 1
        assert len(profile["recurring_bills"]) == 2
        
        # Verify specific asset data
        real_estate = profile["real_estate_assets"][0]
        assert real_estate["size_sqft"] == 1200
        assert real_estate["location"] == "Mumbai"
        
        gold = profile["gold_assets"][0]
        assert gold["volume_g"] == 50
        assert gold["purchase_price_per_g"] == 5800
        
        logger.info("✅ All data integrity checks passed!")
        logger.info("✅ Consolidated storage is working correctly!")
        
        # Log summary
        logger.info(f"""
📊 Profile Summary for {test_user_id}:
- Persona: {profile['persona']}
- Financial Goals: {len(profile['financial_goals'])} goals
- Real Estate: {len(profile['real_estate_assets'])} properties
- Gold: {len(profile['gold_assets'])} holdings
- Stocks: {len(profile['stock_assets'])} positions
- Vehicles: {len(profile['vehicle_assets'])} vehicles
- Crypto: {len(profile['crypto_assets'])} holdings
- Bills: {len(profile['recurring_bills'])} recurring bills
""")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_consolidated_storage())
    if success:
        print("🎉 Test completed successfully!")
    else:
        print("💥 Test failed!") 