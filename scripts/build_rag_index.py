"""
This script fetches all transactions from Firestore and calls the
local API to build the Vertex AI RAG index.

Instructions:
1. Make sure the FastAPI server is running locally.
   (e.g., `uvicorn main:app --reload`)
2. Make sure you have the required libraries:
   `pip install requests google-cloud-firestore tqdm`
3. Run this script from the root of your project:
   `python -m scripts.build_rag_index`
"""
import requests
import json
import datetime
import time
import concurrent.futures
from google.cloud import firestore
from tqdm import tqdm

from app.core.config import get_settings

# --- Configuration ---
API_BASE_URL = "http://localhost:8080/api/v1"
INDEX_ENDPOINT = f"{API_BASE_URL}/transactions/index"
MAX_WORKERS = 20  # Number of parallel requests

def json_converter(o):
    """Converts datetime objects to ISO 8601 strings for JSON serialization."""
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def index_single_transaction(tx, session):
    """Sends a single transaction to the indexing endpoint."""
    try:
        json_payload = json.dumps(tx, default=json_converter)
        response = session.post(
            INDEX_ENDPOINT,
            data=json_payload,
            headers={'Content-Type': 'application/json'},
            timeout=60  # 60-second timeout for the request
        )
        if response.status_code == 200:
            return True
        else:
            tqdm.write(f"❌ Failed to index {tx.get('receipt_id', 'N/A')}: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        tqdm.write(f"❌ Exception while indexing {tx.get('receipt_id', 'N/A')}: {e}")
        return False

def build_index():
    """Fetches transactions and calls the indexing API in parallel."""
    print("--- Starting RAG Index Build ---")

    # 1. Initialize Firestore
    try:
        settings = get_settings()
        db = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT_ID)
        print(f"Connected to Firestore project: {settings.GOOGLE_CLOUD_PROJECT_ID}")
    except Exception as e:
        print(f"❌ Could not connect to Firestore: {e}")
        print("Please ensure your GCP credentials are set up correctly.")
        return

    # 2. Fetch all transactions
    try:
        transactions_ref = db.collection("transactions")
        all_transactions = [doc.to_dict() for doc in transactions_ref.stream()]
        total_transactions = len(all_transactions)
        print(f"Found {total_transactions} transactions to index.")
        if not all_transactions:
            print("No transactions found. Exiting.")
            return
    except Exception as e:
        print(f"❌ Error fetching transactions from Firestore: {e}")
        return

    # 3. Call the indexing API for each transaction in parallel
    print(f"\n--- Sending {total_transactions} transactions to the RAG engine in parallel (max_workers={MAX_WORKERS}) ---")
    start_time = time.time()
    success_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with requests.Session() as session:
            futures = [executor.submit(index_single_transaction, tx, session) for tx in all_transactions]
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=total_transactions, desc="Indexing Transactions"):
                if future.result():
                    success_count += 1
    
    total_time = time.time() - start_time
    failure_count = total_transactions - success_count

    # 4. Print summary
    print("\n\n--- Index Build Complete ---")
    print(f"Total time taken: {total_time:.2f} seconds")
    if total_transactions > 0:
        print(f"Average time per transaction: {total_time / total_transactions:.2f} seconds")
    print(f"Successfully indexed: {success_count}")
    print(f"Failed to index:    {failure_count}")
    print("----------------------------\n")
    if failure_count == 0:
        print("✅ Your RAG index is now ready for chat!")
    else:
        print("⚠️ Some transactions failed to index. Please check the errors above.")


if __name__ == "__main__":
    build_index() 