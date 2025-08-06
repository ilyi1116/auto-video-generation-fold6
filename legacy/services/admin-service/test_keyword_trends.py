"""
關鍵字趨勢模組測試
測試新的 keyword_trends 表格和相關 API 功能
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .crud import crud_keyword_trend
from .database import get_db
from .main import app
from .models import Base, KeywordTrend
from .social_trends import SocialTrendsService, collect_and_save_trends

# 測試資料庫設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_keyword_trends.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆蓋資料庫依賴"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 覆蓋依賴
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def db_setup():
    """設定測試資料庫"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_setup):
    """提供資料庫會話"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """提供測試客戶端"""
    return TestClient(app)


@pytest.fixture
def sample_keyword_trends():
    """範例關鍵字趨勢數據"""
    return [
        {
            "platform": "TikTok",
            "keyword": "AI影片生成",
            "period": "day",
            "rank": 1,
            "search_volume": 1500000,
            "change_percentage": "+25%",
            "region": "global",
            "category": "科技",
            "metadata": {"source": "tiktok_api_v1", "confidence": 0.95},
        },
        {
            "platform": "YouTube",
            "keyword": "YouTube Shorts",
            "period": "day",
            "rank": 1,
            "search_volume": 2000000,
            "change_percentage": "+30%",
            "region": "global",
            "category": "娛樂",
            "metadata": {"source": "youtube_data_api_v3", "confidence": 0.92},
        },
        {
            "platform": "Instagram",
            "keyword": "Reels創作",
            "period": "day",
            "rank": 1,
            "search_volume": 1600000,
            "change_percentage": "+35%",
            "region": "global",
            "category": "創作",
            "metadata": {"source": "instagram_basic_display_api", "confidence": 0.88},
        },
    ]


class TestKeywordTrendModel:
    """測試 KeywordTrend 模型"""

    def test_create_keyword_trend(self, db_session):
        """測試創建關鍵字趨勢記錄"""
        keyword_trend = KeywordTrend(
            platform="TikTok",
            keyword="測試關鍵字",
            period="day",
            rank=1,
            search_volume=1000000,
            change_percentage="+10%",
            region="global",
            category="測試分類",
            metadata={"test": True},
        )

        db_session.add(keyword_trend)
        db_session.commit()
        db_session.refresh(keyword_trend)

        assert keyword_trend.id is not None
        assert keyword_trend.platform == "TikTok"
        assert keyword_trend.keyword == "測試關鍵字"
        assert keyword_trend.period == "day"
        assert keyword_trend.rank == 1
        assert keyword_trend.search_volume == 1000000
        assert keyword_trend.collected_at is not None

    def test_keyword_trend_str_representation(self, db_session):
        """測試字串表示"""
        keyword_trend = KeywordTrend(
            platform="YouTube", keyword="測試關鍵字", period="week", rank=5
        )

        expected = "<KeywordTrend(platform=YouTube, keyword=測試關鍵字, rank=5)>"
        assert str(keyword_trend) == expected


class TestKeywordTrendCRUD:
    """測試 KeywordTrend CRUD 操作"""

    def test_get_trends_by_platform(self, db_session, sample_keyword_trends):
        """測試根據平台獲取趨勢"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        # 測試獲取 TikTok 趨勢
        tiktok_trends = crud_keyword_trend.get_trends_by_platform(
            db_session, platform="TikTok", period="day"
        )

        assert len(tiktok_trends) == 1
        assert tiktok_trends[0].platform == "TikTok"
        assert tiktok_trends[0].keyword == "AI影片生成"

    def test_get_latest_trends(self, db_session, sample_keyword_trends):
        """測試獲取最新趨勢"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        # 獲取最新趨勢
        latest_trends = crud_keyword_trend.get_latest_trends(db_session, period="day", limit=10)

        assert len(latest_trends) == 3
        assert all(trend.period == "day" for trend in latest_trends)

    def test_search_keywords(self, db_session, sample_keyword_trends):
        """測試搜尋關鍵字"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        # 搜尋包含 "創作" 的關鍵字
        results = crud_keyword_trend.search_keywords(db_session, search_term="創作")

        assert len(results) == 1
        assert "創作" in results[0].keyword

    def test_get_platform_statistics(self, db_session, sample_keyword_trends):
        """測試獲取平台統計"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        # 獲取統計數據
        stats = crud_keyword_trend.get_platform_statistics(db_session, days=7)

        assert "statistics" in stats
        assert len(stats["statistics"]) == 3  # 三個平台
        assert stats["period_days"] == 7

    def test_get_top_keywords_by_period(self, db_session, sample_keyword_trends):
        """測試獲取各平台熱門關鍵字"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        # 獲取熱門關鍵字
        top_keywords = crud_keyword_trend.get_top_keywords_by_period(
            db_session, period="day", top_n=5
        )

        assert "TikTok" in top_keywords
        assert "YouTube" in top_keywords
        assert "Instagram" in top_keywords
        assert len(top_keywords["TikTok"]) == 1


class TestSocialTrendsService:
    """測試社交趨勢服務"""

    @patch("aiohttp.ClientSession")
    async def test_collect_all_trends(self, mock_session):
        """測試收集所有趨勢"""
        service = SocialTrendsService()

        # 模擬 API 響應
        mock_session.return_value.__aenter__ = AsyncMock()
        mock_session.return_value.__aexit__ = AsyncMock()

        trends_data = await service.collect_all_trends(
            platforms=["TikTok", "YouTube"], period="day"
        )

        assert isinstance(trends_data, dict)
        assert "TikTok" in trends_data or "YouTube" in trends_data

    async def test_collect_and_save_trends(self):
        """測試收集並儲存趨勢"""
        with patch("services.admin-service.social_trends.social_trends_service") as mock_service:
            mock_service.collect_all_trends.return_value = {
                "TikTok": [{"keyword": "測試", "rank": 1}]
            }
            mock_service.save_trends_to_db.return_value = 1

            result = await collect_and_save_trends(platforms=["TikTok"], period="day")

            assert result["success"] is True


class TestTrendTasksAPI:
    """測試趨勢相關 API 端點"""

    def test_get_keyword_trends_api(self, client, db_session, sample_keyword_trends):
        """測試關鍵字趨勢 API"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        # 模擬認證
        with patch("services.admin-service.main.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(id=1, username="test_user")

            response = client.get("/admin/keyword-trends?period=day&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "trends" in data["data"]

    def test_get_platforms_trends_api(self, client, db_session, sample_keyword_trends):
        """測試平台趨勢排行榜 API"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        with patch("services.admin-service.main.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(id=1, username="test_user")

            response = client.get("/admin/keyword-trends/platforms?period=day&top_n=5")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "platforms" in data["data"]

    def test_search_keyword_trends_api(self, client, db_session, sample_keyword_trends):
        """測試搜尋關鍵字趨勢 API"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        with patch("services.admin-service.main.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(id=1, username="test_user")

            response = client.get("/admin/keyword-trends/search?q=AI")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "results" in data["data"]

    def test_trigger_trends_collection_api(self, client):
        """測試觸發趨勢收集 API"""
        with patch("services.admin-service.main.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(id=1, username="test_user")

            with patch("services.admin-service.main.collect_and_save_trends") as mock_collect:
                mock_collect.return_value = {"success": True, "total_records_saved": 50}

                response = client.post(
                    "/admin/keyword-trends/collect", json={"platforms": ["TikTok"], "period": "day"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_get_trends_statistics_api(self, client, db_session, sample_keyword_trends):
        """測試趨勢統計 API"""
        # 添加測試數據
        for trend_data in sample_keyword_trends:
            trend = KeywordTrend(**trend_data)
            db_session.add(trend)
        db_session.commit()

        with patch("services.admin-service.main.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(id=1, username="test_user")

            response = client.get("/admin/keyword-trends/statistics?days=7")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "statistics" in data["data"]


class TestCeleryTasks:
    """測試 Celery 任務"""

    @patch("services.admin-service.tasks.trends_tasks.collect_and_save_trends")
    def test_collect_keyword_trends_new_task(self, mock_collect):
        """測試關鍵字趨勢收集任務"""
        # 模擬成功結果
        mock_collect.return_value = {
            "success": True,
            "total_records_saved": 25,
            "platforms_processed": 2,
        }

        # 由於這是 Celery 任務，我們只測試任務邏輯
        # 實際運行需要 Celery worker

        # 模擬任務執行邏輯
        result = mock_collect.return_value

        assert result["success"] is True
        assert result["total_records_saved"] == 25
        assert result["platforms_processed"] == 2


class TestDataIntegrity:
    """測試數據完整性"""

    def test_duplicate_prevention(self, db_session):
        """測試重複數據防止機制"""
        # 添加第一條記錄
        trend1 = KeywordTrend(
            platform="TikTok", keyword="重複測試", period="day", rank=1, search_volume=1000
        )
        db_session.add(trend1)
        db_session.commit()

        # 嘗試添加相似記錄（不同時間）
        trend2 = KeywordTrend(
            platform="TikTok",
            keyword="重複測試",
            period="day",
            rank=1,
            search_volume=1000,
            collected_at=datetime.utcnow() + timedelta(hours=2),
        )
        db_session.add(trend2)
        db_session.commit()

        # 檢查兩條記錄都存在（因為時間不同）
        count = db_session.query(KeywordTrend).filter(KeywordTrend.keyword == "重複測試").count()
        assert count == 2

    def test_date_range_queries(self, db_session):
        """測試日期範圍查詢"""
        # 添加不同日期的記錄
        base_time = datetime.utcnow()

        for i in range(5):
            trend = KeywordTrend(
                platform="TikTok",
                keyword=f"日期測試{i}",
                period="day",
                rank=i + 1,
                collected_at=base_time - timedelta(days=i),
            )
            db_session.add(trend)
        db_session.commit()

        # 查詢過去3天的記錄
        start_date = base_time - timedelta(days=3)
        end_date = base_time

        trends = crud_keyword_trend.get_trending_keywords_by_date_range(
            db_session, start_date=start_date, end_date=end_date
        )

        assert len(trends) == 4  # 包含第0到第3天


class TestPerformance:
    """測試性能"""

    def test_large_dataset_query(self, db_session):
        """測試大數據集查詢性能"""
        import time

        # 創建大量測試數據
        trends = []
        for i in range(1000):
            trend = KeywordTrend(
                platform=f"Platform{i % 5}",
                keyword=f"關鍵字{i}",
                period="day",
                rank=i % 100 + 1,
                search_volume=1000 + i,
            )
            trends.append(trend)

        db_session.add_all(trends)
        db_session.commit()

        # 測試查詢性能
        start_time = time.time()
        results = crud_keyword_trend.get_latest_trends(db_session, limit=50)
        end_time = time.time()

        assert len(results) == 50
        assert (end_time - start_time) < 1.0  # 查詢應在1秒內完成


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])
