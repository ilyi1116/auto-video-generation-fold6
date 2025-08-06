import logging

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..platforms import instagram, tiktok, youtube
from ..schemas import (
    OAuthCallback,
    PlatformAuth,
    PublishRequest,
    PublishResponse,
    TokenResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/auth/{platform}", response_model=PlatformAuth)
async def get_auth_url(platform: str):
    """獲取平台授權 URL"""

    if platform == "tiktok":
        auth_url = tiktok.get_auth_url()
        return PlatformAuth(
            platform="tiktok",
            auth_url=auth_url,
            client_id=settings.TIKTOK_CLIENT_ID,
        )
    elif platform == "youtube":
        auth_url = youtube.get_auth_url()
        return PlatformAuth(
            platform="youtube",
            auth_url=auth_url,
            client_id=settings.YOUTUBE_CLIENT_ID,
        )
    elif platform == "instagram":
        auth_url = instagram.get_auth_url()
        return PlatformAuth(
            platform="instagram",
            auth_url=auth_url,
            client_id=settings.INSTAGRAM_CLIENT_ID,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported platform")


@router.post("/auth/{platform}/callback", response_model=TokenResponse)
async def handle_oauth_callback(platform: str, callback: OAuthCallback):
    """處理 OAuth 回調並交換 token"""

    try:
        if platform == "tiktok":
            token_data = await tiktok.exchange_code_for_token(callback.code)
        elif platform == "youtube":
            token_data = await youtube.exchange_code_for_token(callback.code)
        elif platform == "instagram":
            token_data = await instagram.exchange_code_for_token(callback.code)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")

        return TokenResponse(**token_data)

    except Exception as e:
        logger.error(f"OAuth callback error for {platform}: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.post("/tiktok/publish", response_model=PublishResponse)
async def publish_to_tiktok(request: PublishRequest):
    """發布影片到 TikTok"""

    try:
        result = await tiktok.publish_video(
            video_id=request.video_id,
            access_token=request.access_token,
            title=request.title,
            description=request.description,
            tags=request.tags,
            settings=request.settings,
        )

        return PublishResponse(**result)

    except Exception as e:
        logger.error(f"TikTok publish error: {e}")
        return PublishResponse(success=False, error=f"Failed to publish to TikTok: {str(e)}")


@router.post("/youtube/publish", response_model=PublishResponse)
async def publish_to_youtube(request: PublishRequest):
    """發布影片到 YouTube"""

    try:
        result = await youtube.publish_video(
            video_id=request.video_id,
            access_token=request.access_token,
            title=request.title,
            description=request.description,
            tags=request.tags,
            settings=request.settings,
        )

        return PublishResponse(**result)

    except Exception as e:
        logger.error(f"YouTube publish error: {e}")
        return PublishResponse(success=False, error=f"Failed to publish to YouTube: {str(e)}")


@router.post("/instagram/publish", response_model=PublishResponse)
async def publish_to_instagram(request: PublishRequest):
    """發布影片到 Instagram"""

    try:
        result = await instagram.publish_video(
            video_id=request.video_id,
            access_token=request.access_token,
            title=request.title,
            description=request.description,
            tags=request.tags,
            settings=request.settings,
        )

        return PublishResponse(**result)

    except Exception as e:
        logger.error(f"Instagram publish error: {e}")
        return PublishResponse(success=False, error=f"Failed to publish to Instagram: {str(e)}")


@router.get("/status/{platform}")
async def check_platform_status(platform: str):
    """檢查平台 API 狀態"""

    try:
        if platform == "tiktok":
            status = await tiktok.check_api_status()
        elif platform == "youtube":
            status = await youtube.check_api_status()
        elif platform == "instagram":
            status = await instagram.check_api_status()
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")

        return {"platform": platform, "status": status}

    except Exception as e:
        logger.error(f"Platform status check error for {platform}: {e}")
        return {"platform": platform, "status": "error", "error": str(e)}
