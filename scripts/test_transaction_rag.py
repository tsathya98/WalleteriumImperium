#!/usr/bin/env python3
"""
Test script for Transaction RAG Agent
Demonstrates the RAG-powered transaction query system
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

import requests


# Configuration
BASE_URL = "http://localhost:8080"
TEST_USER_ID = "test_user_123"
TEST_SESSION_ID = f"test_session_{int(time.time())}"


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_response(response_data: Dict[str, Any]):
    """Print a formatted response"""
    print(f"\n🤖 TransactBot Response:")
    print(f"   {response_data.get('response', 'No response')}")
    
    sources = response_data.get('sources', [])
    if sources:
        print(f"\n📊 Sources Found: {len(sources)}")
        for i, source in enumerate(sources[:3], 1):  # Show max 3 sources
            print(f"   {i}. {source.get('title', 'Unknown')}")
    
    metadata = response_data.get('metadata', {})
    if metadata:
        processing_time = metadata.get('processing_time_seconds', 'Unknown')
        print(f"\n⏱️  Processing Time: {processing_time}s")
    
    print(f"🎯 Query Type: {response_data.get('query_type', 'Unknown')}")
    print(f"📈 Confidence: {response_data.get('confidence', 0):.1%}")


def test_chat_query(query: str) -> Dict[str, Any]:
    """Test a chat query"""
    url = f"{BASE_URL}/api/v1/transactions/chat"
    
    payload = {
        "query": query,
        "user_id": TEST_USER_ID,
        "session_id": TEST_SESSION_ID,
        "language": "en"
    }
    
    try:
        print(f"\n💬 Query: '{query}'")
        print("🔄 Processing...")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return {"error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"error": str(e)}


def test_bulk_indexing() -> Dict[str, Any]:
    """Test bulk indexing of transactions"""
    url = f"{BASE_URL}/api/v1/transactions/index/bulk"
    
    payload = {
        "batch_size": 10,
        "force_reindex": False
    }
    
    try:
        print("🔄 Starting bulk indexing...")
        
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Indexing error {response.status_code}: {response.text}")
            return {"error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Indexing request failed: {e}")
        return {"error": str(e)}


def test_corpus_info() -> Dict[str, Any]:
    """Test getting corpus information"""
    url = f"{BASE_URL}/api/v1/transactions/corpus/info"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Corpus info error {response.status_code}: {response.text}")
            return {"error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Corpus info request failed: {e}")
        return {"error": str(e)}


def test_analytics() -> Dict[str, Any]:
    """Test analytics functionality"""
    url = f"{BASE_URL}/api/v1/transactions/analytics"
    
    payload = {
        "user_id": TEST_USER_ID,
        "analysis_type": "spending_summary",
        "include_insights": True
    }
    
    try:
        print("🔄 Generating analytics...")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Analytics error {response.status_code}: {response.text}")
            return {"error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Analytics request failed: {e}")
        return {"error": str(e)}


def main():
    """Main test function"""
    print_header("🚀 Transaction RAG Agent Test Suite")
    print(f"📍 Testing against: {BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print(f"💬 Session ID: {TEST_SESSION_ID}")
    
    # Test 1: Check if API is running
    print_header("1️⃣  API Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and healthy")
        else:
            print(f"⚠️  API health check returned {response.status_code}")
    except Exception as e:
        print(f"❌ API is not accessible: {e}")
        print("🔧 Please ensure the server is running with: python main.py")
        return
    
    # Test 2: Get corpus information
    print_header("2️⃣  RAG Corpus Information")
    corpus_info = test_corpus_info()
    if "error" not in corpus_info:
        print(f"✅ RAG Corpus ID: {corpus_info.get('corpus_id', 'Unknown')}")
        print(f"📝 Display Name: {corpus_info.get('display_name', 'Unknown')}")
        print(f"🌍 Location: {corpus_info.get('location', 'Unknown')}")
    else:
        print("⚠️  Could not retrieve corpus information")
    
    # Test 3: Bulk indexing (if no transactions are indexed)
    print_header("3️⃣  Bulk Transaction Indexing")
    index_result = test_bulk_indexing()
    if "error" not in index_result:
        total = index_result.get('total_processed', 0)
        successful = index_result.get('successfully_indexed', 0)
        processing_time = index_result.get('processing_time_seconds', 0)
        
        print(f"✅ Indexing completed!")
        print(f"📊 Total processed: {total}")
        print(f"✅ Successfully indexed: {successful}")
        print(f"⏱️  Processing time: {processing_time:.2f}s")
        
        if total == 0:
            print("ℹ️  No transactions found to index")
            print("💡 You can add dummy transactions with: python scripts/populate_dummy_transactions.py")
    else:
        print("⚠️  Bulk indexing encountered issues")
    
    # Test 4: Sample queries
    print_header("4️⃣  Natural Language Query Tests")
    
    test_queries = [
        "How much did I spend on restaurants last month?",
        "What are my top 3 spending categories?",
        "Show me my most expensive transactions",
        "Where do I shop most frequently?",
        "Find all transactions containing coffee",
        "Compare my spending this month vs last month"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i}/{len(test_queries)} ---")
        result = test_chat_query(query)
        
        if "error" not in result:
            print_response(result)
        else:
            print(f"❌ Query failed: {result['error']}")
        
        # Small delay between queries
        time.sleep(1)
    
    # Test 5: Analytics
    print_header("5️⃣  Analytics Test")
    analytics_result = test_analytics()
    if "error" not in analytics_result:
        print(f"✅ Analytics generated successfully!")
        print(f"📈 Analysis Type: {analytics_result.get('analysis_type', 'Unknown')}")
        print(f"📊 Summary Preview: {analytics_result.get('summary', 'No summary')[:200]}...")
    else:
        print("⚠️  Analytics generation encountered issues")
    
    # Final summary
    print_header("📋 Test Summary")
    print("✅ Transaction RAG Agent test suite completed!")
    print("\n🎯 Next Steps:")
    print("   1. Try more complex queries through the API")
    print("   2. Integrate with your frontend application")
    print("   3. Set up automatic transaction indexing")
    print("   4. Customize prompts and responses for your use case")
    print("\n📚 Documentation: agents/transaction_rag_agent/README.md")
    print("🔗 API Docs: http://localhost:8080/docs")


if __name__ == "__main__":
    main() 