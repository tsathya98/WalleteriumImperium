#!/usr/bin/env python3
"""
Project Raseed - AI-Powered Receipt Management Backend
Main FastAPI application entry point for Google Cloud Run deployment
"""

import os
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api import receipts, health
from app.api import onboarding as onboarding_api
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.firestore_service import FirestoreService
from app.services.token_service import TokenService

# Setup logging
setup_logging(settings.LOG_LEVEL)

# Global metrics collector
from app.utils.monitoring import MetricsCollector

metrics = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI application"""
    try:
        print("🚀 Starting Raseed Receipt Processor")

        # Initialize Firestore service
        firestore_service = FirestoreService()
        await firestore_service.initialize()
        app.state.firestore = firestore_service

        # Initialize Token service (SYNC VERSION)
        token_service = TokenService(firestore_service=firestore_service)
        await token_service.initialize()  # Sync initialization
        app.state.token_service = token_service

        print("✅ All services initialized successfully")

        yield

    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        raise
    finally:
        print("🛑 Shutting down services...")
        # Cleanup if needed
        if hasattr(app.state, "token_service"):
            await app.state.token_service.shutdown()


# Create FastAPI application
app = FastAPI(
    title="WalleteriumImperium Receipt Analysis API",
    description="AI-powered receipt analysis using Google Cloud Vertex AI and Gemini 2.5 Flash",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log request
    print(
        f"📝 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
    )

    # Record metrics
    metrics.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=process_time,
    )

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": request.url.path,
        },
    )


# Include routers
app.include_router(receipts.router, prefix="/api/v1/receipts", tags=["receipts"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(
    onboarding_api.router, prefix="/api/v1/onboarding", tags=["onboarding"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WalleteriumImperium Receipt Analysis API",
        "version": "2.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return metrics.get_metrics_summary()


if __name__ == "__main__":
    print("🚀 Starting WalleteriumImperium Receipt Processor...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"📁 Log Level: {settings.LOG_LEVEL}")

    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
