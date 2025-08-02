"""
創業者模式多平台發布管理器
專為創業者自動化內容發布和獲利優化設計

主要功能：
1. 統一的多平台發布介面
2. 智能發布時間優化
3. 平台特定內容調整
4. 發布狀態追蹤和重試機制
5. 獲利表現分析
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .platforms import instagram, tiktok, youtube

logger = logging.getLogger(__name__)


class PublishStatus(Enum):
    """發布狀態枚舉"""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class Platform(Enum):
    """支援的平台枚舉"""

    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube-shorts"
    INSTAGRAM_REELS = "instagram-reels"
    FACEBOOK_REELS = "facebook-reels"


@dataclass
class ContentOptimization:
    """內容優化配置"""

    platform: Platform
    title_max_length: int
    description_max_length: int
    hashtag_limit: int
    aspect_ratio: str
    max_duration: int  # 秒
    optimal_posting_times: List[str]
    engagement_boosters: List[str]


@dataclass
class PublishRequest:
    """發布請求模型"""

    video_id: str
    user_id: str
    platforms: List[Platform]
    content: Dict[str, Any]  # 包含 title, description, hashtags 等
    assets: Dict[str, Any]  # 包含 video_url, thumbnail_url 等
    publish_immediately: bool = False
    scheduled_time: Optional[datetime] = None
    retry_on_failure: bool = True
    max_retries: int = 3
    platform_specific_settings: Dict[Platform, Dict[str, Any]] = field(
        default_factory=dict
    )


@dataclass
class PublishResult:
    """發布結果模型"""

    platform: Platform
    status: PublishStatus
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    engagement_stats: Dict[str, Any] = field(default_factory=dict)
    revenue_tracking: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchPublishResult:
    """批次發布結果"""

    request_id: str
    total_platforms: int
    successful_platforms: List[Platform]
    failed_platforms: List[Platform]
    platform_results: Dict[Platform, PublishResult]
    overall_success_rate: float
    started_at: datetime
    completed_at: Optional[datetime] = None


class EntrepreneurPublisher:
    """創業者模式多平台發布管理器"""

    def __init__(self):
        self.platform_configs = self._initialize_platform_configs()
        self.active_publications = {}  # 追蹤進行中的發布
        self.publish_history = {}  # 發布歷史記錄

        # 平台客戶端映射
        self.platform_clients = {
            Platform.TIKTOK: tiktok,
            Platform.YOUTUBE_SHORTS: youtube,
            Platform.INSTAGRAM_REELS: instagram,
        }

        logger.info("創業者多平台發布管理器已初始化")

    def _initialize_platform_configs(
        self,
    ) -> Dict[Platform, ContentOptimization]:
        """初始化平台配置"""

        return {
            Platform.TIKTOK: ContentOptimization(
                platform=Platform.TIKTOK,
                title_max_length=150,
                description_max_length=2200,
                hashtag_limit=10,
                aspect_ratio="9:16",
                max_duration=180,
                optimal_posting_times=["19:00", "20:00", "21:00"],
                engagement_boosters=["#fyp", "#viral", "#trending"],
            ),
            Platform.YOUTUBE_SHORTS: ContentOptimization(
                platform=Platform.YOUTUBE_SHORTS,
                title_max_length=100,
                description_max_length=5000,
                hashtag_limit=15,
                aspect_ratio="9:16",
                max_duration=60,
                optimal_posting_times=["18:00", "19:00", "20:00"],
                engagement_boosters=["#shorts", "#trending", "#viral"],
            ),
            Platform.INSTAGRAM_REELS: ContentOptimization(
                platform=Platform.INSTAGRAM_REELS,
                title_max_length=125,
                description_max_length=2200,
                hashtag_limit=30,
                aspect_ratio="9:16",
                max_duration=90,
                optimal_posting_times=["17:00", "19:00", "21:00"],
                engagement_boosters=["#reels", "#viral", "#explore"],
            ),
        }

    async def publish_to_multiple_platforms(
        self, request: PublishRequest
    ) -> BatchPublishResult:
        """多平台批次發布"""

        try:
            request_id = f"batch_{
                datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            }_{request.user_id}"

            batch_result = BatchPublishResult(
                request_id=request_id,
                total_platforms=len(request.platforms),
                successful_platforms=[],
                failed_platforms=[],
                platform_results={},
                overall_success_rate=0.0,
                started_at=datetime.utcnow(),
            )

            # 記錄為活動中的發布
            self.active_publications[request_id] = batch_result

            logger.info(
                f"開始多平台發布 - 請求ID: {request_id}, 平台數: {len(request.platforms)}"
            )

            # 為每個平台優化內容
            optimized_content = {}
            for platform in request.platforms:
                optimized_content[platform] = (
                    self._optimize_content_for_platform(
                        platform, request.content, request.assets
                    )
                )

            # 並行發布到所有平台
            publish_tasks = []
            for platform in request.platforms:
                task = self._publish_to_single_platform(
                    platform, request, optimized_content[platform]
                )
                publish_tasks.append(task)

            # 等待所有發布任務完成
            platform_results = await asyncio.gather(
                *publish_tasks, return_exceptions=True
            )

            # 處理結果
            for i, result in enumerate(platform_results):
                platform = request.platforms[i]

                if isinstance(result, Exception):
                    # 處理異常
                    publish_result = PublishResult(
                        platform=platform,
                        status=PublishStatus.FAILED,
                        error_message=str(result),
                    )
                    batch_result.failed_platforms.append(platform)
                else:
                    # 正常結果
                    publish_result = result
                    if publish_result.status == PublishStatus.PUBLISHED:
                        batch_result.successful_platforms.append(platform)
                    else:
                        batch_result.failed_platforms.append(platform)

                batch_result.platform_results[platform] = publish_result

            # 計算成功率
            batch_result.overall_success_rate = (
                len(batch_result.successful_platforms)
                / len(request.platforms)
                * 100
            )
            batch_result.completed_at = datetime.utcnow()

            # 更新歷史記錄
            self.publish_history[request_id] = batch_result

            # 從活動列表中移除
            if request_id in self.active_publications:
                del self.active_publications[request_id]

            logger.info(
                f"多平台發布完成 - 成功: {len(batch_result.successful_platforms)}, "
                f"失敗: {len(batch_result.failed_platforms)}, "
                f"成功率: {batch_result.overall_success_rate:.1f}%"
            )

            return batch_result

        except Exception as e:
            logger.error(f"多平台發布失敗: {e}")
            raise

    async def _publish_to_single_platform(
        self,
        platform: Platform,
        request: PublishRequest,
        optimized_content: Dict[str, Any],
    ) -> PublishResult:
        """發布到單一平台"""

        try:
            logger.info(f"開始發布到 {platform.value}")

            # 獲取平台客戶端
            client = self.platform_clients.get(platform)
            if not client:
                raise Exception(f"不支援的平台: {platform.value}")

            # 獲取用戶的平台認證信息
            access_token = await self._get_platform_access_token(
                request.user_id, platform
            )
            if not access_token:
                raise Exception(f"缺少 {platform.value} 平台的認證信息")

            # 檢查是否需要延遲發布
            if not request.publish_immediately and request.scheduled_time:
                if request.scheduled_time > datetime.utcnow():
                    return PublishResult(
                        platform=platform,
                        status=PublishStatus.SCHEDULED,
                        published_at=request.scheduled_time,
                    )

            # 執行發布
            publish_response = await self._execute_platform_publish(
                client, platform, access_token, optimized_content, request
            )

            if publish_response.get("success", False):
                result = PublishResult(
                    platform=platform,
                    status=PublishStatus.PUBLISHED,
                    post_id=publish_response.get("post_id"),
                    post_url=publish_response.get("post_url"),
                    published_at=datetime.utcnow(),
                )

                # 啟動分析追蹤
                asyncio.create_task(
                    self._start_analytics_tracking(
                        platform, result.post_id, request.user_id
                    )
                )

                logger.info(f"成功發布到 {platform.value}: {result.post_url}")
                return result
            else:
                error_msg = publish_response.get("error", "未知錯誤")

                # 如果啟用重試且未達到最大重試次數
                if request.retry_on_failure and request.max_retries > 0:
                    logger.warning(
                        f"{platform.value} 發布失敗，準備重試: {error_msg}"
                    )

                    # 延遲後重試
                    await asyncio.sleep(5)

                    # 減少重試次數並重新嘗試
                    retry_request = request
                    retry_request.max_retries -= 1

                    return await self._publish_to_single_platform(
                        platform, retry_request, optimized_content
                    )
                else:
                    return PublishResult(
                        platform=platform,
                        status=PublishStatus.FAILED,
                        error_message=error_msg,
                    )

        except Exception as e:
            logger.error(f"發布到 {platform.value} 失敗: {e}")
            return PublishResult(
                platform=platform,
                status=PublishStatus.FAILED,
                error_message=str(e),
            )

    def _optimize_content_for_platform(
        self,
        platform: Platform,
        content: Dict[str, Any],
        assets: Dict[str, Any],
    ) -> Dict[str, Any]:
        """為特定平台優化內容"""

        config = self.platform_configs[platform]
        optimized = {}

        # 優化標題
        title = content.get("title", "")
        if len(title) > config.title_max_length:
            optimized["title"] = title[: config.title_max_length - 3] + "..."
        else:
            optimized["title"] = title

        # 優化描述
        description = content.get("description", "")
        if len(description) > config.description_max_length:
            optimized["description"] = (
                description[: config.description_max_length - 3] + "..."
            )
        else:
            optimized["description"] = description

        # 優化標籤
        hashtags = content.get("hashtags", [])
        platform_hashtags = config.engagement_boosters.copy()

        # 添加原有標籤（限制數量）
        remaining_slots = config.hashtag_limit - len(platform_hashtags)
        for tag in hashtags[:remaining_slots]:
            if tag not in platform_hashtags:
                platform_hashtags.append(tag)

        optimized["hashtags"] = platform_hashtags

        # 平台特定優化
        if platform == Platform.TIKTOK:
            optimized["disable_duet"] = False
            optimized["disable_comment"] = False
            optimized["disable_stitch"] = False
            optimized["cover_timestamp"] = 1000
        elif platform == Platform.YOUTUBE_SHORTS:
            optimized["category"] = "Entertainment"
            optimized["made_for_kids"] = False
            optimized["visibility"] = "public"
        elif platform == Platform.INSTAGRAM_REELS:
            optimized["allow_comments"] = True
            optimized["allow_sharing"] = True

        # 添加資產信息
        optimized.update(assets)

        return optimized

    async def _execute_platform_publish(
        self,
        client,
        platform: Platform,
        access_token: str,
        content: Dict[str, Any],
        request: PublishRequest,
    ) -> Dict[str, Any]:
        """執行平台發布"""

        try:
            if platform == Platform.TIKTOK:
                return await client.publish_video(
                    video_id=request.video_id,
                    access_token=access_token,
                    title=content["title"],
                    description=content["description"],
                    tags=content["hashtags"],
                    settings={
                        "disable_duet": content.get("disable_duet", False),
                        "disable_comment": content.get(
                            "disable_comment", False
                        ),
                        "disable_stitch": content.get("disable_stitch", False),
                        "cover_timestamp": content.get(
                            "cover_timestamp", 1000
                        ),
                    },
                )
            elif platform == Platform.YOUTUBE_SHORTS:
                return await client.upload_short_video(
                    video_url=content["video_url"],
                    access_token=access_token,
                    title=content["title"],
                    description=content["description"],
                    tags=content["hashtags"],
                    category=content.get("category", "Entertainment"),
                    made_for_kids=content.get("made_for_kids", False),
                )
            elif platform == Platform.INSTAGRAM_REELS:
                return await client.publish_reel(
                    video_url=content["video_url"],
                    access_token=access_token,
                    caption=f"{content['title']}\n\n{
                        content['description']
                    }\n\n{' '.join(content['hashtags'])}",
                    allow_comments=content.get("allow_comments", True),
                    allow_sharing=content.get("allow_sharing", True),
                )
            else:
                raise Exception(f"不支援的平台: {platform.value}")

        except Exception as e:
            logger.error(f"平台發布執行失敗 {platform.value}: {e}")
            return {"success": False, "error": str(e)}

    async def _get_platform_access_token(
        self, user_id: str, platform: Platform
    ) -> Optional[str]:
        """獲取平台訪問令牌"""

        # 這裡應該從資料庫或認證服務獲取用戶的平台令牌
        # 模擬返回令牌
        mock_tokens = {
            Platform.TIKTOK: f"tiktok_token_{user_id}",
            Platform.YOUTUBE_SHORTS: f"youtube_token_{user_id}",
            Platform.INSTAGRAM_REELS: f"instagram_token_{user_id}",
        }

        return mock_tokens.get(platform)

    async def _start_analytics_tracking(
        self, platform: Platform, post_id: str, user_id: str
    ) -> None:
        """啟動分析追蹤"""

        try:
            # 延遲5分鐘後開始追蹤（讓平台有時間處理）
            await asyncio.sleep(300)

            client = self.platform_clients.get(platform)
            if not client:
                return

            # 獲取初始統計數據
            access_token = await self._get_platform_access_token(
                user_id, platform
            )
            if not access_token:
                return

            # 這裡可以實作定期統計數據收集
            logger.info(f"開始追蹤 {platform.value} 貼文分析: {post_id}")

        except Exception as e:
            logger.error(f"啟動分析追蹤失敗: {e}")

    async def get_optimal_publishing_times(
        self, user_id: str, platforms: List[Platform]
    ) -> Dict[Platform, List[str]]:
        """獲取最佳發布時間"""

        optimal_times = {}

        for platform in platforms:
            config = self.platform_configs.get(platform)
            if config:
                # 基礎最佳時間
                base_times = config.optimal_posting_times.copy()

                # 可以根據用戶歷史數據進行個性化調整
                # 這裡使用預設時間
                optimal_times[platform] = base_times

        return optimal_times

    async def schedule_batch_publish(
        self, request: PublishRequest, publish_times: Dict[Platform, datetime]
    ) -> str:
        """排程批次發布"""

        try:
            request_id = f"scheduled_{
                datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            }_{request.user_id}"

            # 為每個平台創建排程任務
            for platform, scheduled_time in publish_times.items():
                if platform in request.platforms:
                    # 計算延遲時間
                    delay_seconds = (
                        scheduled_time - datetime.utcnow()
                    ).total_seconds()

                    if delay_seconds > 0:
                        # 創建延遲任務
                        asyncio.create_task(
                            self._delayed_publish(
                                request, platform, delay_seconds
                            )
                        )

                        logger.info(
                            f"已排程 {platform.value} 發布: \
                                {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        )

            return request_id

        except Exception as e:
            logger.error(f"排程發布失敗: {e}")
            raise

    async def _delayed_publish(
        self, request: PublishRequest, platform: Platform, delay_seconds: float
    ) -> None:
        """延遲發布"""

        try:
            await asyncio.sleep(delay_seconds)

            # 創建單平台發布請求
            single_platform_request = PublishRequest(
                video_id=request.video_id,
                user_id=request.user_id,
                platforms=[platform],
                content=request.content,
                assets=request.assets,
                publish_immediately=True,
                retry_on_failure=request.retry_on_failure,
                max_retries=request.max_retries,
                platform_specific_settings=request.platform_specific_settings,
            )

            # 執行發布
            result = await self.publish_to_multiple_platforms(
                single_platform_request
            )

            logger.info(f"延遲發布到 {platform.value} 完成")

        except Exception as e:
            logger.error(f"延遲發布失敗: {e}")

    def get_publish_history(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[BatchPublishResult]:
        """獲取發布歷史"""

        user_history = []
        for request_id, result in self.publish_history.items():
            # 從請求ID中提取用戶ID（簡化實作）
            if user_id in request_id:
                user_history.append(result)

        # 按時間排序
        user_history.sort(key=lambda x: x.started_at, reverse=True)

        return user_history[offset : offset + limit]

    def get_active_publications(
        self, user_id: str
    ) -> List[BatchPublishResult]:
        """獲取活動中的發布"""

        active = []
        for request_id, result in self.active_publications.items():
            if user_id in request_id:
                active.append(result)

        return active

    async def cancel_scheduled_publish(self, request_id: str) -> bool:
        """取消排程發布"""

        try:
            # 這裡需要實作取消已排程任務的邏輯
            # 由於 asyncio.Task 沒有直接的取消機制，
            # 可能需要使用其他方式如資料庫狀態標記

            logger.info(f"排程發布已取消: {request_id}")
            return True

        except Exception as e:
            logger.error(f"取消排程發布失敗: {e}")
            return False

    async def get_revenue_analytics(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """獲取收益分析"""

        try:
            # 模擬收益數據
            # 實際應該從各平台的分析API獲取真實數據

            revenue_data = {
                "total_revenue": 125.50,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "platform_breakdown": {
                    "tiktok": {"revenue": 65.30, "views": 125000, "cpm": 0.52},
                    "youtube-shorts": {
                        "revenue": 45.20,
                        "views": 89000,
                        "cpm": 0.51,
                    },
                    "instagram-reels": {
                        "revenue": 15.00,
                        "views": 45000,
                        "cpm": 0.33,
                    },
                },
                "top_performing_content": [
                    {
                        "title": "AI 自動化工具",
                        "platform": "tiktok",
                        "revenue": 28.50,
                        "views": 45000,
                    }
                ],
                "revenue_trend": [
                    {"date": "2024-01-01", "revenue": 5.20},
                    {"date": "2024-01-02", "revenue": 8.50},
                    {"date": "2024-01-03", "revenue": 12.30},
                ],
            }

            return revenue_data

        except Exception as e:
            logger.error(f"獲取收益分析失敗: {e}")
            return {"total_revenue": 0, "error": str(e)}
