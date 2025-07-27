"""
Script to populate 100 realistic dummy transactions in Firestore
Based on the receipt scanner format
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from google.cloud import firestore

# Realistic business data
RESTAURANTS = [
    {"name": "El Chalan Restaurant", "type": "peruvian", "avg_price": 35},
    {"name": "McDonald's", "type": "fast_food", "avg_price": 12},
    {"name": "Olive Garden", "type": "italian", "avg_price": 28},
    {"name": "Starbucks", "type": "cafe", "avg_price": 8},
    {"name": "Subway", "type": "sandwich", "avg_price": 10},
    {"name": "Chipotle", "type": "mexican", "avg_price": 15},
    {"name": "Pizza Hut", "type": "pizza", "avg_price": 22},
    {"name": "Domino's Pizza", "type": "pizza", "avg_price": 18},
    {"name": "Burger King", "type": "fast_food", "avg_price": 11},
    {"name": "KFC", "type": "fast_food", "avg_price": 14},
]

GROCERY_STORES = [
    {"name": "Walmart", "avg_price": 85},
    {"name": "Target", "avg_price": 65},
    {"name": "Kroger", "avg_price": 72},
    {"name": "Safeway", "avg_price": 68},
    {"name": "Whole Foods", "avg_price": 95},
    {"name": "Costco", "avg_price": 145},
    {"name": "Publix", "avg_price": 58},
]

GAS_STATIONS = [
    {"name": "Shell", "avg_price": 45},
    {"name": "Exxon", "avg_price": 48},
    {"name": "BP", "avg_price": 44},
    {"name": "Chevron", "avg_price": 46},
    {"name": "Texaco", "avg_price": 43},
]

PHARMACIES = [
    {"name": "CVS Pharmacy", "avg_price": 35},
    {"name": "Walgreens", "avg_price": 32},
    {"name": "Rite Aid", "avg_price": 28},
]

CLOTHING_STORES = [
    {"name": "Target", "avg_price": 85},
    {"name": "H&M", "avg_price": 55},
    {"name": "Zara", "avg_price": 120},
    {"name": "Nike Store", "avg_price": 95},
    {"name": "Adidas", "avg_price": 88},
]

# Food items for restaurants
RESTAURANT_ITEMS = {
    "peruvian": [
        {"name": "Ceviche", "price": 15.00, "desc": "Fresh fish ceviche with onions"},
        {"name": "Lomo Saltado", "price": 18.50, "desc": "Beef stir-fry with potatoes"},
        {"name": "Causa de Pollo", "price": 12.00, "desc": "Peruvian potato dish with chicken"},
        {"name": "Anticuchos", "price": 14.00, "desc": "Grilled beef heart skewers"},
        {"name": "Pisco Sour", "price": 8.00, "desc": "Traditional Peruvian cocktail"},
    ],
    "fast_food": [
        {"name": "Big Mac", "price": 5.99, "desc": "Classic burger with special sauce"},
        {"name": "French Fries", "price": 2.99, "desc": "Crispy golden fries"},
        {"name": "Chicken McNuggets", "price": 4.99, "desc": "Crispy chicken pieces"},
        {"name": "Coca Cola", "price": 1.99, "desc": "Refreshing soda drink"},
        {"name": "Apple Pie", "price": 1.29, "desc": "Warm apple pie dessert"},
    ],
    "italian": [
        {"name": "Chicken Alfredo", "price": 16.99, "desc": "Pasta with creamy alfredo sauce"},
        {"name": "Lasagna", "price": 14.99, "desc": "Layered pasta with meat sauce"},
        {"name": "Caesar Salad", "price": 8.99, "desc": "Fresh romaine with caesar dressing"},
        {"name": "Breadsticks", "price": 5.99, "desc": "Unlimited garlic breadsticks"},
        {"name": "Tiramisu", "price": 6.99, "desc": "Classic Italian dessert"},
    ],
    "cafe": [
        {"name": "Grande Latte", "price": 4.65, "desc": "Espresso with steamed milk"},
        {"name": "Croissant", "price": 2.95, "desc": "Buttery pastry"},
        {"name": "Blueberry Muffin", "price": 2.45, "desc": "Fresh baked muffin"},
        {"name": "Americano", "price": 2.65, "desc": "Espresso with hot water"},
    ],
    "sandwich": [
        {"name": "Turkey Breast", "price": 8.99, "desc": "Fresh turkey with vegetables"},
        {"name": "Italian BMT", "price": 9.49, "desc": "Salami, pepperoni, and ham"},
        {"name": "Veggie Delite", "price": 6.99, "desc": "Fresh vegetables and cheese"},
        {"name": "Chips", "price": 1.50, "desc": "Crispy potato chips"},
        {"name": "Cookie", "price": 1.00, "desc": "Chocolate chip cookie"},
    ],
    "mexican": [
        {"name": "Burrito Bowl", "price": 8.95, "desc": "Rice, beans, meat, and toppings"},
        {"name": "Chicken Burrito", "price": 8.25, "desc": "Grilled chicken in flour tortilla"},
        {"name": "Guacamole", "price": 2.60, "desc": "Fresh made guacamole"},
        {"name": "Chips", "price": 1.45, "desc": "Crispy tortilla chips"},
    ],
    "pizza": [
        {"name": "Pepperoni Pizza", "price": 12.99, "desc": "Classic pepperoni pizza"},
        {"name": "Margherita Pizza", "price": 11.99, "desc": "Fresh mozzarella and basil"},
        {"name": "Wings", "price": 8.99, "desc": "Buffalo chicken wings"},
        {"name": "Garlic Bread", "price": 4.99, "desc": "Toasted bread with garlic"},
    ],
}

# Grocery items
GROCERY_ITEMS = [
    {"name": "Bananas", "price": 1.98, "desc": "Fresh bananas per lb"},
    {"name": "Bread", "price": 2.50, "desc": "Whole wheat bread loaf"},
    {"name": "Milk", "price": 3.49, "desc": "1 gallon whole milk"},
    {"name": "Eggs", "price": 2.99, "desc": "Large eggs dozen"},
    {"name": "Chicken Breast", "price": 5.99, "desc": "Boneless chicken breast per lb"},
    {"name": "Rice", "price": 4.99, "desc": "Long grain white rice 5lb"},
    {"name": "Apples", "price": 3.99, "desc": "Red delicious apples 3lb bag"},
    {"name": "Yogurt", "price": 4.49, "desc": "Greek yogurt 32oz"},
    {"name": "Cheese", "price": 4.99, "desc": "Cheddar cheese block"},
    {"name": "Pasta", "price": 1.99, "desc": "Spaghetti pasta 1lb"},
    {"name": "Tomatoes", "price": 2.99, "desc": "Fresh tomatoes per lb"},
    {"name": "Orange Juice", "price": 3.99, "desc": "100% orange juice 64oz"},
]

# Pharmacy items
PHARMACY_ITEMS = [
    {"name": "Advil", "price": 8.99, "desc": "Pain reliever 200mg 100ct"},
    {"name": "Vitamins", "price": 12.99, "desc": "Daily multivitamin 60ct"},
    {"name": "Band-Aids", "price": 4.99, "desc": "Adhesive bandages 40ct"},
    {"name": "Shampoo", "price": 6.99, "desc": "Daily shampoo 12oz"},
    {"name": "Toothpaste", "price": 3.99, "desc": "Fluoride toothpaste 6oz"},
    {"name": "Soap", "price": 2.99, "desc": "Body wash 16oz"},
]

# Clothing items
CLOTHING_ITEMS = [
    {"name": "T-Shirt", "price": 15.99, "desc": "Cotton crew neck t-shirt"},
    {"name": "Jeans", "price": 49.99, "desc": "Classic fit blue jeans"},
    {"name": "Running Shoes", "price": 89.99, "desc": "Athletic running shoes"},
    {"name": "Hoodie", "price": 39.99, "desc": "Pullover hoodie sweatshirt"},
    {"name": "Socks", "price": 9.99, "desc": "Cotton crew socks 6-pack"},
    {"name": "Baseball Cap", "price": 19.99, "desc": "Adjustable baseball cap"},
]

def generate_receipt_data() -> Dict[str, Any]:
    """Generate a realistic receipt transaction"""
    
    # Choose transaction type (90% debit, 10% credit for returns)
    transaction_type = "debit" if random.random() < 0.9 else "credit"
    
    # Choose business type
    business_types = ["restaurant", "grocery", "gas", "pharmacy", "clothing"]
    business_type = random.choices(
        business_types, 
        weights=[40, 25, 15, 10, 10],  # More restaurants, less specialty stores
        k=1
    )[0]
    
    # Generate based on business type
    if business_type == "restaurant":
        return generate_restaurant_receipt(transaction_type)
    elif business_type == "grocery":
        return generate_grocery_receipt(transaction_type)
    elif business_type == "gas":
        return generate_gas_receipt(transaction_type)
    elif business_type == "pharmacy":
        return generate_pharmacy_receipt(transaction_type)
    else:
        return generate_clothing_receipt(transaction_type)

def generate_restaurant_receipt(transaction_type: str) -> Dict[str, Any]:
    """Generate restaurant receipt"""
    restaurant = random.choice(RESTAURANTS)
    restaurant_type = restaurant["type"]
    
    # Generate 1-4 items
    num_items = random.randint(1, 4)
    items = []
    total_amount = 0
    
    available_items = RESTAURANT_ITEMS.get(restaurant_type, RESTAURANT_ITEMS["fast_food"])
    selected_items = random.sample(available_items, min(num_items, len(available_items)))
    
    for item in selected_items:
        quantity = random.randint(1, 2)
        unit_price = item["price"] + random.uniform(-1, 1)  # Add some variation
        unit_price = max(0.99, round(unit_price, 2))
        total_price = round(quantity * unit_price, 2)
        total_amount += total_price
        
        items.append({
            "name": item["name"],
            "quantity": float(quantity),
            "unit_price": unit_price,
            "total_price": total_price,
            "category": "Restaurant, fast-food",
            "description": item["desc"],
            "warranty": None,
            "recurring": None
        })
    
    # Add tax and tip
    tax = round(total_amount * 0.08, 2)
    tip = round(total_amount * random.uniform(0.15, 0.22), 2) if transaction_type == "debit" else 0
    total_amount = round(total_amount + tax + tip, 2)
    
    if transaction_type == "credit":
        total_amount = -abs(total_amount)  # Negative for returns
    
    return {
        "receipt_id": str(uuid.uuid4()),
        "place": restaurant["name"],
        "time": generate_random_timestamp().isoformat() + "Z",
        "amount": total_amount,
        "transactionType": transaction_type,
        "category": "Restaurant, fast-food",
        "description": f"{'Return from' if transaction_type == 'credit' else 'Meal at'} {restaurant['name']}",
        "importance": random.choice(["low", "medium", "high"]),
        "warranty": None,
        "recurring": None,
        "items": items,
        "metadata": {
            "vendor_type": "RESTAURANT",
            "confidence": random.choice(["high", "medium"]),
            "processing_time_seconds": round(random.uniform(8, 25), 3),
            "model_version": "gemini-2.5-flash"
        }
    }

def generate_grocery_receipt(transaction_type: str) -> Dict[str, Any]:
    """Generate grocery store receipt"""
    store = random.choice(GROCERY_STORES)
    
    # Generate 3-8 items
    num_items = random.randint(3, 8)
    items = []
    total_amount = 0
    
    selected_items = random.sample(GROCERY_ITEMS, min(num_items, len(GROCERY_ITEMS)))
    
    for item in selected_items:
        quantity = random.randint(1, 3)
        unit_price = item["price"] + random.uniform(-0.5, 0.5)
        unit_price = max(0.99, round(unit_price, 2))
        total_price = round(quantity * unit_price, 2)
        total_amount += total_price
        
        items.append({
            "name": item["name"],
            "quantity": float(quantity),
            "unit_price": unit_price,
            "total_price": total_price,
            "category": "Groceries",
            "description": item["desc"],
            "warranty": None,
            "recurring": None
        })
    
    # Add tax
    tax = round(total_amount * 0.06, 2)
    total_amount = round(total_amount + tax, 2)
    
    if transaction_type == "credit":
        total_amount = -abs(total_amount)
    
    return {
        "receipt_id": str(uuid.uuid4()),
        "place": store["name"],
        "time": generate_random_timestamp().isoformat() + "Z",
        "amount": total_amount,
        "transactionType": transaction_type,
        "category": "Groceries",
        "description": f"{'Return to' if transaction_type == 'credit' else 'Shopping at'} {store['name']}",
        "importance": "medium",
        "warranty": None,
        "recurring": None,
        "items": items,
        "metadata": {
            "vendor_type": "SUPERMARKET",
            "confidence": "high",
            "processing_time_seconds": round(random.uniform(10, 30), 3),
            "model_version": "gemini-2.5-flash"
        }
    }

def generate_gas_receipt(transaction_type: str) -> Dict[str, Any]:
    """Generate gas station receipt"""
    station = random.choice(GAS_STATIONS)
    
    # Gas purchase
    gallons = round(random.uniform(8, 18), 3)
    price_per_gallon = round(random.uniform(3.20, 4.50), 3)
    total_amount = round(gallons * price_per_gallon, 2)
    
    items = [{
        "name": "Regular Gasoline",
        "quantity": gallons,
        "unit_price": price_per_gallon,
        "total_price": total_amount,
        "category": "Fuel",
        "description": f"Regular unleaded gasoline {gallons} gallons",
        "warranty": None,
        "recurring": None
    }]
    
    if transaction_type == "credit":
        total_amount = -abs(total_amount)
    
    return {
        "receipt_id": str(uuid.uuid4()),
        "place": station["name"],
        "time": generate_random_timestamp().isoformat() + "Z",
        "amount": total_amount,
        "transactionType": transaction_type,
        "category": "Fuel",
        "description": f"{'Refund from' if transaction_type == 'credit' else 'Fuel purchase at'} {station['name']}",
        "importance": "medium",
        "warranty": None,
        "recurring": None,
        "items": items,
        "metadata": {
            "vendor_type": "SERVICE",
            "confidence": "high",
            "processing_time_seconds": round(random.uniform(5, 15), 3),
            "model_version": "gemini-2.5-flash"
        }
    }

def generate_pharmacy_receipt(transaction_type: str) -> Dict[str, Any]:
    """Generate pharmacy receipt"""
    pharmacy = random.choice(PHARMACIES)
    
    # Generate 1-3 items
    num_items = random.randint(1, 3)
    items = []
    total_amount = 0
    
    selected_items = random.sample(PHARMACY_ITEMS, min(num_items, len(PHARMACY_ITEMS)))
    
    for item in selected_items:
        quantity = 1
        unit_price = item["price"] + random.uniform(-1, 2)
        unit_price = max(2.99, round(unit_price, 2))
        total_price = round(quantity * unit_price, 2)
        total_amount += total_price
        
        items.append({
            "name": item["name"],
            "quantity": float(quantity),
            "unit_price": unit_price,
            "total_price": total_price,
            "category": "Pharmacy",
            "description": item["desc"],
            "warranty": None,
            "recurring": None
        })
    
    # Add tax
    tax = round(total_amount * 0.07, 2)
    total_amount = round(total_amount + tax, 2)
    
    if transaction_type == "credit":
        total_amount = -abs(total_amount)
    
    return {
        "receipt_id": str(uuid.uuid4()),
        "place": pharmacy["name"],
        "time": generate_random_timestamp().isoformat() + "Z",
        "amount": total_amount,
        "transactionType": transaction_type,
        "category": "Pharmacy",
        "description": f"{'Return to' if transaction_type == 'credit' else 'Purchase from'} {pharmacy['name']}",
        "importance": "medium",
        "warranty": None,
        "recurring": None,
        "items": items,
        "metadata": {
            "vendor_type": "SUPERMARKET",
            "confidence": "high",
            "processing_time_seconds": round(random.uniform(6, 20), 3),
            "model_version": "gemini-2.5-flash"
        }
    }

def generate_clothing_receipt(transaction_type: str) -> Dict[str, Any]:
    """Generate clothing store receipt"""
    store = random.choice(CLOTHING_STORES)
    
    # Generate 1-3 items
    num_items = random.randint(1, 3)
    items = []
    total_amount = 0
    
    selected_items = random.sample(CLOTHING_ITEMS, min(num_items, len(CLOTHING_ITEMS)))
    
    for item in selected_items:
        quantity = 1
        unit_price = item["price"] + random.uniform(-5, 10)
        unit_price = max(9.99, round(unit_price, 2))
        total_price = round(quantity * unit_price, 2)
        total_amount += total_price
        
        items.append({
            "name": item["name"],
            "quantity": float(quantity),
            "unit_price": unit_price,
            "total_price": total_price,
            "category": "Clothes & shoes",
            "description": item["desc"],
            "warranty": None,
            "recurring": None
        })
    
    # Add tax
    tax = round(total_amount * 0.08, 2)
    total_amount = round(total_amount + tax, 2)
    
    if transaction_type == "credit":
        total_amount = -abs(total_amount)
    
    return {
        "receipt_id": str(uuid.uuid4()),
        "place": store["name"],
        "time": generate_random_timestamp().isoformat() + "Z",
        "amount": total_amount,
        "transactionType": transaction_type,
        "category": "Clothes & shoes",
        "description": f"{'Return to' if transaction_type == 'credit' else 'Purchase from'} {store['name']}",
        "importance": random.choice(["low", "medium"]),
        "warranty": None,
        "recurring": None,
        "items": items,
        "metadata": {
            "vendor_type": "SUPERMARKET",
            "confidence": "high",
            "processing_time_seconds": round(random.uniform(8, 25), 3),
            "model_version": "gemini-2.5-flash"
        }
    }

def generate_random_timestamp() -> datetime:
    """Generate random timestamp within last 6 months"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    
    random_date = start_date + timedelta(days=random_days)
    
    # Add random time
    random_hour = random.randint(6, 22)
    random_minute = random.randint(0, 59)
    random_second = random.randint(0, 59)
    
    return random_date.replace(hour=random_hour, minute=random_minute, second=random_second)

async def populate_transactions():
    """Populate 100 dummy transactions in Firestore"""
    
    # Initialize Firestore client
    client = firestore.AsyncClient(project="walleterium")
    
    print("🚀 Starting to populate 100 dummy transactions...")
    
    batch_size = 10
    total_created = 0
    
    try:
        for batch_num in range(10):  # 10 batches of 10 transactions each
            batch = client.batch()
            
            for i in range(batch_size):
                receipt_data = generate_receipt_data()
                doc_id = receipt_data["receipt_id"]
                
                # Add timestamps
                receipt_data["created_at"] = datetime.utcnow()
                receipt_data["updated_at"] = datetime.utcnow()
                
                # Add to batch
                doc_ref = client.collection("transactions").document(doc_id)
                batch.set(doc_ref, receipt_data)
                
                total_created += 1
                print(f"📝 Prepared transaction {total_created}: {receipt_data['place']} - ${receipt_data['amount']}")
            
            # Commit batch
            await batch.commit()
            print(f"✅ Committed batch {batch_num + 1}/10 ({batch_size} transactions)")
        
        print(f"🎉 Successfully populated {total_created} dummy transactions!")
        
    except Exception as e:
        print(f"❌ Error populating transactions: {e}")
        raise
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(populate_transactions()) 