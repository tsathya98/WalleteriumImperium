"""
Pydantic data models for Project Raseed
MVP: Simple receipt analysis structure, will be enhanced with AI features later
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    CREDIT = "credit"
    DEBIT = "debit"


class ImportanceLevel(str, Enum):
    """Importance level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrenceType(str, Enum):
    """Subscription recurrence types"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ProcessingStatus(str, Enum):
    """Receipt processing status enumeration"""
    UPLOADED = "uploaded"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStage(str, Enum):
    """Processing stage enumeration"""
    UPLOAD = "upload"
    ANALYSIS = "analysis"
    COMPLETED = "completed"


# Nested Objects for MVP
class SubscriptionDetails(BaseModel):
    """Subscription details when recurring=true"""
    name: str = Field(..., description="Subscription service name")
    recurrence: RecurrenceType = Field(..., description="Billing frequency")
    nextDueDate: str = Field(..., description="Next billing date (ISO 8601)")
    
    @field_validator("nextDueDate")
    @classmethod
    def validate_next_due_date(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("nextDueDate must be in ISO 8601 format")


class WarrantyDetails(BaseModel):
    """Warranty details when warranty=true"""
    validUntil: str = Field(..., description="Warranty expiry date (ISO 8601)")
    provider: Optional[str] = Field(None, description="Warranty provider name")
    termsURL: Optional[str] = Field(None, description="Link to warranty terms")
    
    @field_validator("validUntil")
    @classmethod
    def validate_valid_until(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("validUntil must be in ISO 8601 format")


# Main Receipt Analysis Model (MVP Version)
class ReceiptAnalysis(BaseModel):
    """Main receipt analysis result - MVP structure, will be enhanced later"""
    
    # Core required fields
    place: str = Field(..., description="Store or merchant name where transaction occurred")
    time: str = Field(..., description="Transaction timestamp (ISO 8601)")
    amount: float = Field(..., ge=0, description="Transaction amount (positive)")
    transactionType: TransactionType = Field(..., description="Transaction type")
    
    # Optional fields
    category: Optional[str] = Field(None, description="User-defined category (e.g., 'Dining', 'Groceries')")
    description: Optional[str] = Field(None, description="Free-form notes about the transaction")
    importance: Optional[ImportanceLevel] = Field(None, description="Transaction importance level")
    warranty: Optional[bool] = Field(False, description="Does this purchase include a warranty?")
    recurring: Optional[bool] = Field(False, description="Is this a recurring/subscription payment?")
    
    # Conditional nested objects
    subscription: Optional[SubscriptionDetails] = Field(None, description="Subscription details (when recurring=true)")
    warrantyDetails: Optional[WarrantyDetails] = Field(None, description="Warranty details (when warranty=true)")
    
    # MVP metadata (will be enhanced with AI confidence scores later)
    receipt_id: str = Field(..., description="Unique receipt identifier")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    
    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("time must be in ISO 8601 format")


# Request Models for Multipart Form Data
class ReceiptUploadMetadata(BaseModel):
    """Metadata for receipt upload (sent as form field)"""
    user_id: str = Field(..., description="User ID from Firebase Auth")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Optional metadata")
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        return v.strip()
    



# Response Models
class ReceiptUploadResponse(BaseModel):
    """Response model for receipt upload"""
    processing_token: str = Field(..., description="Token to track processing status")
    estimated_time: int = Field(..., description="Estimated processing time in seconds")
    status: ProcessingStatus = Field(default=ProcessingStatus.UPLOADED)
    message: str = Field(default="Receipt uploaded successfully, processing started")


class ProcessingProgress(BaseModel):
    """Processing progress information"""
    stage: ProcessingStage = Field(..., description="Current processing stage")
    percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Progress message")
    estimated_remaining: Optional[int] = Field(None, description="Estimated remaining seconds")


class ErrorDetail(BaseModel):
    """Error detail information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ReceiptStatusResponse(BaseModel):
    """Response model for receipt status check"""
    token: str = Field(..., description="Processing token")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: ProcessingProgress = Field(..., description="Processing progress")
    
    # Result data (only when completed)
    result: Optional[ReceiptAnalysis] = Field(None, description="Processing result")
    
    # Error information (only when failed)
    error: Optional[ErrorDetail] = Field(None, description="Error details")
    
    # Timestamps
    created_at: datetime = Field(..., description="Token creation time")
    updated_at: datetime = Field(..., description="Last update time")
    expires_at: datetime = Field(..., description="Token expiration time")


# Database Models (Firestore Documents)
class TokenData(BaseModel):
    """Token data stored in Firestore"""
    token: str = Field(..., description="Processing token")
    user_id: str = Field(..., description="User ID")
    status: ProcessingStatus = Field(..., description="Processing status")
    progress: ProcessingProgress = Field(..., description="Progress information")
    
    # Result data
    result: Optional[ReceiptAnalysis] = Field(None)
    error: Optional[ErrorDetail] = Field(None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Token expiration time")
    
    # Processing metadata
    retry_count: int = Field(default=0, description="Number of retry attempts")
    processing_start_time: Optional[datetime] = Field(None)
    processing_end_time: Optional[datetime] = Field(None)


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "unhealthy"] = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0", description="API version")
    
    services: Dict[str, Literal["healthy", "unhealthy", "degraded"]] = Field(
        default={}, description="Individual service health status"
    )
    
    metrics: Dict[str, Any] = Field(default={}, description="Health metrics")


# Error Response Models
class ValidationError(BaseModel):
    """Validation error response"""
    error: str = Field(default="Validation Error")
    message: str = Field(..., description="Error message")
    details: List[Dict[str, Any]] = Field(..., description="Validation error details")


class APIError(BaseModel):
    """Generic API error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")