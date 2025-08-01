import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import requests

from .celery_app import celery_app
from .config import settings
from .database import SessionLocal
from .models import PlatformAccount, ScheduledPost

logger = logging.getLogger(__name__)


@celery_app.task
def check_scheduled_posts():
    """檢查並執行到期的排程發布"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        pending_posts = (
            db.query(ScheduledPost)
            .filter(
                ScheduledPost.status == "pending",
                ScheduledPost.scheduled_time <= now,
            )
            .all()
        )

        for post in pending_posts:
            try:
                publish_post.delay(post.id)
                logger.info(f"Triggered publish task for post {post.id}")
            except Exception as e:
                logger.error(
                    f"Failed to trigger publish for post {post.id}: {e}"
                )

    except Exception as e:
        logger.error(f"Error checking scheduled posts: {e}")
    finally:
        db.close()


@celery_app.task
def publish_post(post_id: int):
    """執行實際的發布操作"""
    db = SessionLocal()
    try:
        post = (
            db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
        )
        if not post:
            logger.error(f"Post {post_id} not found")
            return

        if post.status != "pending":
            logger.warning(
                f"Post {post_id} status is not pending: {post.status}"
            )
            return

        # 獲取平台帳號資訊
        platform_account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.user_id == post.user_id,
                PlatformAccount.platform == post.platform,
                PlatformAccount.is_active is True,
            )
            .first()
        )

        if not platform_account:
            post.status = "failed"
            post.error_message = "Platform account not found or inactive"
            db.commit()
            return

        # 發布到對應平台
        result = None
        if post.platform == "tiktok":
            result = publish_to_tiktok(post, platform_account)
        elif post.platform == "youtube":
            result = publish_to_youtube(post, platform_account)
        elif post.platform == "instagram":
            result = publish_to_instagram(post, platform_account)
        else:
            post.status = "failed"
            post.error_message = f"Unsupported platform: {post.platform}"
            db.commit()
            return

        if result["success"]:
            post.status = "published"
            post.post_url = result.get("post_url")
            post.published_at = datetime.utcnow()
            logger.info(f"Successfully published post {post_id}")
        else:
            post.status = "failed"
            post.error_message = result.get("error", "Unknown error")
            logger.error(
                f"Failed to publish post {post_id}: {post.error_message}"
            )

        db.commit()

    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {e}")
        if post:
            post.status = "failed"
            post.error_message = str(e)
            db.commit()
    finally:
        db.close()


def publish_to_tiktok(
    post: ScheduledPost, account: PlatformAccount
) -> Dict[str, Any]:
    """發布到 TikTok"""
    try:
        # 調用 social-service API
        response = requests.post(
            f"{settings.SOCIAL_SERVICE_URL}/api/v1/platforms/tiktok/publish",
            json={
                "video_id": post.video_id,
                "access_token": account.access_token,
                "title": post.title,
                "description": post.description,
                "tags": post.tags,
                "settings": post.platform_settings,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return {"success": True, "post_url": data.get("post_url")}
        else:
            return {
                "success": False,
                "error": f"TikTok API error: {response.text}",
            }

    except Exception as e:
        return {"success": False, "error": f"TikTok publish error: {str(e)}"}


def publish_to_youtube(
    post: ScheduledPost, account: PlatformAccount
) -> Dict[str, Any]:
    """發布到 YouTube"""
    try:
        response = requests.post(
            f"{settings.SOCIAL_SERVICE_URL}/api/v1/platforms/youtube/publish",
            json={
                "video_id": post.video_id,
                "access_token": account.access_token,
                "title": post.title,
                "description": post.description,
                "tags": post.tags,
                "settings": post.platform_settings,
            },
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            return {"success": True, "post_url": data.get("post_url")}
        else:
            return {
                "success": False,
                "error": f"YouTube API error: {response.text}",
            }

    except Exception as e:
        return {"success": False, "error": f"YouTube publish error: {str(e)}"}


def publish_to_instagram(
    post: ScheduledPost, account: PlatformAccount
) -> Dict[str, Any]:
    """發布到 Instagram"""
    try:
        response = requests.post(
            f"{settings.SOCIAL_SERVICE_URL}/api/v1/platforms/instagram/publish",
            json={
                "video_id": post.video_id,
                "access_token": account.access_token,
                "title": post.title,
                "description": post.description,
                "tags": post.tags,
                "settings": post.platform_settings,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return {"success": True, "post_url": data.get("post_url")}
        else:
            return {
                "success": False,
                "error": f"Instagram API error: {response.text}",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Instagram publish error: {str(e)}",
        }


@celery_app.task
def cleanup_old_posts():
    """清理舊的已發布或失敗的記錄"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = (
            db.query(ScheduledPost)
            .filter(
                ScheduledPost.status.in_(["published", "failed"]),
                ScheduledPost.updated_at < cutoff_date,
            )
            .delete()
        )

        db.commit()
        logger.info(f"Cleaned up {deleted_count} old scheduled posts")

    except Exception as e:
        logger.error(f"Error cleaning up old posts: {e}")
    finally:
        db.close()
