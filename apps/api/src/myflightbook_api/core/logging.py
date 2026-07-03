from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from myflightbook_api.core.config import get_settings

_REQUEST_CONTEXT: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("request_context", default={})
access_logger = logging.getLogger("myflightbook.access")


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(_REQUEST_CONTEXT.get())
        payload.update(getattr(record, "extra_fields", {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


class DevelopmentLogFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        context = {**_REQUEST_CONTEXT.get(), **getattr(record, "extra_fields", {})}
        context_suffix = ""
        if context:
            rendered_context = " ".join(f"{key}={value}" for key, value in sorted(context.items()))
            context_suffix = f" | {rendered_context}"
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        return f"{color}[{record.levelname.lower():>8}] {record.name}: {message}{context_suffix}{self.RESET}"


def _configure_intercepted_loggers() -> None:
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
    ):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


def _initialize_sentry() -> None:
    settings = get_settings()
    if not settings.sentry_dsn:
        return

    try:
        import sentry_sdk
    except ImportError:
        logging.getLogger(__name__).warning(
            "Sentry DSN is configured but sentry-sdk is not installed",
            extra={"extra_fields": {"sentry_dsn_configured": True}},
        )
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or ("development" if settings.debug else "production"),
        traces_sample_rate=0.0,
    )


def setup_logging(app: FastAPI) -> None:
    if getattr(app.state, "logging_configured", False):
        return

    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DevelopmentLogFormatter() if settings.debug else StructuredLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    root_logger.addHandler(handler)

    logging.captureWarnings(True)
    _configure_intercepted_loggers()
    _initialize_sentry()
    app.state.logging_configured = True


class LoggingMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        context = {
            "client_ip": self._client_ip(request),
            "method": request.method,
            "path": request.url.path,
            "request_id": request_id,
        }
        token = _REQUEST_CONTEXT.set(context)
        request.state.request_id = request_id
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            access_logger.exception(
                "http_request_failed",
                extra={"extra_fields": {"duration_ms": duration_ms}},
            )
            raise
        finally:
            if "response" not in locals():
                _REQUEST_CONTEXT.reset(token)

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        access_logger.info(
            "http_request_completed",
            extra={
                "extra_fields": {
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                }
            },
        )
        _REQUEST_CONTEXT.reset(token)
        return response
