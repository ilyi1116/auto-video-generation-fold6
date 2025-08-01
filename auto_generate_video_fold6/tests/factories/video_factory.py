# 影片測試數據工廠
# 遵循 TDD 原則的影片數據生成

import factory
from faker import Faker
from datetime import datetime, timezone
from typing import Dict, Any, List
from enum import Enum

from .base_factory import (
    BaseFactory,
    TDDFactoryMixin,
    CommonFieldsMixin,
    register_factory,
)

fake = Faker(["zh_TW", "en_US"])


class VideoStatus(Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PUBLISHED = "published"


class VideoQuality(Enum):
    LOW = "360p"
    MEDIUM = "720p"
    HIGH = "1080p"
    ULTRA = "4K"


class VideoData:
    """影片數據類別"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@register_factory("video")
class VideoFactory(factory.Factory, TDDFactoryMixin, CommonFieldsMixin):
    """
    影片工廠
    為 TDD 測試提供各種影片數據情境
    """

    class Meta:
        model = VideoData

    # 基本欄位
    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=5))
    description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=400))

    # 關聯欄位
    project_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    # 影片屬性
    duration = factory.LazyFunction(lambda: fake.random_int(15, 300))  # 秒
    resolution = factory.Iterator(
        [VideoQuality.MEDIUM.value, VideoQuality.HIGH.value]
    )
    fps = factory.Iterator([24, 30, 60])
    file_size = factory.LazyFunction(
        lambda: fake.random_int(1024 * 1024, 100 * 1024 * 1024)
    )  # bytes

    # 檔案路徑
    file_path = factory.LazyAttribute(
        lambda o: f"/videos/{o.project_id}/{o.id}.mp4"
    )
    thumbnail_path = factory.LazyAttribute(
        lambda o: f"/thumbnails/{o.project_id}/{o.id}_thumb.jpg"
    )

    # 狀態
    status = factory.LazyAttribute(
        lambda o: fake.random_element(
            [VideoStatus.PROCESSING.value, VideoStatus.COMPLETED.value]
        )
    )

    # 處理資訊
    processing_started_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc)
    )
    processing_completed_at = None
    processing_progress = factory.LazyFunction(lambda: fake.random_int(0, 100))

    # 錯誤資訊
    error_message = None
    retry_count = 0

    # 媒體資訊
    video_codec = factory.Iterator(["h264", "h265", "vp9"])
    audio_codec = factory.Iterator(["aac", "mp3", "opus"])
    bitrate = factory.LazyFunction(lambda: fake.random_int(1000, 8000))  # kbps

    # AI 生成資訊
    script_used = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=500))
    voice_settings = factory.LazyAttribute(
        lambda o: {
            "voice_id": fake.uuid4(),
            "speed": fake.random.uniform(0.8, 1.2),
            "pitch": fake.random.uniform(-0.2, 0.2),
            "volume": fake.random.uniform(0.7, 1.0),
        }
    )

    # 視覺設定
    background_images = factory.LazyAttribute(
        lambda o: [f"/images/bg_{i}.jpg" for i in range(fake.random_int(3, 8))]
    )
    transition_effects = factory.LazyAttribute(
        lambda o: fake.random_element(["fade", "slide", "zoom", "dissolve"])
    )

    # 統計數據
    view_count = factory.LazyFunction(lambda: fake.random_int(0, 10000))
    like_count = factory.LazyFunction(lambda: fake.random_int(0, 1000))
    share_count = factory.LazyFunction(lambda: fake.random_int(0, 100))
    comment_count = factory.LazyFunction(lambda: fake.random_int(0, 200))

    # 發布資訊
    published_at = None
    published_platforms = factory.LazyAttribute(lambda o: [])

    @classmethod
    def create_processing_video(cls, project_id: str = None, **kwargs):
        """建立正在處理的影片"""
        return cls.create(
            status=VideoStatus.PROCESSING.value,
            project_id=project_id or fake.uuid4(),
            processing_progress=fake.random_int(10, 90),
            processing_completed_at=None,
            **kwargs,
        )

    @classmethod
    def create_completed_video(cls, project_id: str = None, **kwargs):
        """建立已完成的影片"""
        return cls.create(
            status=VideoStatus.COMPLETED.value,
            project_id=project_id or fake.uuid4(),
            processing_progress=100,
            processing_completed_at=datetime.now(timezone.utc),
            file_path=f"/videos/{project_id or fake.uuid4()}/completed.mp4",
            **kwargs,
        )

    @classmethod
    def create_failed_video(cls, project_id: str = None, **kwargs):
        """建立處理失敗的影片"""
        return cls.create(
            status=VideoStatus.FAILED.value,
            project_id=project_id or fake.uuid4(),
            processing_progress=fake.random_int(0, 50),
            error_message="影片處理失敗：編碼錯誤",
            retry_count=fake.random_int(1, 3),
            **kwargs,
        )

    @classmethod
    def create_published_video(cls, project_id: str = None, **kwargs):
        """建立已發布的影片"""
        return cls.create(
            status=VideoStatus.PUBLISHED.value,
            project_id=project_id or fake.uuid4(),
            processing_progress=100,
            processing_completed_at=datetime.now(timezone.utc),
            published_at=datetime.now(timezone.utc),
            published_platforms=["tiktok", "instagram_reels"],
            view_count=fake.random_int(100, 5000),
            **kwargs,
        )

    @classmethod
    def create_high_quality_video(cls, **kwargs):
        """建立高品質影片"""
        return cls.create(
            resolution=VideoQuality.HIGH.value,
            fps=60,
            bitrate=fake.random_int(4000, 8000),
            video_codec="h265",
            audio_codec="aac",
            **kwargs,
        )

    @classmethod
    def create_for_red_phase(cls, **kwargs):
        """RED 階段：建立會導致測試失敗的影片數據"""
        return cls.create(
            title="",  # 無效：空標題
            duration=-1,  # 無效：負數持續時間
            file_size=0,  # 無效：檔案大小為0
            project_id="",  # 無效：空專案ID
            **kwargs,
        )

    @classmethod
    def create_for_green_phase(cls, **kwargs):
        """GREEN 階段：建立讓測試通過的最簡影片數據"""
        return cls.create(
            title="測試影片",
            duration=30,
            status=VideoStatus.COMPLETED.value,
            processing_progress=100,
            **kwargs,
        )


@register_factory("create_video")
class CreateVideoFactory(factory.Factory, TDDFactoryMixin):
    """
    建立影片請求數據工廠
    模擬 API 請求中的影片建立數據
    """

    class Meta:
        model = dict

    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=4))
    description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=200))
    project_id = factory.LazyFunction(lambda: fake.uuid4())

    # 影片設定
    resolution = VideoQuality.HIGH.value
    fps = 30
    quality_preset = "medium"

    # 內容設定
    script_content = factory.LazyAttribute(
        lambda o: fake.text(max_nb_chars=300)
    )
    voice_settings = factory.LazyAttribute(
        lambda o: {"voice_id": fake.uuid4(), "speed": 1.0, "pitch": 0.0}
    )

    @classmethod
    def create_invalid_request(cls, **kwargs):
        """建立無效的影片建立請求"""
        return cls.build(
            title="",  # 無效：空標題
            project_id="invalid-id",  # 無效：錯誤格式的ID
            resolution="invalid-resolution",  # 無效：不支援的解析度
            **kwargs,
        )

    @classmethod
    def create_minimal_valid_request(cls, **kwargs):
        """建立最簡有效的影片建立請求"""
        return cls.build(
            title="簡單測試影片",
            project_id=fake.uuid4(),
            script_content="這是一個測試腳本",
            **kwargs,
        )


class VideoBatchFactory:
    """影片批次建立工廠"""

    @staticmethod
    def create_project_videos(
        project_id: str, count: int = 3
    ) -> List[VideoData]:
        """為特定專案建立多個影片"""
        videos = []
        for i in range(count):
            video = VideoFactory.create_completed_video(
                project_id=project_id, title=f"專案影片 {i + 1}"
            )
            videos.append(video)
        return videos

    @staticmethod
    def create_mixed_status_videos(project_id: str) -> Dict[str, VideoData]:
        """建立不同狀態的影片"""
        return {
            "processing": VideoFactory.create_processing_video(project_id),
            "completed": VideoFactory.create_completed_video(project_id),
            "failed": VideoFactory.create_failed_video(project_id),
            "published": VideoFactory.create_published_video(project_id),
        }


# TDD 輔助函數
def create_test_videos_scenario(
    project_id: str = None,
) -> Dict[str, VideoData]:
    """
    建立完整的測試影片情境
    用於複雜的 TDD 測試場景
    """
    test_project_id = project_id or fake.uuid4()

    return {
        "processing_video": VideoFactory.create_processing_video(
            test_project_id
        ),
        "completed_video": VideoFactory.create_completed_video(
            test_project_id
        ),
        "failed_video": VideoFactory.create_failed_video(test_project_id),
        "published_video": VideoFactory.create_published_video(
            test_project_id
        ),
        "high_quality_video": VideoFactory.create_high_quality_video(
            project_id=test_project_id
        ),
        "invalid_video": VideoFactory.create_for_red_phase(),
        "valid_video": VideoFactory.create_for_green_phase(),
    }


def cleanup_test_videos(videos: Dict[str, VideoData]):
    """
    清理測試影片數據
    在測試完成後呼叫
    """
    # 清理影片檔案和數據庫記錄
    pass
