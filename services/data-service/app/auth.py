import httpx
from fastapi import HTTPException
import structlog

logger = structlog.get_logger(__name__)

AUTH_SERVICE_URL = "http://auth-service:8001"


async def get_current_user(token: str) -> int:
    """Verify JWT token with auth service and return user ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/v1/me", headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                user_data = response.json()
                return user_data["id"]
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid token")
            elif response.status_code == 403:
                raise HTTPException(status_code=403, detail="Token required")
            else:
                raise HTTPException(status_code=401, detail="Authentication failed")

    except httpx.RequestError as e:
        logger.error("Failed to verify token with auth service", error=str(e))
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during token verification", error=str(e))
        raise HTTPException(status_code=500, detail="Internal authentication error")
