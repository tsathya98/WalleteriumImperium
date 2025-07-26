#!/usr/bin/env python3
"""
Project Raseed - AI-Powered Receipt Management Backend
Main FastAPI application entry point for Google Cloud Run deployment
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime

from app.api import receipts, health
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.firestore_service import FirestoreService
from app.services.vertex_ai_service import get_vertex_ai_service
from app.services.token_service import TokenService
from app.utils.monitoring import MetricsCollector

# Global settings
settings = get_settings()

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize services on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Raseed Receipt Processor")

    # Initialize services
    try:
        # Initialize Firestore service
        firestore_service = FirestoreService()
        await firestore_service.initialize()
        app.state.firestore = firestore_service

        # Initialize vertex AI service
        vertex_ai_service = get_vertex_ai_service()
        app.state.vertex_ai = vertex_ai_service

        # Initialize token service with proper dependencies
        token_service_instance = TokenService(
            firestore_service=firestore_service,
            vertex_ai_service=vertex_ai_service
        )
        await token_service_instance.initialize()
        app.state.token_service = token_service_instance

        metrics_collector = MetricsCollector()
        app.state.metrics = metrics_collector

        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        sys.exit(1)

    yield

    # Cleanup on shutdown
    logger.info("🛑 Shutting down Raseed Receipt Processor")

# Create FastAPI application
app = FastAPI(
    title="Project Raseed - Receipt Processor API",
    description="AI-powered receipt management system for Google Wallet",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware for Flutter frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = (datetime.utcnow() - start_time).total_seconds()

    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred while processing your request",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )

# Include API routers
app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"]
)

app.include_router(
    receipts.router,
    prefix="/api/v1/receipts",
    tags=["Receipt Processing"]
)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Raseed Receipt Processor",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs" if settings.DEBUG else None,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
