"""
Receipt Analysis service for Project Raseed
MVP: Returns realistic JSON stubs, will integrate real Vertex AI later
"""

import json
import asyncio
import random
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.logging import get_logger, log_async_performance
from app.models import ReceiptAnalysis, TransactionType, ImportanceLevel, SubscriptionDetails, WarrantyDetails

settings = get_settings()
logger = get_logger(__name__)


class ReceiptAnalysisService:
    """MVP Receipt Analysis service with realistic JSON stubs"""
    
    def __init__(self):
        self._initialized = False
        # Indian market data for realistic receipts
        self.indian_stores = [
            {"name": "BigBasket", "category": "Groceries"},
            {"name": "Swiggy", "category": "Food Delivery"},
            {"name": "Reliance Smart", "category": "Groceries"},
            {"name": "Spencer's", "category": "Groceries"},
            {"name": "D-Mart", "category": "Groceries"},
            {"name": "Zomato", "category": "Food Delivery"},
            {"name": "Amazon India", "category": "Online Shopping"},
            {"name": "Flipkart", "category": "Online Shopping"},
            {"name": "Uber", "category": "Transportation"},
            {"name": "Ola Cabs", "category": "Transportation"},
            {"name": "BookMyShow", "category": "Entertainment"},
            {"name": "PayTM Mall", "category": "Online Shopping"},
            {"name": "Myntra", "category": "Fashion"},
            {"name": "Nykaa", "category": "Beauty"},
            {"name": "Domino's Pizza", "category": "Food Delivery"},
            {"name": "McDonald's", "category": "Dining"},
            {"name": "Starbucks", "category": "Dining"},
            {"name": "Café Coffee Day", "category": "Dining"},
            {"name": "PVR Cinemas", "category": "Entertainment"},
            {"name": "More Supermarket", "category": "Groceries"},
            {"name": "FabIndia", "category": "Fashion"},
            {"name": "Lifestyle", "category": "Fashion"},
            {"name": "Westside", "category": "Fashion"},
            {"name": "Croma", "category": "Electronics"},
            {"name": "Vijay Sales", "category": "Electronics"}
        ]
        
        self.subscription_services = [
            {"name": "Netflix", "recurrence": "monthly", "amount_range": (199, 799)},
            {"name": "Amazon Prime", "recurrence": "annually", "amount_range": (999, 1499)},
            {"name": "Disney+ Hotstar", "recurrence": "monthly", "amount_range": (299, 899)},
            {"name": "Spotify Premium", "recurrence": "monthly", "amount_range": (119, 189)},
            {"name": "Zomato Pro", "recurrence": "monthly", "amount_range": (59, 99)},
            {"name": "YouTube Premium", "recurrence": "monthly", "amount_range": (129, 199)},
            {"name": "Swiggy One", "recurrence": "monthly", "amount_range": (99, 149)}
        ]
        
        self.warranty_categories = [
            "Electronics", "Appliances", "Fashion", "Home & Garden"
        ]
    
    async def initialize(self):
        """Initialize service"""
        try:
            self._initialized = True
            logger.info("✅ Receipt Analysis service initialized (MVP mode)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Receipt Analysis service: {e}")
            raise
    
    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Receipt Analysis service not initialized")
    
    @log_async_performance(logger)
    async def process_receipt_image(self, image_base64: str, user_id: str = None) -> ReceiptAnalysis:
        """
        Process receipt image and return analysis
        MVP: Returns realistic mock data, will integrate real AI later
        """
        self._ensure_initialized()
        
        try:
            # Create receipt ID
            receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"
            
            logger.info("Starting receipt analysis (MVP)", extra={
                "receipt_id": receipt_id,
                "user_id": user_id,
                "mode": "mvp_stub"
            })
            
            # Simulate processing time
            processing_start = datetime.utcnow()
            await asyncio.sleep(random.uniform(1, 2))  # 1-2 seconds for MVP
            
            # Generate realistic receipt data
            receipt_data = await self._generate_realistic_receipt(receipt_id)
            
            processing_time = (datetime.utcnow() - processing_start).total_seconds()
            receipt_data.processing_time = processing_time
            
            logger.info("Receipt analysis completed (MVP)", extra={
                "receipt_id": receipt_id,
                "processing_time": processing_time,
                "place": receipt_data.place,
                "amount": receipt_data.amount
            })
            
            return receipt_data
            
        except Exception as e:
            logger.error("Receipt analysis failed", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise
    
    async def _generate_realistic_receipt(self, receipt_id: str) -> ReceiptAnalysis:
        """Generate realistic receipt data for Indian market"""
        
        # Decide receipt type
        receipt_types = ["regular", "subscription", "warranty", "high_value"]
        receipt_type = random.choices(
            receipt_types, 
            weights=[70, 15, 10, 5]  # Most are regular receipts
        )[0]
        
        if receipt_type == "subscription":
            return await self._generate_subscription_receipt(receipt_id)
        elif receipt_type == "warranty":
            return await self._generate_warranty_receipt(receipt_id)
        elif receipt_type == "high_value":
            return await self._generate_high_value_receipt(receipt_id)
        else:
            return await self._generate_regular_receipt(receipt_id)
    
    async def _generate_regular_receipt(self, receipt_id: str) -> ReceiptAnalysis:
        """Generate regular transaction receipt"""
        store = random.choice(self.indian_stores)
        
        # Amount based on category
        amount_ranges = {
            "Groceries": (150, 2500),
            "Food Delivery": (200, 800),
            "Online Shopping": (500, 5000),
            "Transportation": (50, 500),
            "Entertainment": (100, 800),
            "Dining": (300, 1500),
            "Fashion": (800, 4000),
            "Beauty": (200, 1200),
            "Electronics": (2000, 25000)
        }
        
        min_amt, max_amt = amount_ranges.get(store["category"], (100, 1000))
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        # Generate timestamp (last 30 days)
        days_back = random.randint(0, 30)
        hours_back = random.randint(0, 23)
        transaction_time = datetime.utcnow() - timedelta(days=days_back, hours=hours_back)
        
        # Determine transaction type (most are debits)
        transaction_type = random.choices(
            [TransactionType.DEBIT, TransactionType.CREDIT],
            weights=[90, 10]
        )[0]
        
        # Importance based on amount
        if amount > 5000:
            importance = ImportanceLevel.HIGH
        elif amount > 1000:
            importance = ImportanceLevel.MEDIUM
        else:
            importance = ImportanceLevel.LOW
        
        return ReceiptAnalysis(
            receipt_id=receipt_id,
            place=store["name"],
            category=store["category"],
            time=transaction_time.isoformat() + "Z",
            amount=amount,
            transactionType=transaction_type,
            importance=importance,
            description=f"Transaction at {store['name']}",
            warranty=False,
            recurring=False
        )
    
    async def _generate_subscription_receipt(self, receipt_id: str) -> ReceiptAnalysis:
        """Generate subscription receipt"""
        service = random.choice(self.subscription_services)
        amount = random.uniform(service["amount_range"][0], service["amount_range"][1])
        
        # Next billing date
        if service["recurrence"] == "monthly":
            next_due = datetime.utcnow() + timedelta(days=30)
        else:  # annually
            next_due = datetime.utcnow() + timedelta(days=365)
        
        transaction_time = datetime.utcnow() - timedelta(days=random.randint(0, 5))
        
        subscription_details = SubscriptionDetails(
            name=service["name"],
            recurrence=service["recurrence"],
            nextDueDate=next_due.isoformat() + "Z"
        )
        
        return ReceiptAnalysis(
            receipt_id=receipt_id,
            place=service["name"],
            category="Subscription",
            time=transaction_time.isoformat() + "Z",
            amount=round(amount, 2),
            transactionType=TransactionType.DEBIT,
            importance=ImportanceLevel.MEDIUM,
            description=f"{service['name']} subscription renewal",
            warranty=False,
            recurring=True,
            subscription=subscription_details
        )
    
    async def _generate_warranty_receipt(self, receipt_id: str) -> ReceiptAnalysis:
        """Generate receipt with warranty"""
        category = random.choice(self.warranty_categories)
        
        # Find store that sells this category
        stores_for_category = [
            store for store in self.indian_stores 
            if store["category"] in ["Electronics", "Fashion", "Online Shopping"]
        ]
        store = random.choice(stores_for_category)
        
        amount = random.uniform(5000, 25000)  # Higher amounts for warranty items
        transaction_time = datetime.utcnow() - timedelta(days=random.randint(0, 10))
        
        # Warranty expires in 1-2 years
        warranty_expiry = transaction_time + timedelta(days=random.randint(365, 730))
        
        warranty_details = WarrantyDetails(
            validUntil=warranty_expiry.isoformat() + "Z",
            provider=store["name"],
            termsURL=f"https://{store['name'].lower().replace(' ', '')}.com/warranty"
        )
        
        return ReceiptAnalysis(
            receipt_id=receipt_id,
            place=store["name"],
            category=category,
            time=transaction_time.isoformat() + "Z",
            amount=round(amount, 2),
            transactionType=TransactionType.DEBIT,
            importance=ImportanceLevel.HIGH,
            description=f"{category} purchase with warranty",
            warranty=True,
            recurring=False,
            warrantyDetails=warranty_details
        )
    
    async def _generate_high_value_receipt(self, receipt_id: str) -> ReceiptAnalysis:
        """Generate high-value transaction"""
        high_value_stores = [
            {"name": "Apple Store", "category": "Electronics"},
            {"name": "Samsung Store", "category": "Electronics"},
            {"name": "Tanishq", "category": "Jewelry"},
            {"name": "Kalyan Jewellers", "category": "Jewelry"},
            {"name": "Westside", "category": "Fashion"},
            {"name": "Lifestyle", "category": "Fashion"}
        ]
        
        store = random.choice(high_value_stores)
        amount = random.uniform(15000, 75000)  # High-value transactions
        transaction_time = datetime.utcnow() - timedelta(days=random.randint(0, 7))
        
        return ReceiptAnalysis(
            receipt_id=receipt_id,
            place=store["name"],
            category=store["category"],
            time=transaction_time.isoformat() + "Z",
            amount=round(amount, 2),
            transactionType=TransactionType.DEBIT,
            importance=ImportanceLevel.HIGH,
            description=f"High-value purchase at {store['name']}",
            warranty=random.choice([True, False]),
            recurring=False
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for Receipt Analysis service"""
        try:
            if not self._initialized:
                return {"status": "unhealthy", "error": "Not initialized"}
            
            return {
                "status": "healthy",
                "mode": "mvp",
                "stores_count": len(self.indian_stores),
                "subscription_services": len(self.subscription_services)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance (backward compatibility)
vertex_ai_service = ReceiptAnalysisService()