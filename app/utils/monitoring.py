"""
Monitoring and metrics utilities for Project Raseed
Provides comprehensive performance monitoring and health tracking
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import time
from collections import defaultdict, deque

from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collect and track performance metrics"""

    def __init__(self):
        self.metrics = defaultdict(dict)
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
        self.request_times = deque(maxlen=1000)  # Keep last 1000 requests
        self._start_time = time.time()

    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = self._build_metric_key(name, labels)
        self.counters[key] += 1
        logger.debug(f"Counter incremented: {key}")

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        key = self._build_metric_key(name, labels)
        self.histograms[key].append(value)

        # Keep only recent values (last 1000)
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]

        logger.debug(f"Histogram recorded: {key} = {value}")

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        key = self._build_metric_key(name, labels)
        self.gauges[key] = value
        logger.debug(f"Gauge set: {key} = {value}")

    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record request metrics"""
        self.request_times.append({
            'timestamp': time.time(),
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration
        })

        # Update metrics
        self.increment_counter("http_requests_total", {
            "method": method,
            "status": str(status_code)
        })

        self.record_histogram("http_request_duration_seconds", duration, {
            "method": method,
            "path": path
        })

    def record_processing_event(self, event: str, user_id: str, duration: Optional[float] = None):
        """Record receipt processing events"""
        self.increment_counter("receipt_processing_events_total", {
            "event": event,
            "user_type": self._classify_user(user_id)
        })

        if duration is not None:
            self.record_histogram("receipt_processing_duration_seconds", duration, {
                "stage": event
            })

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        try:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    key: {
                        "count": len(values),
                        "mean": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "p95": self._percentile(values, 0.95) if values else 0,
                        "p99": self._percentile(values, 0.99) if values else 0
                    }
                    for key, values in self.histograms.items()
                },
                "uptime_seconds": time.time() - self._start_time,
                "recent_requests": self._get_request_stats()
            }
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}

    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build metric key with labels"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _classify_user(self, user_id: str) -> str:
        """Classify user type for metrics"""
        if user_id.startswith("dev_"):
            return "development"
        elif user_id.startswith("test_"):
            return "test"
        else:
            return "regular"

    def _percentile(self, values: list, p: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        if index >= len(sorted_values):
            return sorted_values[-1]
        return sorted_values[index]

    def _get_request_stats(self) -> Dict[str, Any]:
        """Get recent request statistics"""
        if not self.request_times:
            return {}

        recent_requests = list(self.request_times)
        total_requests = len(recent_requests)

        if total_requests == 0:
            return {}

        # Calculate success rate (2xx status codes)
        successful = sum(1 for req in recent_requests if 200 <= req['status_code'] < 300)
        success_rate = (successful / total_requests) * 100

        # Calculate average response time
        avg_response_time = sum(req['duration'] for req in recent_requests) / total_requests

        # Calculate requests per minute (last 5 minutes)
        five_min_ago = time.time() - 300
        recent_count = sum(1 for req in recent_requests if req['timestamp'] > five_min_ago)
        rpm = recent_count / 5

        return {
            "total_requests": total_requests,
            "success_rate_percent": round(success_rate, 2),
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_per_minute": round(rpm, 2),
            "status_distribution": self._get_status_distribution(recent_requests)
        }

    def _get_status_distribution(self, requests: list) -> Dict[str, int]:
        """Get distribution of status codes"""
        distribution = defaultdict(int)
        for req in requests:
            status_range = f"{req['status_code'] // 100}xx"
            distribution[status_range] += 1
        return dict(distribution)


class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self):
        self.health_history = deque(maxlen=100)  # Keep last 100 health checks
        self.last_check_time = None
        self.consecutive_failures = 0

    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        check_start = time.time()

        try:
            # Import here to avoid circular imports
            from app.services.firestore_service import firestore_service
            from app.services.vertex_ai_service import vertex_ai_service
            from app.services.token_service import token_service

            # Check all services
            health_checks = await asyncio.gather(
                firestore_service.health_check(),
                vertex_ai_service.health_check(),
                token_service.health_check(),
                return_exceptions=True
            )

            firestore_health, vertex_ai_health, token_service_health = health_checks

            # Handle exceptions
            if isinstance(firestore_health, Exception):
                firestore_health = {"status": "unhealthy", "error": str(firestore_health)}
            if isinstance(vertex_ai_health, Exception):
                vertex_ai_health = {"status": "unhealthy", "error": str(vertex_ai_health)}
            if isinstance(token_service_health, Exception):
                token_service_health = {"status": "unhealthy", "error": str(token_service_health)}

            # Determine overall health
            service_statuses = {
                "firestore": firestore_health.get("status", "unknown"),
                "vertex_ai": vertex_ai_health.get("status", "unknown"),
                "token_service": token_service_health.get("status", "unknown")
            }

            overall_healthy = all(status == "healthy" for status in service_statuses.values())
            overall_status = "healthy" if overall_healthy else "unhealthy"

            # Calculate check duration
            check_duration = time.time() - check_start

            # Build health response
            health_data = {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "check_duration_ms": round(check_duration * 1000, 2),
                "services": {
                    "firestore": firestore_health,
                    "vertex_ai": vertex_ai_health,
                    "token_service": token_service_health
                },
                "system": {
                    "uptime_seconds": self._get_uptime(),
                    "memory_usage_mb": self._get_memory_usage(),
                    "cpu_usage_percent": self._get_cpu_usage()
                }
            }

            # Update health history
            self._update_health_history(overall_healthy)

            # Add health trends
            health_data["trends"] = self._get_health_trends()

            return health_data

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._update_health_history(False)

            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "check_duration_ms": round((time.time() - check_start) * 1000, 2)
            }

    def _update_health_history(self, is_healthy: bool):
        """Update health check history"""
        self.health_history.append({
            "timestamp": time.time(),
            "healthy": is_healthy
        })

        self.last_check_time = time.time()

        if is_healthy:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

    def _get_health_trends(self) -> Dict[str, Any]:
        """Calculate health trends from history"""
        if not self.health_history:
            return {}

        recent_checks = list(self.health_history)[-20:]  # Last 20 checks
        total_checks = len(recent_checks)
        healthy_checks = sum(1 for check in recent_checks if check["healthy"])

        return {
            "success_rate_percent": round((healthy_checks / total_checks) * 100, 2),
            "consecutive_failures": self.consecutive_failures,
            "last_failure": self._get_last_failure_time(),
            "total_checks": len(self.health_history)
        }

    def _get_last_failure_time(self) -> Optional[str]:
        """Get timestamp of last health check failure"""
        for check in reversed(self.health_history):
            if not check["healthy"]:
                return datetime.fromtimestamp(check["timestamp"]).isoformat()
        return None

    def _get_uptime(self) -> float:
        """Get application uptime in seconds"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return time.time() - process.create_time()
        except Exception:
            return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.cpu_percent()
        except Exception:
            return 0.0


class PerformanceTracker:
    """Track and analyze performance metrics"""

    def __init__(self):
        self.operation_timings = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)

    def track_operation(self, operation: str, duration: float, success: bool = True):
        """Track operation performance"""
        self.operation_timings[operation].append({
            'duration': duration,
            'timestamp': time.time(),
            'success': success
        })

        # Keep only recent data (last 1000 operations per type)
        if len(self.operation_timings[operation]) > 1000:
            self.operation_timings[operation] = self.operation_timings[operation][-1000:]

        # Update counters
        if success:
            self.success_counts[operation] += 1
        else:
            self.error_counts[operation] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all operations"""
        summary = {}

        for operation, timings in self.operation_timings.items():
            if not timings:
                continue

            durations = [t['duration'] for t in timings]
            success_rate = self.success_counts[operation] / (
                self.success_counts[operation] + self.error_counts[operation]
            ) * 100 if (self.success_counts[operation] + self.error_counts[operation]) > 0 else 0

            summary[operation] = {
                'total_operations': len(timings),
                'success_rate_percent': round(success_rate, 2),
                'avg_duration_ms': round(sum(durations) / len(durations) * 1000, 2),
                'min_duration_ms': round(min(durations) * 1000, 2),
                'max_duration_ms': round(max(durations) * 1000, 2),
                'p95_duration_ms': round(self._percentile(durations, 0.95) * 1000, 2),
                'errors': self.error_counts[operation]
            }

        return summary

    def _percentile(self, values: list, p: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        if index >= len(sorted_values):
            return sorted_values[-1]
        return sorted_values[index]


# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
performance_tracker = PerformanceTracker()
