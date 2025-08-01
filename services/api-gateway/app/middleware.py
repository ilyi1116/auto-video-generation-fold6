from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
import time
import uuid
from typing import Callable

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured logging with request tracking"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Extract client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Bind request context to logger
        request_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=user_agent,
        )

        # Add request ID to request state
        request.state.request_id = request_id

        # Log request start
        start_time = time.time()
        request_logger.info("Request started")

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log request completion
            request_logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log request error
            request_logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                process_time=f"{process_time:.3f}s",
            )

            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
