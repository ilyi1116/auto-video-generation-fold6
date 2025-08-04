import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import re
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from .models import SocialTrendConfig, TrendingKeyword, KeywordTrend, SocialPlatform, TrendTimeframe
from .database import SessionLocal
from .schemas import TrendingKeywordCreate, SystemLogCreate
from .crud import crud_trending_keyword, crud_system_log

logger = logging.getLogger(__name__)


class BaseSocialTrendCollector(ABC):
    """社交媒體趨勢收集器基類"""
    
    def __init__(self, config: SocialTrendConfig):
        self.config = config
        self.session = None
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def collect_trends(self, timeframe: TrendTimeframe) -> List[Dict[str, Any]]:
        """收集趨勢數據"""
        pass
    
    def _prepare_headers(self) -> Dict[str, str]:
        """準備 HTTP 請求頭"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": self.config.language or "en-US,en;q=0.9",
        }
        
        if self.config.api_key:
            # 根據平台添加不同的認證頭
            if self.config.platform == SocialPlatform.TWITTER:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            elif self.config.platform == SocialPlatform.YOUTUBE:
                headers["X-API-Key"] = self.config.api_key
        
        return headers
    
    def _clean_keyword(self, keyword: str) -> str:
        """清理關鍵字"""
        # 移除特殊字符，保留英文、中文、數字和空格
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', keyword)
        return cleaned.strip()


class TwitterTrendCollector(BaseSocialTrendCollector):
    """Twitter 趨勢收集器"""
    
    async def collect_trends(self, timeframe: TrendTimeframe) -> List[Dict[str, Any]]:
        """收集 Twitter 趨勢"""
        trends = []
        
        try:
            # Twitter API v2 趨勢端點
            url = "https://api.twitter.com/2/trends/by/woeid/1"  # 全球趨勢
            if self.config.region != "global":
                # 根據地區設置不同的 WOEID
                region_woeids = {
                    "US": "23424977",
                    "UK": "23424975", 
                    "TW": "23424971",
                    "JP": "23424856"
                }
                woeid = region_woeids.get(self.config.region, "1")
                url = f"https://api.twitter.com/2/trends/by/woeid/{woeid}"
            
            headers = self._prepare_headers()
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    trend_items = data.get("data", [])
                    
                    for i, trend in enumerate(trend_items[:50]):  # 限制前50個
                        keyword = self._clean_keyword(trend.get("trend", ""))
                        if keyword:
                            trends.append({
                                "keyword": keyword,
                                "rank": i + 1,
                                "score": trend.get("tweet_volume", 0),
                                "metadata": {
                                    "tweet_volume": trend.get("tweet_volume"),
                                    "trend_type": trend.get("trend_type"),
                                    "url": trend.get("url")
                                }
                            })
                
                else:
                    logger.error(f"Twitter API 請求失敗: {response.status}")
        
        except Exception as e:
            logger.error(f"收集 Twitter 趨勢失敗: {e}")
            # 返回模擬數據用於測試
            trends = self._get_mock_trends("twitter")
        
        return trends
    
    def _get_mock_trends(self, platform: str) -> List[Dict[str, Any]]:
        """獲取模擬趨勢數據"""
        mock_keywords = {
            "twitter": ["AI", "ChatGPT", "Python", "JavaScript", "React", "Node.js", "API", "Database", "Cloud", "DevOps"],
            "youtube": ["Tutorial", "Music", "Gaming", "Tech Review", "Cooking", "Travel", "Fitness", "Comedy", "News", "DIY"],
            "tiktok": ["Dance", "Comedy", "Food", "Fashion", "Travel", "Tech", "Animals", "Art", "Music", "Lifestyle"],
            "instagram": ["Photography", "Fashion", "Food", "Travel", "Fitness", "Art", "Nature", "Beauty", "Design", "Lifestyle"],
            "facebook": ["News", "Family", "Friends", "Events", "Business", "Community", "Sports", "Entertainment", "Technology", "Health"]
        }
        
        keywords = mock_keywords.get(platform, mock_keywords["twitter"])
        return [
            {
                "keyword": keyword,
                "rank": i + 1,
                "score": 1000 - (i * 50),
                "metadata": {"mock_data": True}
            }
            for i, keyword in enumerate(keywords)
        ]


class YouTubeTrendCollector(BaseSocialTrendCollector):
    """YouTube 趨勢收集器"""
    
    async def collect_trends(self, timeframe: TrendTimeframe) -> List[Dict[str, Any]]:
        """收集 YouTube 趨勢"""
        trends = []
        
        try:
            # YouTube Data API v3
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "maxResults": 50,
                "regionCode": self.config.region if self.config.region != "global" else "US",
                "key": self.config.api_key
            }
            
            if self.config.category:
                # 根據分類設置 categoryId
                category_ids = {
                    "music": "10",
                    "gaming": "20",
                    "education": "27",
                    "technology": "28",
                    "entertainment": "24"
                }
                params["videoCategoryId"] = category_ids.get(self.config.category.lower(), "0")
            
            headers = self._prepare_headers()
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = data.get("items", [])
                    
                    for i, video in enumerate(videos):
                        snippet = video.get("snippet", {})
                        statistics = video.get("statistics", {})
                        
                        title = snippet.get("title", "")
                        # 從標題中提取關鍵字
                        keywords = self._extract_keywords_from_title(title)
                        
                        for keyword in keywords:
                            if keyword:
                                trends.append({
                                    "keyword": keyword,
                                    "rank": i + 1,
                                    "score": int(statistics.get("viewCount", 0)),
                                    "metadata": {
                                        "video_id": video.get("id"),
                                        "title": title,
                                        "view_count": statistics.get("viewCount"),
                                        "like_count": statistics.get("likeCount"),
                                        "channel_title": snippet.get("channelTitle")
                                    }
                                })
                
                else:
                    logger.error(f"YouTube API 請求失敗: {response.status}")
                    trends = self._get_mock_trends("youtube")
        
        except Exception as e:
            logger.error(f"收集 YouTube 趨勢失敗: {e}")
            trends = self._get_mock_trends("youtube")
        
        return trends
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """從標題中提取關鍵字"""
        # 簡單的關鍵字提取邏輯
        # 移除常見停用詞
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "how", "what", "when", "where", "why", "is", "are", "was", "were"}
        
        # 分割標題並清理
        words = re.findall(r'\b\w+\b', title.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords[:5]  # 返回前5個關鍵字


class TikTokTrendCollector(BaseSocialTrendCollector):
    """TikTok 趨勢收集器"""
    
    async def collect_trends(self, timeframe: TrendTimeframe) -> List[Dict[str, Any]]:
        """收集 TikTok 趨勢"""
        trends = []
        
        try:
            # TikTok 沒有公開的官方 API，這裡使用模擬數據
            # 實際實現可能需要使用第三方服務或爬蟲
            logger.info("TikTok 趨勢收集 - 使用模擬數據")
            trends = self._get_mock_trends("tiktok")
        
        except Exception as e:
            logger.error(f"收集 TikTok 趨勢失敗: {e}")
            trends = self._get_mock_trends("tiktok")
        
        return trends


class InstagramTrendCollector(BaseSocialTrendCollector):
    """Instagram 趨勢收集器"""
    
    async def collect_trends(self, timeframe: TrendTimeframe) -> List[Dict[str, Any]]:
        """收集 Instagram 趨勢"""
        trends = []
        
        try:
            # Instagram Graph API
            # 需要 Facebook 開發者帳號和 Instagram Business 帳號
            logger.info("Instagram 趨勢收集 - 使用模擬數據")
            trends = self._get_mock_trends("instagram")
        
        except Exception as e:
            logger.error(f"收集 Instagram 趨勢失敗: {e}")
            trends = self._get_mock_trends("instagram")
        
        return trends


class FacebookTrendCollector(BaseSocialTrendCollector):
    """Facebook 趨勢收集器"""
    
    async def collect_trends(self, timeframe: TrendTimeframe) -> List[Dict[str, Any]]:
        """收集 Facebook 趨勢"""
        trends = []
        
        try:
            # Facebook Graph API
            logger.info("Facebook 趨勢收集 - 使用模擬數據")
            trends = self._get_mock_trends("facebook")
        
        except Exception as e:
            logger.error(f"收集 Facebook 趨勢失敗: {e}")
            trends = self._get_mock_trends("facebook")
        
        return trends


class SocialTrendsManager:
    """社交媒體趨勢管理器"""
    
    def __init__(self):
        self.collectors = {
            SocialPlatform.TWITTER: TwitterTrendCollector,
            SocialPlatform.YOUTUBE: YouTubeTrendCollector,
            SocialPlatform.TIKTOK: TikTokTrendCollector,
            SocialPlatform.INSTAGRAM: InstagramTrendCollector,
            SocialPlatform.FACEBOOK: FacebookTrendCollector,
        }
    
    async def collect_all_trends(self) -> Dict[str, Any]:
        """收集所有活躍平台的趨勢"""
        db = SessionLocal()
        results = {}
        
        try:
            # 獲取所有活躍的趨勢配置
            active_configs = db.query(SocialTrendConfig).filter(
                SocialTrendConfig.is_active == True
            ).all()
            
            logger.info(f"發現 {len(active_configs)} 個活躍的趨勢配置")
            
            for config in active_configs:
                try:
                    platform_results = await self._collect_platform_trends(config)
                    results[f"{config.platform}_{config.region}"] = platform_results
                except Exception as e:
                    logger.error(f"收集平台 {config.platform} 趨勢失敗: {e}")
                    results[f"{config.platform}_{config.region}"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "results": results,
                "total_configs": len(active_configs)
            }
        
        finally:
            db.close()
    
    async def _collect_platform_trends(self, config: SocialTrendConfig) -> Dict[str, Any]:
        """收集指定平台的趨勢"""
        collector_class = self.collectors.get(config.platform)
        if not collector_class:
            raise ValueError(f"不支援的平台: {config.platform}")
        
        platform_results = {
            "platform": config.platform,
            "region": config.region,
            "timeframes": {},
            "total_keywords": 0
        }
        
        async with collector_class(config) as collector:
            for timeframe_str in config.timeframes:
                try:
                    timeframe = TrendTimeframe(timeframe_str)
                    trends = await collector.collect_trends(timeframe)
                    
                    # 保存趨勢到資料庫
                    saved_count = await self._save_trends_to_db(trends, config, timeframe)
                    
                    platform_results["timeframes"][timeframe_str] = {
                        "keywords_collected": len(trends),
                        "keywords_saved": saved_count,
                        "success": True
                    }
                    platform_results["total_keywords"] += saved_count
                
                except Exception as e:
                    logger.error(f"收集 {config.platform} {timeframe_str} 趨勢失敗: {e}")
                    platform_results["timeframes"][timeframe_str] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return platform_results
    
    async def _save_trends_to_db(self, trends: List[Dict[str, Any]], 
                                config: SocialTrendConfig, 
                                timeframe: TrendTimeframe) -> int:
        """保存趨勢數據到資料庫"""
        db = SessionLocal()
        saved_count = 0
        
        try:
            current_time = datetime.utcnow()
            
            for trend_data in trends:
                # 同時保存到新舊兩個表格以確保相容性
                
                # 1. 保存到新的 keyword_trends 表格
                keyword_trend = KeywordTrend(
                    platform=config.platform.value if hasattr(config.platform, 'value') else str(config.platform),
                    keyword=trend_data["keyword"],
                    period=self._convert_timeframe_to_period(timeframe),
                    rank=trend_data["rank"],
                    search_volume=trend_data.get("score"),
                    region=config.region,
                    category=config.category,
                    score=trend_data.get("score"),
                    change_percentage=trend_data.get("change_percentage"),
                    metadata=trend_data.get("metadata"),
                    collected_at=current_time
                )
                db.add(keyword_trend)
                
                # 2. 保存到舊的 trending_keywords 表格 (保持相容性)
                keyword_create = TrendingKeywordCreate(
                    platform=config.platform,
                    keyword=trend_data["keyword"],
                    rank=trend_data["rank"],
                    score=trend_data.get("score"),
                    timeframe=timeframe,
                    region=config.region,
                    category=config.category,
                    trend_date=current_time,
                    metadata=trend_data.get("metadata")
                )
                
                crud_trending_keyword.create(db, obj_in=keyword_create.dict())
                saved_count += 1
            
            db.commit()
            logger.info(f"成功保存 {saved_count} 個 {config.platform} 趨勢關鍵字")
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存趨勢數據失敗: {e}")
        
        finally:
            db.close()
        
        return saved_count
    
    def _convert_timeframe_to_period(self, timeframe: TrendTimeframe) -> str:
        """將 TrendTimeframe 轉換為 period 字串"""
        timeframe_mapping = {
            TrendTimeframe.ONE_DAY: "day",
            TrendTimeframe.ONE_WEEK: "week", 
            TrendTimeframe.ONE_MONTH: "month",
            TrendTimeframe.THREE_MONTHS: "3_months",
            TrendTimeframe.SIX_MONTHS: "6_months"
        }
        return timeframe_mapping.get(timeframe, "day")
    
    async def collect_platform_trends(self, platform: SocialPlatform, 
                                    region: str = "global") -> Dict[str, Any]:
        """收集指定平台和地區的趨勢"""
        db = SessionLocal()
        
        try:
            config = db.query(SocialTrendConfig).filter(
                SocialTrendConfig.platform == platform,
                SocialTrendConfig.region == region,
                SocialTrendConfig.is_active == True
            ).first()
            
            if not config:
                return {
                    "success": False,
                    "error": f"找不到 {platform} {region} 的活躍配置"
                }
            
            result = await self._collect_platform_trends(config)
            result["success"] = True
            return result
        
        finally:
            db.close()


class TrendsScheduler:
    """趨勢收集排程器"""
    
    def __init__(self):
        self.running = False
        self.trends_manager = SocialTrendsManager()
    
    async def start(self):
        """啟動排程器"""
        self.running = True
        logger.info("趨勢收集排程器已啟動")
        
        while self.running:
            try:
                await self._run_scheduled_collections()
                # 每小時檢查一次
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"趨勢排程器運行錯誤: {e}")
                await asyncio.sleep(3600)
    
    def stop(self):
        """停止排程器"""
        self.running = False
        logger.info("趨勢收集排程器已停止")
    
    async def _run_scheduled_collections(self):
        """運行計劃的趨勢收集任務"""
        logger.info("開始執行計劃的趨勢收集任務")
        
        try:
            results = await self.trends_manager.collect_all_trends()
            
            if results["success"]:
                logger.info(f"趨勢收集完成，處理了 {results['total_configs']} 個配置")
            else:
                logger.error("趨勢收集失敗")
            
            # 記錄操作日誌
            self._log_collection_result(results)
        
        except Exception as e:
            logger.error(f"執行趨勢收集任務失敗: {e}")
    
    def _log_collection_result(self, results: Dict[str, Any]):
        """記錄收集結果日誌"""
        try:
            db = SessionLocal()
            log_data = SystemLogCreate(
                action="trends_collection",
                resource_type="social_trends",
                level="info" if results["success"] else "error",
                message=f"趨勢收集任務完成，處理 {results.get('total_configs', 0)} 個配置",
                details=results
            )
            crud_system_log.create_log(db, log_in=log_data)
            db.close()
        except Exception as e:
            logger.error(f"記錄趨勢收集日誌失敗: {e}")


# 全域排程器實例
trends_scheduler = TrendsScheduler()


# 趨勢管理工具函數
def start_trends_scheduler():
    """啟動趨勢收集排程器"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(trends_scheduler.start())


def stop_trends_scheduler():
    """停止趨勢收集排程器"""
    trends_scheduler.stop()


async def collect_platform_trends_manually(platform: SocialPlatform, 
                                         region: str = "global") -> Dict[str, Any]:
    """手動收集指定平台趨勢"""
    manager = SocialTrendsManager()
    return await manager.collect_platform_trends(platform, region)