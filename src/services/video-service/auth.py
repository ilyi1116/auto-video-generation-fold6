"""
Authentication Module for Video Service

This module handles JWT token validation and user authentication
for the video generation service.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp
import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom authentication error"""


async def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return user ID

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise
    """

    try:
        # Get JWT settings from environment
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "RS256")
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

        if not jwt_secret:
            # If no local JWT secret, validate with auth service
            return await verify_token_remote(token, auth_service_url)

        # Decode and verify token locally
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=[jwt_algorithm],
                options={"verify_exp": True},
            )

            # Extract user ID from payload
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Token missing user ID (sub claim)")
                return None

            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.warning("Token has expired")
                return None

            logger.debug(f"Token validated for user: {user_id}")
            return user_id

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None


async def verify_token_remote(token: str, auth_service_url: str) -> Optional[str]:
    """
    Verify token with remote authentication service

    Args:
        token: JWT token string
        auth_service_url: URL of authentication service

    Returns:
        User ID if token is valid, None otherwise
    """

    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}

            async with session.get(
                f"{auth_service_url}/api/v1/auth/verify",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    user_id = result.get("user_id")

                    if user_id:
                        logger.debug(f"Remote token validated for user: {user_id}")
                        return user_id
                    else:
                        logger.warning("Remote verification returned no user ID")
                        return None

                elif response.status == 401:
                    logger.warning("Token rejected by auth service")
                    return None
                else:
                    logger.error(f"Auth service error: {response.status}")
                    return None

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to auth service: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Remote token verification failed: {str(e)}")
        return None


async def get_user_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed user information from token

    Args:
        token: JWT token string

    Returns:
        User information dictionary if successful, None otherwise
    """

    try:
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}

            async with session.get(
                f"{auth_service_url}/api/v1/auth/me",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    logger.debug(f"Retrieved user info for: {user_info.get('id')}")
                    return user_info
                else:
                    logger.warning(f"Failed to get user info: {response.status}")
                    return None

    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}")
        return None


def create_service_token(service_name: str, expires_in: int = 3600) -> str:
    """
    Create internal service-to-service JWT token

    Args:
        service_name: Name of the service
        expires_in: Token expiration time in seconds

    Returns:
        JWT token string
    """

    try:
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            raise AuthenticationError("JWT secret not configured")

        payload = {
            "sub": f"service:{service_name}",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "type": "service",
            "service": service_name,
        }

        token = jwt.encode(payload, jwt_secret, algorithm=os.getenv("JWT_ALGORITHM", "RS256"))

        logger.debug(f"Created service token for: {service_name}")
        return token

    except Exception as e:
        logger.error(f"Failed to create service token: {str(e)}")
        raise AuthenticationError(f"Failed to create service token: {str(e)}")


async def check_user_permissions(user_id: str, resource: str, action: str) -> bool:
    """
    Check if user has permission to perform action on resource

    Args:
        user_id: User identifier
        resource: Resource name (e.g., "video_project")
        action: Action name (e.g., "create", "read", "update", "delete")

    Returns:
        True if user has permission, False otherwise
    """

    try:
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        service_token = create_service_token("video-service")

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {service_token}"}

            payload = {
                "user_id": user_id,
                "resource": resource,
                "action": action,
            }

            async with session.post(
                f"{auth_service_url}/api/v1/auth/permissions/check",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    has_permission = result.get("allowed", False)

                    logger.debug(
                        f"Permission check for {user_id}: {resource} \
                            .{action} = {has_permission}"
                    )
                    return has_permission
                else:
                    logger.warning(f"Permission check failed: {response.status}")
                    return False

    except Exception as e:
        logger.error(f"Permission check failed: {str(e)}")
        return False


def require_authentication(func):
    """
    Decorator to require authentication for a function
    """

    async def wrapper(*args, **kwargs):
        # This would be used with FastAPI dependency injection
        # Implementation depends on specific FastAPI patterns
        return await func(*args, **kwargs)

    return wrapper


def get_token_from_header(authorization: str) -> Optional[str]:
    """
    Extract token from Authorization header

    Args:
        authorization: Authorization header value

    Returns:
        Token string if valid format, None otherwise
    """

    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None


class TokenValidator:
    """Token validation utility class"""

    def __init__(self, jwt_secret: str, algorithm: str = "RS256"):
        self.jwt_secret = jwt_secret
        self.algorithm = algorithm

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate token and return payload

        Args:
            token: JWT token string

        Returns:
            Token payload dictionary

        Raises:
            HTTPException: If token is invalid
        """

        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm],
                options={"verify_exp": True},
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    async def validate_service_token(self, token: str, required_service: str) -> bool:
        """
        Validate service-to-service token

        Args:
            token: JWT token string
            required_service: Required service name

        Returns:
            True if valid service token, False otherwise
        """

        try:
            payload = await self.validate_token(token)

            token_type = payload.get("type")
            service_name = payload.get("service")

            return token_type == "service" and service_name == required_service

        except HTTPException:
            return False


# Global token validator instance
_token_validator = None


def get_token_validator() -> TokenValidator:
    """Get global token validator instance"""

    global _token_validator

    if _token_validator is None:
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            raise AuthenticationError("JWT secret not configured")

        jwt_algorithm = os.getenv("JWT_ALGORITHM", "RS256")
        _token_validator = TokenValidator(jwt_secret, jwt_algorithm)

    return _token_validator
