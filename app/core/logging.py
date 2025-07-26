"""
Logging configuration for Project Raseed
Structured logging with Google Cloud Logging compatibility
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging compatible with Google Cloud Logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Add request context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if hasattr(record, "receipt_id"):
            log_entry["receipt_id"] = record.receipt_id

        return json.dumps(log_entry)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context to log record if available"""
        # This will be populated by middleware
        import contextvars

        try:
            request_id = contextvars.copy_context().get("request_id", None)
            user_id = contextvars.copy_context().get("user_id", None)

            if request_id:
                record.request_id = request_id
            if user_id:
                record.user_id = user_id

        except Exception:
            # If context variables are not available, continue without them
            pass

        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Setup application logging configuration"""

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = StructuredFormatter()

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers_config = {
        "uvicorn": logging.WARNING,
        "uvicorn.access": logging.INFO,
        "fastapi": logging.INFO,
        "google": logging.WARNING,
        "urllib3": logging.WARNING,
        "httpx": logging.WARNING,
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # Application logger
    app_logger = logging.getLogger("raseed")
    app_logger.setLevel(numeric_level)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for structured logging"""

    def __init__(self, logger: logging.Logger, extra_fields: Dict[str, Any] = None):
        self.extra_fields = extra_fields or {}
        super().__init__(logger, {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message with extra fields"""
        # Merge extra fields
        extra = kwargs.get("extra", {})
        extra.update(self.extra_fields)
        kwargs["extra"] = {"extra_fields": extra}

        return msg, kwargs

    def with_fields(self, **fields) -> "LoggerAdapter":
        """Create new adapter with additional fields"""
        new_fields = self.extra_fields.copy()
        new_fields.update(fields)
        return LoggerAdapter(self.logger, new_fields)


def get_logger(name: str, **extra_fields) -> LoggerAdapter:
    """Get structured logger with optional extra fields"""
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, extra_fields)


# Performance monitoring decorator
def log_performance(logger: LoggerAdapter):
    """Decorator to log function performance"""

    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"{func.__name__} completed successfully",
                    extra={
                        "function": func.__name__,
                        "duration_seconds": round(duration, 3),
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "duration_seconds": round(duration, 3),
                        "status": "error",
                        "error": str(e),
                    },
                )

                raise

        return wrapper

    return decorator


# Async performance monitoring decorator
def log_async_performance(logger: LoggerAdapter):
    """Decorator to log async function performance"""

    def decorator(func):
        import functools

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"{func.__name__} completed successfully",
                    extra={
                        "function": func.__name__,
                        "duration_seconds": round(duration, 3),
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "duration_seconds": round(duration, 3),
                        "status": "error",
                        "error": str(e),
                    },
                )

                raise

        return wrapper

    return decorator
