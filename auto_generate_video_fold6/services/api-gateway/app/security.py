from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from .config import settings

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        if settings.security_headers_enabled:
            # HSTS (HTTP Strict Transport Security)
            if settings.ssl_enabled:
                response.headers["Strict-Transport-Security"] = f"max-age={settings.hsts_max_age}; includeSubDomains; preload"
            
            # Content Security Policy
            response.headers["Content-Security-Policy"] = settings.csp_policy
            
            # X-Frame-Options
            response.headers["X-Frame-Options"] = "DENY"
            
            # X-Content-Type-Options
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # X-XSS-Protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions Policy
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), payment=(), "
                "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
            )
            
            # Cross-Origin Policies
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
            
            # Remove server information
            response.headers.pop("Server", None)
            
            # Add custom security headers
            response.headers["X-Security-Version"] = "1.0"
            response.headers["X-Powered-By"] = "Auto Video Generation System"
        
        return response


class TrustedProxyMiddleware(BaseHTTPMiddleware):
    """Middleware to handle trusted proxy headers"""
    
    def __init__(self, app, trusted_proxies: list = None):
        super().__init__(app)
        self.trusted_proxies = trusted_proxies or ["127.0.0.1", "::1"]
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP from X-Forwarded-For header if from trusted proxy
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        
        if forwarded_for and client_ip in self.trusted_proxies:
            # Take the first IP from X-Forwarded-For chain
            real_ip = forwarded_for.split(",")[0].strip()
            request.scope["client"] = (real_ip, request.client.port)
        
        # Handle X-Forwarded-Proto for HTTPS detection
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto == "https":
            request.scope["scheme"] = "https"
        
        response = await call_next(request)
        return response


def validate_ssl_config():
    """Validate SSL configuration"""
    if settings.ssl_enabled:
        import os
        
        if not os.path.exists(settings.ssl_cert_path):
            logger.error("SSL certificate file not found", path=settings.ssl_cert_path)
            raise FileNotFoundError(f"SSL certificate not found: {settings.ssl_cert_path}")
        
        if not os.path.exists(settings.ssl_key_path):
            logger.error("SSL private key file not found", path=settings.ssl_key_path)
            raise FileNotFoundError(f"SSL private key not found: {settings.ssl_key_path}")
        
        logger.info("SSL configuration validated successfully")
    else:
        logger.warning("SSL is disabled - this is not recommended for production")


def get_ssl_context():
    """Get SSL context for HTTPS"""
    if not settings.ssl_enabled:
        return None
    
    import ssl
    
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(settings.ssl_cert_path, settings.ssl_key_path)
    
    # Security settings
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS")
    
    return context


class RateLimitSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting with security features"""
    
    def __init__(self, app, redis_client):
        super().__init__(app)
        self.redis = redis_client
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        
        # Check for suspicious patterns
        suspicious_patterns = [
            "/.env", "/admin", "/.git", "/wp-admin", "/phpmyadmin",
            "/config", "/backup", "/test", "/debug"
        ]
        
        if any(pattern in path.lower() for pattern in suspicious_patterns):
            logger.warning("Suspicious request detected", ip=client_ip, path=path)
            # Increase rate limit penalty for suspicious requests
            await self._increment_penalty(client_ip)
        
        # Check rate limit
        if await self._is_rate_limited(client_ip):
            logger.warning("Rate limit exceeded", ip=client_ip)
            return Response("Rate limit exceeded", status_code=429)
        
        response = await call_next(request)
        
        # Log failed authentication attempts
        if response.status_code == 401:
            await self._log_auth_failure(client_ip, path)
        
        return response
    
    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        try:
            key = f"rate_limit:{client_ip}"
            current = await self.redis.get(key)
            
            if current is None:
                await self.redis.setex(key, 60, 1)
                return False
            
            current_count = int(current)
            if current_count >= settings.rate_limit_per_minute:
                return True
            
            await self.redis.incr(key)
            return False
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            return False
    
    async def _increment_penalty(self, client_ip: str):
        """Increase penalty for suspicious behavior"""
        try:
            penalty_key = f"penalty:{client_ip}"
            await self.redis.incr(penalty_key)
            await self.redis.expire(penalty_key, 3600)  # 1 hour penalty
        except Exception as e:
            logger.error("Failed to increment penalty", error=str(e))
    
    async def _log_auth_failure(self, client_ip: str, path: str):
        """Log authentication failures"""
        try:
            fail_key = f"auth_fail:{client_ip}"
            failures = await self.redis.incr(fail_key)
            await self.redis.expire(fail_key, 300)  # 5 minutes
            
            if failures > 5:
                logger.critical("Multiple auth failures detected", ip=client_ip, failures=failures)
        except Exception as e:
            logger.error("Failed to log auth failure", error=str(e))