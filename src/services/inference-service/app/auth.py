import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import get_settings

logger = structlog.get_logger()
security = HTTPBearer()
settings = get_settings()


async def verify_token(token: str) -> dict:
    """Verify JWT token with auth service"""
    try:
        # First try to decode locally
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        # If local verification fails, check with auth service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/verify",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication token",
                    )
        except httpx.RequestError as e:
            logger.error("Auth service connection failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = await verify_token(token)

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return {
            "id": int(user_id),
            "username": payload.get("username"),
            "email": payload.get("email"),
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
