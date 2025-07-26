"""
Health check API endpoints for Project Raseed
Provides comprehensive health monitoring and diagnostics
"""

from fastapi import APIRouter, Request
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import HealthCheckResponse


settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(request: Request):
    """
    Comprehensive health check endpoint

    Returns the health status of all system components including:
    - Overall system health
    - Individual service health (Firestore, Vertex AI, Token Service)
    - Performance metrics
    - System information
    """
    try:
        logger.info(
            "Health check requested",
            extra={
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # Check all services using app.state instances
        firestore_health = await request.app.state.firestore.health_check()
        vertex_ai_health = await request.app.state.vertex_ai.health_check()
        token_service_health = await request.app.state.token_service.health_check()

        # Determine overall health
        service_statuses = {
            "firestore": firestore_health.get("status", "unknown"),
            "vertex_ai": vertex_ai_health.get("status", "unknown"),
            "token_service": token_service_health.get("status", "unknown"),
        }

        overall_status = (
            "healthy"
            if all(status == "healthy" for status in service_statuses.values())
            else "unhealthy"
        )

        # Collect metrics
        metrics = {
            "uptime_seconds": _get_uptime_seconds(),
            "memory_usage_mb": _get_memory_usage_mb(),
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG,
            "firestore_latency_ms": firestore_health.get("latency_ms", 0),
            "vertex_ai_latency_ms": vertex_ai_health.get("latency_ms", 0),
            "processing_stats": token_service_health.get("processing_stats", {}),
        }

        response = HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services=service_statuses,
            metrics=metrics,
        )

        logger.info(
            "Health check completed",
            extra={"overall_status": overall_status, "services": service_statuses},
        )

        return response

    except Exception as e:
        logger.error(f"Health check failed: {e}")

        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            services={"system": "unhealthy"},
            metrics={"error": str(e)},
        )


@router.get("/health/services")
async def detailed_health_check(request: Request):
    """
    Detailed health check with individual service information

    Provides granular health information for debugging and monitoring
    """
    try:
        # Get detailed health info from each service
        firestore_details = await request.app.state.firestore.health_check()
        vertex_ai_details = await request.app.state.vertex_ai.health_check()
        token_service_details = await request.app.state.token_service.health_check()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "firestore": firestore_details,
                "vertex_ai": vertex_ai_details,
                "token_service": token_service_details,
            },
            "system_info": {
                "environment": settings.ENVIRONMENT,
                "debug_mode": settings.DEBUG,
                "project_id": settings.GOOGLE_CLOUD_PROJECT_ID,
                "vertex_ai_location": settings.VERTEX_AI_LOCATION,
                "emulator_mode": {
                    "firestore": settings.use_firestore_emulator,
                    "vertex_ai": settings.use_vertex_ai_mock,
                },
            },
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "error": "Health check failed",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/health/ready")
async def readiness_check(request: Request):
    """
    Kubernetes/Cloud Run readiness check

    Simple endpoint to check if the service is ready to accept traffic
    """
    try:
        # Basic connectivity checks
        firestore_ready = (await request.app.state.firestore.health_check()).get(
            "status"
        ) == "healthy"
        vertex_ai_ready = (await request.app.state.vertex_ai.health_check()).get(
            "status"
        ) == "healthy"

        if firestore_ready and vertex_ai_ready:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            return {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "firestore": "ready" if firestore_ready else "not_ready",
                    "vertex_ai": "ready" if vertex_ai_ready else "not_ready",
                },
            }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes/Cloud Run liveness check

    Simple endpoint to check if the service is alive and responding
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "raseed-receipt-processor",
        "version": "1.0.0",
    }


# Helper functions
def _get_uptime_seconds() -> float:
    """Get application uptime in seconds"""
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        return (
            datetime.now() - datetime.fromtimestamp(process.create_time())
        ).total_seconds()
    except Exception:
        return 0.0


def _get_memory_usage_mb() -> float:
    """Get current memory usage in MB"""
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except Exception:
        return 0.0
