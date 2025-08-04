# 專案測試數據工廠
# 遵循 TDD 原則的專案數據生成

import factory
from faker import Faker
from datetime import datetime, timezone
from typing import Dict, List
from enum import Enum

from .base_factory import (
    TDDFactoryMixin,
    CommonFieldsMixin,
    register_factory,
)

fake = Faker(["zh_TW", "en_US"])


class ProjectStatus(Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProjectData:
    """專案數據類別"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@register_factory("project")
class ProjectFactory(factory.Factory, TDDFactoryMixin, CommonFieldsMixin):
    """
    專案工廠
    為 TDD 測試提供各種專案數據情境
    """

    class Meta:
        model = ProjectData

    # 基本欄位
    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=4))
    description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=300))

    # 用戶關聯
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    # 專案設定
    target_platform = factory.Iterator(
        ["tiktok", "instagram_reels", "youtube_shorts"]
    )
    target_audience = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["18-24歲年輕人", "25-34歲上班族", "35-44歲家長", "45歲以上"]
        )
    )
    content_style = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["educational", "entertainment", "promotional", "informational"]
        )
    )

    # 狀態
    status = factory.LazyAttribute(
        lambda o: fake.random_element(
            [
                ProjectStatus.DRAFT.value,
                ProjectStatus.IN_PROGRESS.value,
                ProjectStatus.COMPLETED.value,
            ]
        )
    )

    # 內容設定
    script_content = factory.LazyAttribute(
        lambda o: fake.text(max_nb_chars=500)
    )
    voice_settings = factory.LazyAttribute(
        lambda o: {
            "voice_id": fake.uuid4(),
            "speed": fake.random.uniform(0.8, 1.2),
            "pitch": fake.random.uniform(-0.2, 0.2),
            "emotion": fake.random_element(
                ["neutral", "happy", "sad", "excited"]
            ),
        }
    )

    # 視覺設定
    visual_style = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["modern", "minimalist", "colorful", "dark", "vintage"]
        )
    )
    background_music = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["upbeat", "relaxing", "epic", "acoustic", "electronic"]
        )
    )

    # 統計數據
    view_count = factory.LazyFunction(lambda: fake.random_int(0, 10000))
    like_count = factory.LazyFunction(lambda: fake.random_int(0, 1000))
    share_count = factory.LazyFunction(lambda: fake.random_int(0, 100))

    # 檔案路徑
    output_video_path = factory.LazyAttribute(
        lambda o: f"/videos/{o.id}/output.mp4"
    )
    thumbnail_path = factory.LazyAttribute(
        lambda o: f"/thumbnails/{o.id}/thumb.jpg"
    )

    # 時間設定
    duration_seconds = factory.LazyFunction(lambda: fake.random_int(15, 180))
    scheduled_publish_at = None
    published_at = None

    @classmethod
    def create_draft_project(cls, user_id: str = None, **kwargs):
        """建立草稿專案"""
        return cls.create(
            status=ProjectStatus.DRAFT.value,
            user_id=user_id or fake.uuid4(),
            published_at=None,
            **kwargs,
        )

    @classmethod
    def create_completed_project(cls, user_id: str = None, **kwargs):
        """建立已完成專案"""
        return cls.create(
            status=ProjectStatus.COMPLETED.value,
            user_id=user_id or fake.uuid4(),
            output_video_path=f"/videos/{fake.uuid4()}/completed.mp4",
            **kwargs,
        )

    @classmethod
    def create_published_project(cls, user_id: str = None, **kwargs):
        """建立已發布專案"""
        return cls.create(
            status=ProjectStatus.PUBLISHED.value,
            user_id=user_id or fake.uuid4(),
            published_at=datetime.now(timezone.utc),
            view_count=fake.random_int(100, 5000),
            **kwargs,
        )

    @classmethod
    def create_for_red_phase(cls, **kwargs):
        """RED 階段：建立會導致測試失敗的專案數據"""
        return cls.create(
            title="",  # 無效：空標題
            user_id="",  # 無效：空用戶ID
            duration_seconds=-1,  # 無效：負數持續時間
            **kwargs,
        )

    @classmethod
    def create_for_green_phase(cls, **kwargs):
        """GREEN 階段：建立讓測試通過的最簡專案數據"""
        return cls.create(
            title="測試專案",
            user_id=fake.uuid4(),
            status=ProjectStatus.DRAFT.value,
            **kwargs,
        )


@register_factory("create_project")
class CreateProjectFactory(factory.Factory, TDDFactoryMixin):
    """
    建立專案請求數據工廠
    模擬 API 請求中的專案建立數據
    """

    class Meta:
        model = dict

    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=3))
    description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=200))
    target_platform = factory.Iterator(
        ["tiktok", "instagram_reels", "youtube_shorts"]
    )
    content_style = factory.Iterator(
        ["educational", "entertainment", "promotional"]
    )
    target_audience = "18-34歲年輕人"
    visual_style = "modern"

    @classmethod
    def create_invalid_request(cls, **kwargs):
        """建立無效的專案建立請求"""
        return cls.build(
            title="",  # 無效：空標題
            target_platform="invalid_platform",  # 無效：不支援的平台
            **kwargs,
        )

    @classmethod
    def create_minimal_valid_request(cls, **kwargs):
        """建立最簡有效的專案建立請求"""
        return cls.build(
            title="最簡測試專案", target_platform="tiktok", **kwargs
        )


class ProjectBatchFactory:
    """專案批次建立工廠"""

    @staticmethod
    def create_user_projects(
        user_id: str, count: int = 5
    ) -> List[ProjectData]:
        """為特定用戶建立多個專案"""
        projects = []
        for i in range(count):
            project = ProjectFactory.create(
                user_id=user_id, title=f"用戶專案 {i + 1}"
            )
            projects.append(project)
        return projects

    @staticmethod
    def create_mixed_status_projects(user_id: str) -> Dict[str, ProjectData]:
        """建立不同狀態的專案"""
        return {
            "draft": ProjectFactory.create_draft_project(user_id),
            "completed": ProjectFactory.create_completed_project(user_id),
            "published": ProjectFactory.create_published_project(user_id),
        }


# TDD 輔助函數
def create_test_projects_scenario(
    user_id: str = None,
) -> Dict[str, ProjectData]:
    """
    建立完整的測試專案情境
    用於複雜的 TDD 測試場景
    """
    test_user_id = user_id or fake.uuid4()

    return {
        "draft_project": ProjectFactory.create_draft_project(test_user_id),
        "completed_project": ProjectFactory.create_completed_project(
            test_user_id
        ),
        "published_project": ProjectFactory.create_published_project(
            test_user_id
        ),
        "invalid_project": ProjectFactory.create_for_red_phase(),
        "valid_project": ProjectFactory.create_for_green_phase(),
    }


def cleanup_test_projects(projects: Dict[str, ProjectData]):
    """
    清理測試專案數據
    在測試完成後呼叫
    """
    # 清理邏輯
