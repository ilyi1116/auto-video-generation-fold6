"""
GraphQL Schema 定義
整合所有微服務的資料模型，提供統一的 GraphQL API
"""

from typing import List, Optional

import httpx
import strawberry
import structlog

from .config import get_settings
from .types import AIScript, TrendAnalysis, User, VideoProject

logger = structlog.get_logger()


@strawberry.type
class Query:
    """GraphQL 查詢類型"""

    @strawberry.field
    async def user(self, id: strawberry.ID) -> Optional[User]:
        """獲取單一用戶資訊"""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.AUTH_SERVICE_URL}/users/{id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return User(**data)
                return None
            except Exception as e:
                logger.error("獲取用戶失敗", user_id=id, error=str(e))
                return None

    @strawberry.field
    async def video_projects(
        self,
        user_id: strawberry.ID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[VideoProject]:
        """獲取影片專案列表"""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            try:
                params = {"user_id": user_id, "limit": limit, "offset": offset}
                if status:
                    params["status"] = status

                response = await client.get(
                    f"{settings.VIDEO_SERVICE_URL}/projects", params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        VideoProject(**item)
                        for item in data.get("projects", [])
                    ]
                return []
            except Exception as e:
                logger.error("獲取影片專案失敗", user_id=user_id, error=str(e))
                return []

    @strawberry.field
    async def ai_scripts(
        self, user_id: strawberry.ID, limit: int = 10
    ) -> List[AIScript]:
        """獲取 AI 腳本列表"""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.AI_SERVICE_URL}/scripts",
                    params={"user_id": user_id, "limit": limit},
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        AIScript(**item) for item in data.get("scripts", [])
                    ]
                return []
            except Exception as e:
                logger.error("獲取 AI 腳本失敗", user_id=user_id, error=str(e))
                return []

    @strawberry.field
    async def trending_topics(self, limit: int = 10) -> List[TrendAnalysis]:
        """獲取趨勢主題"""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.TREND_SERVICE_URL}/trending",
                    params={"limit": limit},
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        TrendAnalysis(**item)
                        for item in data.get("trends", [])
                    ]
                return []
            except Exception as e:
                logger.error("獲取趨勢主題失敗", error=str(e))
                return []


@strawberry.type
class Mutation:
    """GraphQL 變更類型"""

    @strawberry.field
    async def create_video_project(
        self,
        user_id: strawberry.ID,
        title: str,
        description: Optional[str] = None,
    ) -> Optional[VideoProject]:
        """建立新的影片專案"""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                }

                response = await client.post(
                    f"{settings.VIDEO_SERVICE_URL}/projects", json=payload
                )

                if response.status_code == 201:
                    data = response.json()
                    return VideoProject(**data)
                return None
            except Exception as e:
                logger.error("建立影片專案失敗", user_id=user_id, error=str(e))
                return None

    @strawberry.field
    async def generate_ai_script(
        self,
        user_id: strawberry.ID,
        topic: str,
        platform: str = "youtube",
        duration: int = 60,
    ) -> Optional[AIScript]:
        """生成 AI 腳本"""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "user_id": user_id,
                    "topic": topic,
                    "platform": platform,
                    "duration": duration,
                }

                response = await client.post(
                    f"{settings.AI_SERVICE_URL}/generate-script", json=payload
                )

                if response.status_code == 201:
                    data = response.json()
                    return AIScript(**data)
                return None
            except Exception as e:
                logger.error("生成 AI 腳本失敗", user_id=user_id, error=str(e))
                return None


# 建立 GraphQL Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
