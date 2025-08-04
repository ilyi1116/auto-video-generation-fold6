"""
創業者模式多平台發布 API 路由
提供統一的多平台發布管理介面
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import verify_token
from ..entrepreneur_publisher import (
    EntrepreneurPublisher,
    Platform,
    PublishRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局發布管理器實例
publisher = EntrepreneurPublisher()


# Pydantic 模型定義
class PublishRequestModel(BaseModel):
    """發布請求模型"""

    video_id: str = Field(..., description="影片ID")
    platforms: List[str] = Field(..., description="目標平台列表")
    content: Dict[str, Any] = Field(..., description="內容信息")
    assets: Dict[str, Any] = Field(..., description="媒體資產")
    publish_immediately: bool = Field(default=True, description="是否立即發布")
    scheduled_time: Optional[datetime] = Field(
        None, description="排程發布時間"
    )
    retry_on_failure: bool = Field(default=True, description="失敗時是否重試")
    max_retries: int = Field(
        default=3, ge=0, le=10, description="最大重試次數"
    )
    platform_specific_settings: Dict[str, Dict[str, Any]] = Field(
        default={}, description="平台特定設定"
    )


class OptimalTimesRequest(BaseModel):
    """最佳發布時間請求"""

    platforms: List[str] = Field(..., description="查詢的平台列表")
    timezone: str = Field(default="Asia/Taipei", description="時區")


class ScheduledPublishRequest(BaseModel):
    """排程發布請求"""

    video_id: str = Field(..., description="影片ID")
    platforms: List[str] = Field(..., description="目標平台列表")
    content: Dict[str, Any] = Field(..., description="內容信息")
    assets: Dict[str, Any] = Field(..., description="媒體資產")
    publish_times: Dict[str, datetime] = Field(
        ..., description="各平台發布時間"
    )
    retry_on_failure: bool = Field(default=True, description="失敗時是否重試")


class PublishHistoryResponse(BaseModel):
    """發布歷史回應"""

    request_id: str
    total_platforms: int
    successful_platforms: List[str]
    failed_platforms: List[str]
    overall_success_rate: float
    started_at: datetime
    completed_at: Optional[datetime]


class RevenueAnalyticsResponse(BaseModel):
    """收益分析回應"""

    total_revenue: float
    period: Dict[str, str]
    platform_breakdown: Dict[str, Dict[str, Any]]
    top_performing_content: List[Dict[str, Any]]
    revenue_trend: List[Dict[str, Any]]


@router.post("/publish")
async def publish_to_platforms(
    request: PublishRequestModel,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
):
    """多平台發布內容"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 驗證平台
        valid_platforms = []
        for platform_str in request.platforms:
            try:
                platform = Platform(platform_str)
                valid_platforms.append(platform)
            except ValueError:
                logger.warning(f"不支援的平台: {platform_str}")

        if not valid_platforms:
            raise HTTPException(status_code=400, detail="沒有有效的發布平台")

        # 轉換平台特定設定
        platform_settings = {}
        for (
            platform_str,
            settings,
        ) in request.platform_specific_settings.items():
            try:
                platform = Platform(platform_str)
                platform_settings[platform] = settings
            except ValueError:
                continue

        # 創建發布請求
        publish_request = PublishRequest(
            video_id=request.video_id,
            user_id=user_id,
            platforms=valid_platforms,
            content=request.content,
            assets=request.assets,
            publish_immediately=request.publish_immediately,
            scheduled_time=request.scheduled_time,
            retry_on_failure=request.retry_on_failure,
            max_retries=request.max_retries,
            platform_specific_settings=platform_settings,
        )

        if request.publish_immediately:
            # 立即發布
            result = await publisher.publish_to_multiple_platforms(
                publish_request
            )

            return {
                "request_id": result.request_id,
                "status": "completed",
                "total_platforms": result.total_platforms,
                "successful_platforms": [
                    p.value for p in result.successful_platforms
                ],
                "failed_platforms": [p.value for p in result.failed_platforms],
                "overall_success_rate": result.overall_success_rate,
                "platform_results": {
                    p.value: {
                        "status": result.platform_results[p].status.value,
                        "post_id": result.platform_results[p].post_id,
                        "post_url": result.platform_results[p].post_url,
                        "error_message": result.platform_results[
                            p
                        ].error_message,
                    }
                    for p in result.platform_results
                },
            }
        else:
            # 排程發布
            if not request.scheduled_time:
                raise HTTPException(
                    status_code=400, detail="排程發布需要指定發布時間"
                )

            # 為所有平台設定相同的發布時間
            publish_times = {
                p: request.scheduled_time for p in valid_platforms
            }

            request_id = await publisher.schedule_batch_publish(
                publish_request, publish_times
            )

            return {
                "request_id": request_id,
                "status": "scheduled",
                "scheduled_time": request.scheduled_time.isoformat(),
                "platforms": [p.value for p in valid_platforms],
                "message": "發布已排程",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多平台發布失敗: {e}")
        raise HTTPException(status_code=500, detail=f"發布失敗: {str(e)}")


@router.get("/optimal-times")
async def get_optimal_publishing_times(
    platforms: str = "tiktok,youtube-shorts,instagram-reels",
    current_user: dict = Depends(verify_token),
):
    """獲取最佳發布時間"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 解析平台列表
        platform_list = []
        for platform_str in platforms.split(","):
            platform_str = platform_str.strip()
            try:
                platform = Platform(platform_str)
                platform_list.append(platform)
            except ValueError:
                logger.warning(f"不支援的平台: {platform_str}")

        if not platform_list:
            raise HTTPException(status_code=400, detail="沒有有效的平台")

        optimal_times = await publisher.get_optimal_publishing_times(
            user_id, platform_list
        )

        return {
            "user_id": user_id,
            "optimal_times": {
                platform.value: times
                for platform, times in optimal_times.items()
            },
            "timezone": "Asia/Taipei",
            "recommendation": "建議在晚上 7-9 點發布以獲得最佳互動效果",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取最佳發布時間失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取最佳時間失敗: {str(e)}"
        )


@router.post("/schedule")
async def schedule_publish(
    request: ScheduledPublishRequest,
    current_user: dict = Depends(verify_token),
):
    """排程多平台發布"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 驗證平台和時間
        valid_platforms = []
        publish_times = {}

        for platform_str in request.platforms:
            try:
                platform = Platform(platform_str)
                valid_platforms.append(platform)

                # 獲取對應的發布時間
                if platform_str in request.publish_times:
                    publish_times[platform] = request.publish_times[
                        platform_str
                    ]
                else:
                    # 使用預設時間（當前時間 + 1小時）
                    publish_times[platform] = datetime.utcnow() + timedelta(
                        hours=1
                    )

            except ValueError:
                logger.warning(f"不支援的平台: {platform_str}")

        if not valid_platforms:
            raise HTTPException(status_code=400, detail="沒有有效的發布平台")

        # 驗證發布時間不能是過去時間
        current_time = datetime.utcnow()
        for platform, publish_time in publish_times.items():
            if publish_time <= current_time:
                raise HTTPException(
                    status_code=400,
                    detail=f"{platform.value} 的發布時間不能是過去時間",
                )

        # 創建發布請求
        publish_request = PublishRequest(
            video_id=request.video_id,
            user_id=user_id,
            platforms=valid_platforms,
            content=request.content,
            assets=request.assets,
            publish_immediately=False,
            retry_on_failure=request.retry_on_failure,
        )

        # 排程發布
        request_id = await publisher.schedule_batch_publish(
            publish_request, publish_times
        )

        return {
            "request_id": request_id,
            "status": "scheduled",
            "platforms": [p.value for p in valid_platforms],
            "publish_times": {
                p.value: publish_times[p].isoformat() for p in valid_platforms
            },
            "message": "批次發布已排程",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"排程發布失敗: {e}")
        raise HTTPException(status_code=500, detail=f"排程失敗: {str(e)}")


@router.get("/history", response_model=List[PublishHistoryResponse])
async def get_publish_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(verify_token),
):
    """獲取發布歷史"""
    try:
        user_id = current_user.get("sub", "unknown")

        history = publisher.get_publish_history(user_id, limit, offset)

        return [
            PublishHistoryResponse(
                request_id=result.request_id,
                total_platforms=result.total_platforms,
                successful_platforms=[
                    p.value for p in result.successful_platforms
                ],
                failed_platforms=[p.value for p in result.failed_platforms],
                overall_success_rate=result.overall_success_rate,
                started_at=result.started_at,
                completed_at=result.completed_at,
            )
            for result in history
        ]

    except Exception as e:
        logger.error(f"獲取發布歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取歷史失敗: {str(e)}")


@router.get("/active")
async def get_active_publications(current_user: dict = Depends(verify_token)):
    """獲取進行中的發布"""
    try:
        user_id = current_user.get("sub", "unknown")

        active_pubs = publisher.get_active_publications(user_id)

        return {
            "active_publications": [
                {
                    "request_id": pub.request_id,
                    "total_platforms": pub.total_platforms,
                    "started_at": pub.started_at.isoformat(),
                    "status": "in_progress",
                }
                for pub in active_pubs
            ],
            "count": len(active_pubs),
        }

    except Exception as e:
        logger.error(f"獲取活動發布失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取活動發布失敗: {str(e)}"
        )


@router.delete("/cancel/{request_id}")
async def cancel_scheduled_publish(
    request_id: str, current_user: dict = Depends(verify_token)
):
    """取消排程發布"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 驗證請求是否屬於當前用戶
        if user_id not in request_id:
            raise HTTPException(status_code=403, detail="無權限取消此發布")

        success = await publisher.cancel_scheduled_publish(request_id)

        if success:
            return {"message": "排程發布已取消", "request_id": request_id}
        else:
            raise HTTPException(status_code=400, detail="取消發布失敗")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消排程發布失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消發布失敗: {str(e)}")


@router.get("/analytics/revenue", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(verify_token),
):
    """獲取收益分析數據"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 設定預設時間範圍（過去30天）
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        revenue_data = await publisher.get_revenue_analytics(
            user_id, start_date, end_date
        )

        return RevenueAnalyticsResponse(**revenue_data)

    except Exception as e:
        logger.error(f"獲取收益分析失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取收益分析失敗: {str(e)}"
        )


@router.get("/platforms/status")
async def get_platform_status(current_user: dict = Depends(verify_token)):
    """獲取各平台連接狀態"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 檢查各平台的連接狀態
        platform_status = {}

        for platform in Platform:
            try:
                # 嘗試獲取訪問令牌來檢查連接狀態
                access_token = await publisher._get_platform_access_token(
                    user_id, platform
                )

                platform_status[platform.value] = {
                    "connected": access_token is not None,
                    "last_checked": datetime.utcnow().isoformat(),
                    "status": "healthy" if access_token else "disconnected",
                }
            except Exception as e:
                platform_status[platform.value] = {
                    "connected": False,
                    "last_checked": datetime.utcnow().isoformat(),
                    "status": "error",
                    "error": str(e),
                }

        return {
            "user_id": user_id,
            "platforms": platform_status,
            "overall_health": (
                "healthy"
                if any(
                    status["connected"] for status in platform_status.values()
                )
                else "disconnected"
            ),
        }

    except Exception as e:
        logger.error(f"獲取平台狀態失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取平台狀態失敗: {str(e)}"
        )


@router.post("/test-publish")
async def test_publish_content(
    platform: str,
    test_content: Dict[str, Any],
    current_user: dict = Depends(verify_token),
):
    """測試發布內容（開發用）"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 驗證平台
        try:
            target_platform = Platform(platform)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"不支援的平台: {platform}"
            )

        # 創建測試發布請求
        test_request = PublishRequest(
            video_id="test_video_123",
            user_id=user_id,
            platforms=[target_platform],
            content=test_content.get(
                "content",
                {
                    "title": "測試發布",
                    "description": "這是一個測試發布",
                    "hashtags": ["#test", "#demo"],
                },
            ),
            assets=test_content.get(
                "assets",
                {
                    "video_url": "https://example.com/test_video.mp4",
                    "thumbnail_url": "https://example.com/test_thumb.jpg",
                },
            ),
            publish_immediately=True,
            retry_on_failure=False,
            max_retries=0,
        )

        # 執行測試發布
        result = await publisher.publish_to_multiple_platforms(test_request)

        return {
            "test_result": (
                "success" if result.overall_success_rate > 0 else "failed"
            ),
            "platform": platform,
            "result_details": {
                "status": result.platform_results[
                    target_platform
                ].status.value,
                "post_id": result.platform_results[target_platform].post_id,
                "post_url": result.platform_results[target_platform].post_url,
                "error_message": result.platform_results[
                    target_platform
                ].error_message,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"測試發布失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試發布失敗: {str(e)}")


@router.get("/health")
async def publisher_health_check():
    """發布管理器健康檢查"""
    try:
        return {
            "status": "healthy",
            "service": "entrepreneur_publisher",
            "active_publications": len(publisher.active_publications),
            "total_history_records": len(publisher.publish_history),
            "supported_platforms": [platform.value for platform in Platform],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
