import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

logger = structlog.get_logger()
security_scheme = HTTPBearer()


async def verify_token_with_auth_service(token: str) -> dict:
    """Verify token with authentication service"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    "Token verification failed",
                    status_code=response.status_code,
                    response=response.text,
                )
                return None

        except httpx.RequestError as e:
            logger.error(
                "Failed to verify token with auth service",
                error=str(e)
            )
            return None


def verify_token_locally(token: str) -> dict:
    """Verify JWT token locally (fallback)"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
        return {"email": email}
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials

        # First try to verify with auth service
        user_data = await verify_token_with_auth_service(token)

        # If auth service is unavailable, verify locally
        if user_data is None:
            logger.warning(
                "Auth service unavailable, using local verification"
            )
            user_data = verify_token_locally(token)

        if user_data is None:
            raise credentials_exception

        return user_data

    except Exception as e:
        logger.error("Token verification error", error=str(e))
        raise credentials_exception


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    ),
):
    """Get current user if token is provided (optional)"""
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user_data = await verify_token_with_auth_service(token)

        if user_data is None:
            user_data = verify_token_locally(token)

        return user_data
    except Exception:
        return None
