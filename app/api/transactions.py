"""
Transaction RAG API - Natural language interface for transaction analysis
Provides RAG-powered conversational access to transaction data
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import uuid
import time

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.firestore_service import FirestoreService
from agents.transaction_rag_agent.agent import get_transaction_rag_agent
from agents.transaction_rag_agent.schemas import (
    TransactionQuery, 
    TransactionRAGResponse,
    TransactionIndexRequest,
    TransactionIndexResponse,
    BulkIndexRequest,
    BulkIndexResponse,
    TransactionAnalyticsRequest,
    TransactionAnalyticsResponse,
    RAGCorpusInfo
)

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])
security = HTTPBearer(auto_error=False)


async def get_firestore_service(request: Request) -> FirestoreService:
    """Dependency to get Firestore service from app state"""
    return request.app.state.firestore_service


@router.post("/chat", response_model=TransactionRAGResponse)
async def chat_with_transactions(
    query_data: TransactionQuery,
    firestore_service: FirestoreService = Depends(get_firestore_service)
):
    """
    Chat with your transaction data using natural language
    
    Ask questions about your spending, get insights, and analyze patterns:
    - "How much did I spend on restaurants last month?"
    - "What are my top spending categories?"
    - "Show me unusual transactions"
    - "Compare this month vs last month spending"
    """
    try:
        start_time = time.time()
        
        logger.info(f"Transaction chat query from user {query_data.user_id}: '{query_data.query}'")
        
        # Get the RAG agent
        rag_agent = await get_transaction_rag_agent()
        
        # Process the query
        response = await rag_agent.query_transactions(
            session_id=query_data.session_id,
            user_id=query_data.user_id,
            query=query_data.query,
            language=query_data.language
        )
        
        processing_time = round(time.time() - start_time, 3)
        
        # Add metadata
        response.metadata = {
            "processing_time_seconds": processing_time,
            "query_length": len(query_data.query),
            "sources_found": len(response.sources),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Transaction chat completed for user {query_data.user_id} in {processing_time}s",
            extra={
                "user_id": query_data.user_id,
                "session_id": query_data.session_id,
                "query_type": response.query_type,
                "confidence": response.confidence,
                "sources_count": len(response.sources),
                "processing_time": processing_time
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Transaction chat failed for user {query_data.user_id}: {e}")
        return TransactionRAGResponse(
            response="I apologize, but I'm having trouble accessing your transaction data right now. Please try again in a moment.",
            session_id=query_data.session_id,
            sources=[],
            query_type="error",
            confidence=0.0,
            language=query_data.language,
            metadata={"error": str(e)}
        )


@router.post("/index", response_model=TransactionIndexResponse)
async def index_transaction(
    index_request: TransactionIndexRequest,
    firestore_service: FirestoreService = Depends(get_firestore_service)
):
    """
    Index a specific transaction into the RAG corpus
    
    This endpoint is typically called automatically when transactions are created/updated,
    but can be used manually to re-index specific transactions.
    """
    try:
        start_time = time.time()
        
        logger.info(f"Manual indexing requested for transaction {index_request.transaction_id}")
        
        # Get the transaction from Firestore
        doc_ref = firestore_service.client.collection("transactions").document(index_request.transaction_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {index_request.transaction_id} not found"
            )
        
        # Get the RAG agent
        rag_agent = await get_transaction_rag_agent()
        
        # Index the transaction
        transaction_data = doc.to_dict()
        success = await rag_agent.index_transaction(transaction_data)
        
        processing_time = round(time.time() - start_time, 3)
        
        if success:
            response = TransactionIndexResponse(
                success=True,
                transaction_id=index_request.transaction_id,
                corpus_id=rag_agent.rag_corpus.corpus_id,
                message="Transaction successfully indexed",
                indexed_at=datetime.utcnow()
            )
            logger.info(f"Transaction {index_request.transaction_id} indexed successfully in {processing_time}s")
        else:
            response = TransactionIndexResponse(
                success=False,
                transaction_id=index_request.transaction_id,
                corpus_id=rag_agent.rag_corpus.corpus_id,
                message="Transaction indexing failed",
                indexed_at=None
            )
            logger.warning(f"Transaction {index_request.transaction_id} indexing failed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction indexing error for {index_request.transaction_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/index/bulk", response_model=BulkIndexResponse)
async def bulk_index_transactions(
    bulk_request: BulkIndexRequest,
    firestore_service: FirestoreService = Depends(get_firestore_service)
):
    """
    Bulk index all transactions into the RAG corpus
    
    This is useful for:
    - Initial setup of the RAG system
    - Re-indexing after system updates
    - Fixing corrupted indexes
    
    WARNING: This can be a time-consuming operation for large transaction datasets.
    """
    try:
        start_time = time.time()
        
        logger.info(f"Bulk indexing started with batch_size={bulk_request.batch_size}")
        
        # Get the RAG agent
        rag_agent = await get_transaction_rag_agent()
        
        # Start bulk indexing
        results = await rag_agent.index_all_transactions(
            firestore_service=firestore_service,
            batch_size=bulk_request.batch_size
        )
        
        processing_time = round(time.time() - start_time, 3)
        
        response = BulkIndexResponse(
            total_processed=results["total_processed"],
            successfully_indexed=results["successfully_indexed"],
            failed=results["failed"],
            success_rate=results["success_rate"],
            corpus_id=results["corpus_id"],
            processing_time_seconds=processing_time,
            started_at=datetime.fromtimestamp(start_time),
            completed_at=datetime.utcnow()
        )
        
        logger.info(
            f"Bulk indexing completed: {results['successfully_indexed']}/{results['total_processed']} "
            f"transactions indexed in {processing_time}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Bulk indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk indexing failed: {str(e)}")


@router.get("/corpus/info", response_model=RAGCorpusInfo)
async def get_corpus_info():
    """
    Get information about the RAG corpus used for transaction indexing
    """
    try:
        # Get the RAG agent
        rag_agent = await get_transaction_rag_agent()
        
        corpus_info = RAGCorpusInfo(
            corpus_id=rag_agent.rag_corpus.corpus_id,
            display_name=rag_agent.rag_corpus.display_name,
            description=rag_agent.rag_corpus.description,
            project_id=settings.GOOGLE_CLOUD_PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION,
            last_updated=datetime.utcnow()
        )
        
        logger.info(f"Corpus info retrieved: {corpus_info.corpus_id}")
        return corpus_info
        
    except Exception as e:
        logger.error(f"Failed to get corpus info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get corpus info: {str(e)}")


@router.post("/analytics", response_model=TransactionAnalyticsResponse)
async def get_transaction_analytics(
    analytics_request: TransactionAnalyticsRequest,
    firestore_service: FirestoreService = Depends(get_firestore_service)
):
    """
    Get AI-powered analytics and insights about transaction patterns
    
    Available analysis types:
    - spending_summary: Overall spending overview
    - category_trends: Category-wise spending trends
    - merchant_analysis: Merchant spending patterns
    - monthly_comparison: Month-over-month comparisons
    - budget_tracking: Budget vs actual spending
    - savings_analysis: Savings opportunities
    """
    try:
        start_time = time.time()
        
        logger.info(f"Analytics requested: {analytics_request.analysis_type} for user {analytics_request.user_id}")
        
        # Get the RAG agent
        rag_agent = await get_transaction_rag_agent()
        
        # Create analytical query based on request type
        analytical_queries = {
            "spending_summary": f"Provide a comprehensive spending summary for user {analytics_request.user_id}. Include total spending, top categories, and key insights.",
            "category_trends": f"Analyze category-wise spending trends for user {analytics_request.user_id}. Show which categories are increasing or decreasing.",
            "merchant_analysis": f"Analyze merchant spending patterns for user {analytics_request.user_id}. Identify top merchants and spending habits.",
            "monthly_comparison": f"Compare monthly spending patterns for user {analytics_request.user_id}. Show trends and changes over time.",
            "budget_tracking": f"Analyze budget performance for user {analytics_request.user_id}. Identify overspending areas and budget adherence.",
            "savings_analysis": f"Identify savings opportunities for user {analytics_request.user_id}. Suggest areas for spending optimization."
        }
        
        query = analytical_queries.get(
            analytics_request.analysis_type,
            f"Provide financial analysis for user {analytics_request.user_id}"
        )
        
        # Add time range filter if provided
        if analytics_request.time_range:
            query += f" for the period from {analytics_request.time_range.get('start_date')} to {analytics_request.time_range.get('end_date')}"
        
        # Add category filter if provided
        if analytics_request.categories:
            query += f" focusing on categories: {', '.join(analytics_request.categories)}"
        
        # Execute the analytical query
        session_id = f"analytics_{analytics_request.user_id}_{int(time.time())}"
        rag_response = await rag_agent.query_transactions(
            session_id=session_id,
            user_id=analytics_request.user_id,
            query=query,
            language="en"
        )
        
        processing_time = round(time.time() - start_time, 3)
        
        # Create analytics response
        response = TransactionAnalyticsResponse(
            analysis_type=analytics_request.analysis_type,
            user_id=analytics_request.user_id,
            summary=rag_response.response,
            data={
                "query_used": query,
                "sources_count": len(rag_response.sources),
                "processing_time": processing_time,
                "confidence": rag_response.confidence
            },
            insights=[],  # Could be enhanced with structured insights extraction
            time_range=analytics_request.time_range,
            confidence=rag_response.confidence
        )
        
        logger.info(f"Analytics completed for {analytics_request.user_id} in {processing_time}s")
        return response
        
    except Exception as e:
        logger.error(f"Analytics failed for user {analytics_request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.post("/webhook/firestore")
async def firestore_webhook(
    request: Request,
    firestore_service: FirestoreService = Depends(get_firestore_service)
):
    """
    Webhook endpoint for Firestore triggers
    
    Automatically indexes transactions when they are created or updated in Firestore.
    This endpoint should be called by Firestore triggers or Cloud Functions.
    """
    try:
        # Parse the webhook payload
        payload = await request.json()
        
        # Extract transaction data from the webhook
        if "eventType" in payload and "data" in payload:
            event_type = payload["eventType"]
            transaction_data = payload["data"]
            
            logger.info(f"Firestore webhook received: {event_type}")
            
            # Only process document creation and updates
            if event_type in ["google.firestore.document.create", "google.firestore.document.update"]:
                # Get the RAG agent
                rag_agent = await get_transaction_rag_agent()
                
                # Index the transaction
                success = await rag_agent.index_transaction(transaction_data)
                
                if success:
                    logger.info(f"Auto-indexed transaction from webhook: {transaction_data.get('receipt_id')}")
                    return {"status": "success", "message": "Transaction indexed"}
                else:
                    logger.warning(f"Failed to auto-index transaction: {transaction_data.get('receipt_id')}")
                    return {"status": "error", "message": "Indexing failed"}
            else:
                logger.info(f"Ignored webhook event type: {event_type}")
                return {"status": "ignored", "message": "Event type not relevant"}
        else:
            logger.warning("Invalid webhook payload received")
            return {"status": "error", "message": "Invalid payload"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)} 