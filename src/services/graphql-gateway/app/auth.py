"""
GraphQL Gateway 身份驗證
"""

from typing import Optional

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import get_settings

logger = structlog.get_logger()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """獲取當前用戶資訊"""
    settings = get_settings()

    try:
        # 驗證 JWT Token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的認證憑證",
            )

        # 從認證服務驗證用戶
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/users/{user_id}",
                headers={"Authorization": f"Bearer {credentials.credentials}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用戶認證失敗",
                )

            user_data = response.json()
            return user_data

    except JWTError as e:
        logger.error("JWT 驗證失敗", error=str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="無效的認證憑證")
    except Exception as e:
        logger.error("用戶認證失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認證服務錯誤",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """獲取可選的用戶資訊（允許匿名訪問）"""
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
