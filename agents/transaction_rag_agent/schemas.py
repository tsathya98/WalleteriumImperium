"""
Pydantic schemas for Transaction RAG Agent
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class TransactionQuery(BaseModel):
    """Schema for transaction RAG queries"""
    
    query: str = Field(..., description="Natural language query about transactions")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Chat session identifier")
    language: str = Field(default="en", description="Response language code")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional query context")


class TransactionSource(BaseModel):
    """Schema for RAG source references"""
    
    title: str = Field(..., description="Source title or transaction identifier")
    uri: str = Field(default="", description="Source URI or reference")
    snippet: str = Field(..., description="Relevant content snippet")
    transaction_id: Optional[str] = Field(default=None, description="Transaction ID if applicable")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score (0-1)")


class TransactionRAGResponse(BaseModel):
    """Schema for transaction RAG responses"""
    
    response: str = Field(..., description="AI-generated response text")
    session_id: str = Field(..., description="Chat session identifier")
    sources: List[TransactionSource] = Field(default_factory=list, description="RAG source references")
    query_type: Literal[
        "spending_analysis", 
        "category_breakdown", 
        "time_analysis", 
        "merchant_analysis",
        "item_search",
        "budget_insights",
        "transaction_search",
        "trend_analysis",
        "comparison",
        "general_query",
        "error"
    ] = Field(..., description="Type of query processed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence (0-1)")
    language: str = Field(default="en", description="Response language")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional response metadata")


class TransactionIndexRequest(BaseModel):
    """Schema for transaction indexing requests"""
    
    transaction_id: str = Field(..., description="Transaction identifier")
    force_reindex: bool = Field(default=False, description="Force re-indexing if already exists")


class TransactionIndexResponse(BaseModel):
    """Schema for transaction indexing responses"""
    
    success: bool = Field(..., description="Indexing success status")
    transaction_id: str = Field(..., description="Transaction identifier")
    corpus_id: Optional[str] = Field(default=None, description="RAG corpus identifier")
    message: str = Field(..., description="Status message")
    indexed_at: Optional[datetime] = Field(default=None, description="Indexing timestamp")


class BulkIndexRequest(BaseModel):
    """Schema for bulk transaction indexing"""
    
    batch_size: int = Field(default=50, ge=1, le=100, description="Batch size for processing")
    force_reindex: bool = Field(default=False, description="Force re-indexing of existing transactions")
    user_id: Optional[str] = Field(default=None, description="Index transactions for specific user only")


class BulkIndexResponse(BaseModel):
    """Schema for bulk indexing responses"""
    
    total_processed: int = Field(..., description="Total transactions processed")
    successfully_indexed: int = Field(..., description="Successfully indexed transactions")
    failed: int = Field(..., description="Failed indexing attempts")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate (0-1)")
    corpus_id: str = Field(..., description="RAG corpus identifier")
    processing_time_seconds: Optional[float] = Field(default=None, description="Total processing time")
    started_at: Optional[datetime] = Field(default=None, description="Processing start time")
    completed_at: Optional[datetime] = Field(default=None, description="Processing completion time")


class TransactionInsight(BaseModel):
    """Schema for transaction insights"""
    
    insight_type: Literal[
        "top_spending_category",
        "frequent_merchant",
        "unusual_transaction",
        "spending_trend",
        "budget_alert",
        "savings_opportunity"
    ] = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    value: Optional[float] = Field(default=None, description="Numerical value if applicable")
    category: Optional[str] = Field(default=None, description="Related category")
    time_period: Optional[str] = Field(default=None, description="Time period for the insight")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Insight confidence")
    actionable: bool = Field(default=False, description="Whether the insight is actionable")
    related_transactions: List[str] = Field(default_factory=list, description="Related transaction IDs")


class TransactionAnalyticsRequest(BaseModel):
    """Schema for transaction analytics requests"""
    
    user_id: str = Field(..., description="User identifier")
    analysis_type: Literal[
        "spending_summary",
        "category_trends",
        "merchant_analysis",
        "monthly_comparison",
        "budget_tracking",
        "savings_analysis"
    ] = Field(..., description="Type of analysis to perform")
    time_range: Optional[Dict[str, str]] = Field(default=None, description="Time range for analysis (start_date, end_date)")
    categories: Optional[List[str]] = Field(default=None, description="Specific categories to analyze")
    include_insights: bool = Field(default=True, description="Whether to include AI-generated insights")


class TransactionAnalyticsResponse(BaseModel):
    """Schema for transaction analytics responses"""
    
    analysis_type: str = Field(..., description="Type of analysis performed")
    user_id: str = Field(..., description="User identifier")
    summary: str = Field(..., description="AI-generated summary of findings")
    data: Dict[str, Any] = Field(..., description="Raw analytics data")
    insights: List[TransactionInsight] = Field(default_factory=list, description="AI-generated insights")
    time_range: Optional[Dict[str, str]] = Field(default=None, description="Time range analyzed")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis generation time")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")


class RAGCorpusInfo(BaseModel):
    """Schema for RAG corpus information"""
    
    corpus_id: str = Field(..., description="Corpus identifier")
    display_name: str = Field(..., description="Human-readable corpus name")
    description: str = Field(..., description="Corpus description")
    total_documents: Optional[int] = Field(default=None, description="Total documents in corpus")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    project_id: str = Field(..., description="Google Cloud project ID")
    location: str = Field(..., description="Vertex AI location")


class TransactionChatSession(BaseModel):
    """Schema for transaction chat session metadata"""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    message_count: int = Field(default=0, description="Number of messages in session")
    language: str = Field(default="en", description="Session language")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Session context data")
    is_active: bool = Field(default=True, description="Whether session is active") 