from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import structlog
from .config import settings

logger = structlog.get_logger()
security_scheme = HTTPBearer()


def verify_token_locally(token: str) -> dict:
    """Verify JWT token locally"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
        return {"email": email, "id": payload.get("user_id")}
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        user_data = verify_token_locally(token)

        if user_data is None:
            raise credentials_exception

        return user_data

    except Exception as e:
        logger.error("Token verification error", error=str(e))
        raise credentials_exception
