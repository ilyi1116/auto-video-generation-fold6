import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from .config import settings
import structlog

logger = structlog.get_logger()

# Redis connection for rate limiting
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()  # Test connection
    logger.info("Connected to Redis for rate limiting")
except Exception as e:
    logger.error("Failed to connect to Redis", error=str(e))
    redis_client = None


def get_user_identifier(request: Request) -> str:
    """Get user identifier for rate limiting"""
    # Try to get user from token first
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        # In production, decode JWT to get user ID
        # For now, use token as identifier
        return f"user:{token[:10]}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=settings.redis_url if redis_client else "memory://",
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    response = HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after,
        },
    )

    # Log rate limit exceeded
    logger.warning(
        "Rate limit exceeded",
        client_ip=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
        endpoint=request.url.path,
        limit=exc.detail,
    )

    return response
