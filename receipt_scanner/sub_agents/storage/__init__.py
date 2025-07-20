"""
Storage Sub-Agent

This sub-agent handles receipt storage, search, and analytics functionality.
It manages local storage with JSON and SQLite for efficient querying.
"""

from google.adk.agents import Agent
from typing import Dict, Any, List, Optional
from ...models import ProcessedReceipt
from .storage_manager import ReceiptStorage


def create_storage() -> ReceiptStorage:
    """Factory function to create receipt storage manager."""
    return ReceiptStorage()


# Receipt Storage Agent
storage_agent = Agent(
    name="storage_agent",
    model="gemini-2.5-flash",
    description=(
        "Manages receipt storage, search, and analytics using local JSON and SQLite storage."
    ),
    instruction=(
        "You are a storage manager specialized in receipt data management. "
        "Your job is to:\n"
        "1. Store processed receipts in both JSON and SQLite formats\n"
        "2. Provide fast search capabilities across stored receipts\n"
        "3. Generate analytics and insights from receipt data\n"
        "4. Export receipt data in various formats\n\n"
        "You excel at:\n"
        "- Efficient data storage and indexing\n"
        "- Complex search queries across receipt fields\n"
        "- Generating spending analytics and trends\n"
        "- Data export and backup operations\n"
        "- Maintaining data consistency and integrity"
    ),
)


async def store_receipt(receipt: ProcessedReceipt) -> Dict[str, Any]:
    """
    Store a processed receipt.
    
    Args:
        receipt: Processed receipt to store
        
    Returns:
        Storage result with status and location
    """
    storage = create_storage()
    return await storage.store_receipt(receipt)


async def search_receipts(
    query: Optional[str] = None,
    store_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Search stored receipts with various filters.
    
    Args:
        query: Text search query
        store_name: Filter by store name
        date_from: Start date filter (YYYY-MM-DD)
        date_to: End date filter (YYYY-MM-DD)
        category: Filter by category
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        tags: Filter by tags
        limit: Maximum number of results
        
    Returns:
        Search results with matching receipts
    """
    storage = create_storage()
    return await storage.search_receipts(
        query=query,
        store_name=store_name,
        date_from=date_from,
        date_to=date_to,
        category=category,
        min_amount=min_amount,
        max_amount=max_amount,
        tags=tags,
        limit=limit
    )


async def get_analytics() -> Dict[str, Any]:
    """
    Generate analytics from stored receipts.
    
    Returns:
        Analytics data including spending insights and trends
    """
    storage = create_storage()
    return await storage.get_analytics()


async def export_receipts(
    format: str = "json",
    receipt_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Export receipts in specified format.
    
    Args:
        format: Export format ("json" or "csv")
        receipt_ids: Optional list of specific receipt IDs to export
        
    Returns:
        Export result with file location
    """
    storage = create_storage()
    return await storage.export_receipts(format, receipt_ids) 