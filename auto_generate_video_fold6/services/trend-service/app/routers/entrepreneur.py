from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..auth import verify_token
from ..database import get_db
from ..models import TrendingTopic
from ..services import trend_analyzer
from ..schemas import PlatformType

logger = logging.getLogger(__name__)

router = APIRouter()


class EntrepreneurModeConfig(BaseModel):
    """創業者模式配置"""
    enabled: bool = False
    daily_video_count: int = 3
    operating_hours: Dict[str, str] = {"start": "09:00", "end": "18:00"}
    content_categories: List[str] = ["technology", "entertainment", "lifestyle"]
    platforms: List[str] = ["tiktok", "youtube-shorts"]
    video_duration: int = 30
    daily_budget: float = 10.0
    quality_threshold: float = 0.7
    auto_publish: bool = False


class EntrepreneurModeStatus(BaseModel):
    """創業者模式狀態"""
    is_running: bool
    last_execution: Optional[datetime]
    next_execution: Optional[datetime]
    today_videos_generated: int
    today_budget_used: float
    total_videos_generated: int
    success_rate: float


class TrendKeywordForEntrepreneur(BaseModel):
    """適合創業者的趨勢關鍵字"""
    keyword: str
    category: str
    trend_score: float
    traffic_volume: int
    competition_level: str  # low, medium, high
    monetization_potential: float
    estimated_cost: float
    suggested_platforms: List[str]
    content_ideas: List[str]


# 全局變量來追蹤創業者模式狀態
entrepreneur_mode_status = {
    "enabled": False,
    "config": None,
    "last_execution": None,
    "next_execution": None,
    "stats": {
        "today_videos": 0,
        "today_budget": 0.0,
        "total_videos": 0,
        "success_rate": 0.95
    }
}


@router.post("/mode/toggle")
async def toggle_entrepreneur_mode(
    config: EntrepreneurModeConfig,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
):
    """切換創業者模式開關"""
    
    try:
        global entrepreneur_mode_status
        
        entrepreneur_mode_status["enabled"] = config.enabled
        entrepreneur_mode_status["config"] = config.dict()
        
        if config.enabled:
            # 計算下次執行時間（30分鐘後）
            entrepreneur_mode_status["next_execution"] = datetime.utcnow() + timedelta(minutes=30)
            
            # 在背景啟動自動化任務
            background_tasks.add_task(start_entrepreneur_automation, config)
            
            logger.info(f"創業者模式已啟用 - 用戶: {current_user.get('sub')}")
            
            return {
                "message": "創業者模式已啟用",
                "status": "enabled",
                "next_execution": entrepreneur_mode_status["next_execution"],
                "config": config.dict()
            }
        else:
            entrepreneur_mode_status["next_execution"] = None
            logger.info(f"創業者模式已停用 - 用戶: {current_user.get('sub')}")
            
            return {
                "message": "創業者模式已停用",
                "status": "disabled"
            }
            
    except Exception as e:
        logger.error(f"切換創業者模式失敗: {e}")
        raise HTTPException(status_code=500, detail=f"切換模式失敗: {str(e)}")


@router.get("/mode/status", response_model=EntrepreneurModeStatus)
async def get_entrepreneur_mode_status(
    current_user: dict = Depends(verify_token),
):
    """獲取創業者模式狀態"""
    
    global entrepreneur_mode_status
    
    return EntrepreneurModeStatus(
        is_running=entrepreneur_mode_status["enabled"],
        last_execution=entrepreneur_mode_status["last_execution"],
        next_execution=entrepreneur_mode_status["next_execution"],
        today_videos_generated=entrepreneur_mode_status["stats"]["today_videos"],
        today_budget_used=entrepreneur_mode_status["stats"]["today_budget"],
        total_videos_generated=entrepreneur_mode_status["stats"]["total_videos"],
        success_rate=entrepreneur_mode_status["stats"]["success_rate"]
    )


@router.get("/trends/entrepreneur", response_model=List[TrendKeywordForEntrepreneur])
async def get_entrepreneur_friendly_trends(
    categories: Optional[str] = None,
    max_competition: str = "medium",
    min_monetization_score: float = 0.6,
    budget_limit: float = 20.0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取適合創業者的趨勢關鍵字"""
    
    try:
        # 解析類別
        category_list = categories.split(",") if categories else ["technology", "entertainment", "lifestyle"]
        
        # 從資料庫獲取基礎趨勢數據
        query = db.query(TrendingTopic).filter(
            TrendingTopic.trend_score >= 0.6,
            TrendingTopic.category.in_(category_list)
        )
        
        raw_trends = query.order_by(TrendingTopic.trend_score.desc()).limit(50).all()
        
        # 為創業者優化趨勢數據
        entrepreneur_trends = []
        
        for trend in raw_trends:
            # 計算競爭等級
            competition_level = calculate_competition_level(trend.trend_score, trend.keyword)
            
            # 跳過高競爭關鍵字
            if max_competition == "low" and competition_level in ["medium", "high"]:
                continue
            elif max_competition == "medium" and competition_level == "high":
                continue
            
            # 計算獲利潛力
            monetization_potential = calculate_monetization_potential(
                trend.keyword, trend.category, trend.trend_score
            )
            
            if monetization_potential < min_monetization_score:
                continue
            
            # 估算製作成本
            estimated_cost = estimate_video_cost(trend.keyword, trend.category)
            
            if estimated_cost > budget_limit:
                continue
            
            # 建議平台
            suggested_platforms = suggest_platforms_for_keyword(trend.keyword, trend.category)
            
            # 生成內容創意
            content_ideas = generate_content_ideas(trend.keyword, trend.category)
            
            entrepreneur_trend = TrendKeywordForEntrepreneur(
                keyword=trend.keyword,
                category=trend.category,
                trend_score=trend.trend_score,
                traffic_volume=getattr(trend, 'traffic_volume', 1000),
                competition_level=competition_level,
                monetization_potential=monetization_potential,
                estimated_cost=estimated_cost,
                suggested_platforms=suggested_platforms,
                content_ideas=content_ideas
            )
            
            entrepreneur_trends.append(entrepreneur_trend)
        
        # 按獲利潛力排序
        entrepreneur_trends.sort(key=lambda x: x.monetization_potential, reverse=True)
        
        logger.info(f"為創業者生成了 {len(entrepreneur_trends)} 個優化趨勢")
        
        return entrepreneur_trends[:20]  # 返回前20個最佳選擇
        
    except Exception as e:
        logger.error(f"獲取創業者趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取趨勢失敗: {str(e)}")


@router.post("/automation/trigger")
async def trigger_automation_manually(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
):
    """手動觸發自動化流程"""
    
    global entrepreneur_mode_status
    
    if not entrepreneur_mode_status["enabled"]:
        raise HTTPException(status_code=400, detail="創業者模式未啟用")
    
    config = EntrepreneurModeConfig(**entrepreneur_mode_status["config"])
    
    # 在背景執行自動化任務
    background_tasks.add_task(execute_entrepreneur_automation, config)
    
    return {
        "message": "自動化流程已觸發",
        "status": "triggered",
        "timestamp": datetime.utcnow()
    }


async def start_entrepreneur_automation(config: EntrepreneurModeConfig):
    """啟動創業者自動化流程"""
    
    logger.info("創業者自動化流程已啟動")
    
    while entrepreneur_mode_status["enabled"]:
        try:
            # 檢查是否在工作時間內
            if is_within_working_hours(config.operating_hours):
                await execute_entrepreneur_automation(config)
            else:
                logger.info("不在工作時間內，跳過此次執行")
            
            # 等待30分鐘再次執行
            await asyncio.sleep(1800)  # 30分鐘
            
        except Exception as e:
            logger.error(f"自動化流程執行錯誤: {e}")
            await asyncio.sleep(300)  # 發生錯誤時等5分鐘再試


async def execute_entrepreneur_automation(config: EntrepreneurModeConfig):
    """執行創業者自動化任務"""
    
    try:
        logger.info("開始執行創業者自動化任務")
        
        global entrepreneur_mode_status
        entrepreneur_mode_status["last_execution"] = datetime.utcnow()
        
        # 檢查今日是否已達限制
        if entrepreneur_mode_status["stats"]["today_videos"] >= config.daily_video_count:
            logger.info(f"今日已達影片數量限制 ({config.daily_video_count})")
            return
        
        if entrepreneur_mode_status["stats"]["today_budget"] >= config.daily_budget:
            logger.info(f"今日已達預算限制 (${config.daily_budget})")
            return
        
        # 這裡會調用其他服務來執行實際的影片生成
        # 例如: 調用 video-service 的 API
        
        logger.info("創業者自動化任務執行完成")
        
        # 更新下次執行時間
        entrepreneur_mode_status["next_execution"] = datetime.utcnow() + timedelta(minutes=30)
        
    except Exception as e:
        logger.error(f"執行自動化任務失敗: {e}")


def calculate_competition_level(trend_score: float, keyword: str) -> str:
    """計算競爭等級"""
    
    # 簡單的競爭等級判斷邏輯
    keyword_length = len(keyword.split())
    
    if trend_score > 0.9 and keyword_length <= 2:
        return "high"
    elif trend_score > 0.7 and keyword_length <= 3:
        return "medium"
    else:
        return "low"


def calculate_monetization_potential(keyword: str, category: str, trend_score: float) -> float:
    """計算獲利潛力"""
    
    # 基礎分數
    base_score = trend_score
    
    # 類別加權
    category_weights = {
        "technology": 0.9,
        "entertainment": 1.0,
        "lifestyle": 0.8,
        "business": 0.7,
        "health": 0.85,
        "food": 0.9
    }
    
    category_multiplier = category_weights.get(category, 0.6)
    
    # 關鍵字特徵加權
    monetization_keywords = ["如何", "教學", "評測", "推薦", "比較", "最佳"]
    keyword_bonus = 0.1 if any(mk in keyword for mk in monetization_keywords) else 0
    
    final_score = min(base_score * category_multiplier + keyword_bonus, 1.0)
    
    return round(final_score, 2)


def estimate_video_cost(keyword: str, category: str) -> float:
    """估算影片製作成本"""
    
    # 基礎成本
    base_cost = 2.0  # USD
    
    # 根據關鍵字複雜度調整
    complexity_multiplier = 1.0
    if len(keyword.split()) > 3:
        complexity_multiplier = 1.2
    
    # 根據類別調整
    category_costs = {
        "technology": 1.3,
        "entertainment": 1.0,
        "lifestyle": 1.1,
        "business": 1.2,
        "health": 1.15
    }
    
    category_multiplier = category_costs.get(category, 1.0)
    
    estimated_cost = base_cost * complexity_multiplier * category_multiplier
    
    return round(estimated_cost, 2)


def suggest_platforms_for_keyword(keyword: str, category: str) -> List[str]:
    """為關鍵字建議適合的平台"""
    
    # 根據類別和關鍵字特徵建議平台
    category_platforms = {
        "technology": ["youtube-shorts", "tiktok"],
        "entertainment": ["tiktok", "instagram-reels", "youtube-shorts"],
        "lifestyle": ["instagram-reels", "tiktok", "youtube-shorts"],
        "business": ["youtube-shorts", "linkedin-video"],
        "health": ["tiktok", "youtube-shorts", "instagram-reels"]
    }
    
    base_platforms = category_platforms.get(category, ["tiktok", "youtube-shorts"])
    
    # 根據關鍵字特徵調整
    if "教學" in keyword or "如何" in keyword:
        if "youtube-shorts" not in base_platforms:
            base_platforms.append("youtube-shorts")
    
    return base_platforms[:3]  # 最多返回3個平台


def generate_content_ideas(keyword: str, category: str) -> List[str]:
    """生成內容創意"""
    
    category_templates = {
        "technology": [
            f"{keyword} 最新趨勢解析",
            f"3分鐘了解 {keyword}",
            f"{keyword} 實用技巧分享"
        ],
        "entertainment": [
            f"{keyword} 背後的有趣故事",
            f"{keyword} 熱門話題討論",
            f"關於 {keyword} 你不知道的事"
        ],
        "lifestyle": [
            f"{keyword} 生活應用指南",
            f"如何用 {keyword} 提升生活品質",
            f"{keyword} 的5個實用建議"
        ]
    }
    
    templates = category_templates.get(category, [
        f"{keyword} 深度解析",
        f"{keyword} 實用指南",
        f"{keyword} 最新資訊"
    ])
    
    return templates


def is_within_working_hours(operating_hours: Dict[str, str]) -> bool:
    """檢查是否在工作時間內"""
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    start_time = operating_hours.get("start", "09:00")
    end_time = operating_hours.get("end", "18:00")
    
    return start_time <= current_time <= end_time


@router.get("/stats/daily")
async def get_daily_stats(
    current_user: dict = Depends(verify_token),
):
    """獲取每日統計數據"""
    
    global entrepreneur_mode_status
    
    return {
        "date": datetime.utcnow().date(),
        "videos_generated": entrepreneur_mode_status["stats"]["today_videos"],
        "budget_used": entrepreneur_mode_status["stats"]["today_budget"],
        "success_rate": entrepreneur_mode_status["stats"]["success_rate"],
        "total_videos": entrepreneur_mode_status["stats"]["total_videos"],
        "mode_enabled": entrepreneur_mode_status["enabled"]
    }