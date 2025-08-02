"""
Voice Enhancement Service 身份驗證
"""

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

        # 模擬用戶數據（實際應用中從資料庫獲取）
        user_data = {
            "id": user_id,
            "username": payload.get("username", "user"),
            "email": payload.get("email", "user@example.com"),
        }

        return user_data

    except JWTError as e:
        logger.error("JWT 驗證失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="無效的認證憑證"
        )
    except Exception as e:
        logger.error("用戶認證失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認證服務錯誤",
        )
