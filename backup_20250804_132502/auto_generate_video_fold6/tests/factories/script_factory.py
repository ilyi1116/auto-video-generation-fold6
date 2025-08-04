# 腳本測試數據工廠
# 遵循 TDD 原則的腳本數據生成

import factory
from faker import Faker
from typing import Dict, List
from enum import Enum

from .base_factory import (
    TDDFactoryMixin,
    CommonFieldsMixin,
    register_factory,
)

fake = Faker(["zh_TW", "en_US"])


class ScriptType(Enum):
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    PROMOTIONAL = "promotional"
    NEWS = "news"
    TUTORIAL = "tutorial"


class ScriptStatus(Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    USED = "used"


class ScriptData:
    """腳本數據類別"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@register_factory("script")
class ScriptFactory(factory.Factory, TDDFactoryMixin, CommonFieldsMixin):
    """
    腳本工廠
    為 TDD 測試提供各種腳本數據情境
    """

    class Meta:
        model = ScriptData

    # 基本欄位
    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=6))
    content = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=800))

    # 關聯欄位
    project_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    # 腳本類型和設定
    script_type = factory.LazyAttribute(
        lambda o: fake.random_element(
            [
                ScriptType.EDUCATIONAL.value,
                ScriptType.ENTERTAINMENT.value,
                ScriptType.PROMOTIONAL.value,
            ]
        )
    )

    target_platform = factory.Iterator(
        ["tiktok", "instagram_reels", "youtube_shorts"]
    )
    target_audience = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["18-24歲年輕人", "25-34歲上班族", "35-44歲家長"]
        )
    )

    # 語言和風格
    language = "zh-TW"
    tone = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["professional", "casual", "humorous", "serious", "friendly"]
        )
    )
    style = factory.LazyAttribute(
        lambda o: fake.random_element(
            ["conversational", "narrative", "instructional", "persuasive"]
        )
    )

    # 內容統計
    word_count = factory.LazyAttribute(
        lambda o: (
            len(o.content.split())
            if hasattr(o, "content")
            else fake.random_int(50, 200)
        )
    )
    estimated_duration = factory.LazyAttribute(
        lambda o: (
            o.word_count * 0.4
            if hasattr(o, "word_count")
            else fake.random_int(30, 120)
        )
    )  # 秒

    # 狀態
    status = factory.LazyAttribute(
        lambda o: fake.random_element(
            [
                ScriptStatus.DRAFT.value,
                ScriptStatus.GENERATED.value,
                ScriptStatus.REVIEWED.value,
            ]
        )
    )

    # AI 生成資訊
    generated_by_ai = True
    ai_model_used = factory.LazyAttribute(
        lambda o: fake.random_element(["gpt-4", "claude-3", "gemini-pro"])
    )
    generation_prompt = factory.LazyAttribute(
        lambda o: fake.text(max_nb_chars=200)
    )

    # 關鍵字和標籤
    keywords = factory.LazyAttribute(
        lambda o: [fake.word() for _ in range(fake.random_int(3, 8))]
    )
    hashtags = factory.LazyAttribute(
        lambda o: [f"#{fake.word()}" for _ in range(fake.random_int(3, 6))]
    )

    # 結構化內容
    hook = factory.LazyAttribute(
        lambda o: fake.sentence(nb_words=8)
    )  # 開場吸引句
    main_points = factory.LazyAttribute(
        lambda o: [
            fake.sentence(nb_words=12) for _ in range(fake.random_int(2, 5))
        ]
    )
    call_to_action = factory.LazyAttribute(lambda o: fake.sentence(nb_words=6))

    # 版本控制
    version = factory.LazyFunction(lambda: fake.random_int(1, 5))
    parent_script_id = None

    # 使用統計
    usage_count = factory.LazyFunction(lambda: fake.random_int(0, 10))
    last_used_at = None

    # 評分和反饋
    quality_score = factory.LazyFunction(lambda: fake.random.uniform(7.0, 9.5))
    user_rating = None
    feedback = None

    @classmethod
    def create_educational_script(cls, **kwargs):
        """建立教育類型腳本"""
        return cls.create(
            script_type=ScriptType.EDUCATIONAL.value,
            tone="professional",
            style="instructional",
            content=fake.text(max_nb_chars=600),
            main_points=[
                "學習的第一步是理解基本概念",
                "實踐是掌握技能的關鍵",
                "持續練習能夠鞏固知識",
            ],
            **kwargs,
        )

    @classmethod
    def create_entertainment_script(cls, **kwargs):
        """建立娛樂類型腳本"""
        return cls.create(
            script_type=ScriptType.ENTERTAINMENT.value,
            tone="humorous",
            style="conversational",
            content=fake.text(max_nb_chars=400),
            hook="今天要跟大家分享一個超有趣的故事！",
            call_to_action="記得按讚分享給朋友們！",
            **kwargs,
        )

    @classmethod
    def create_promotional_script(cls, **kwargs):
        """建立推廣類型腳本"""
        return cls.create(
            script_type=ScriptType.PROMOTIONAL.value,
            tone="persuasive",
            style="persuasive",
            content=fake.text(max_nb_chars=500),
            call_to_action="立即點擊連結了解更多！",
            **kwargs,
        )

    @classmethod
    def create_approved_script(cls, **kwargs):
        """建立已審核通過的腳本"""
        return cls.create(
            status=ScriptStatus.APPROVED.value,
            quality_score=fake.random.uniform(8.5, 9.5),
            user_rating=fake.random_int(4, 5),
            **kwargs,
        )

    @classmethod
    def create_for_red_phase(cls, **kwargs):
        """RED 階段：建立會導致測試失敗的腳本數據"""
        return cls.create(
            title="",  # 無效：空標題
            content="",  # 無效：空內容
            word_count=-1,  # 無效：負數字數
            estimated_duration=-1,  # 無效：負數持續時間
            **kwargs,
        )

    @classmethod
    def create_for_green_phase(cls, **kwargs):
        """GREEN 階段：建立讓測試通過的最簡腳本數據"""
        return cls.create(
            title="測試腳本",
            content="這是一個測試腳本的內容。",
            status=ScriptStatus.GENERATED.value,
            **kwargs,
        )


@register_factory("create_script")
class CreateScriptFactory(factory.Factory, TDDFactoryMixin):
    """
    建立腳本請求數據工廠
    模擬 API 請求中的腳本建立數據
    """

    class Meta:
        model = dict

    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=5))
    project_id = factory.LazyFunction(lambda: fake.uuid4())
    script_type = ScriptType.EDUCATIONAL.value
    target_platform = "tiktok"
    target_audience = "18-34歲年輕人"
    tone = "friendly"
    style = "conversational"

    # 生成設定
    generation_prompt = factory.LazyAttribute(
        lambda o: fake.text(max_nb_chars=150)
    )
    keywords = factory.LazyAttribute(lambda o: [fake.word() for _ in range(3)])
    desired_length = "medium"  # short, medium, long

    @classmethod
    def create_invalid_request(cls, **kwargs):
        """建立無效的腳本建立請求"""
        return cls.build(
            title="",  # 無效：空標題
            project_id="invalid-id",  # 無效：錯誤格式的ID
            script_type="invalid_type",  # 無效：不支援的類型
            **kwargs,
        )

    @classmethod
    def create_minimal_valid_request(cls, **kwargs):
        """建立最簡有效的腳本建立請求"""
        return cls.build(
            title="簡單測試腳本",
            project_id=fake.uuid4(),
            generation_prompt="請生成一個簡單的測試腳本",
            **kwargs,
        )


class ScriptBatchFactory:
    """腳本批次建立工廠"""

    @staticmethod
    def create_project_scripts(
        project_id: str, count: int = 3
    ) -> List[ScriptData]:
        """為特定專案建立多個腳本"""
        scripts = []
        for i in range(count):
            script = ScriptFactory.create(
                project_id=project_id, title=f"專案腳本 {i + 1}", version=i + 1
            )
            scripts.append(script)
        return scripts

    @staticmethod
    def create_different_types_scripts() -> Dict[str, ScriptData]:
        """建立不同類型的腳本"""
        return {
            "educational": ScriptFactory.create_educational_script(),
            "entertainment": ScriptFactory.create_entertainment_script(),
            "promotional": ScriptFactory.create_promotional_script(),
        }


# TDD 輔助函數
def create_test_scripts_scenario(
    project_id: str = None,
) -> Dict[str, ScriptData]:
    """
    建立完整的測試腳本情境
    用於複雜的 TDD 測試場景
    """
    test_project_id = project_id or fake.uuid4()

    return {
        "draft_script": ScriptFactory.create(
            project_id=test_project_id, status=ScriptStatus.DRAFT.value
        ),
        "generated_script": ScriptFactory.create(
            project_id=test_project_id, status=ScriptStatus.GENERATED.value
        ),
        "approved_script": ScriptFactory.create_approved_script(
            project_id=test_project_id
        ),
        "educational_script": ScriptFactory.create_educational_script(
            project_id=test_project_id
        ),
        "entertainment_script": ScriptFactory.create_entertainment_script(
            project_id=test_project_id
        ),
        "invalid_script": ScriptFactory.create_for_red_phase(),
        "valid_script": ScriptFactory.create_for_green_phase(),
    }


def create_script_versions(
    base_script: ScriptData, versions: int = 3
) -> List[ScriptData]:
    """
    建立腳本版本序列
    用於測試版本控制功能
    """
    versions_list = []
    for i in range(versions):
        version_script = ScriptFactory.create(
            project_id=base_script.project_id,
            title=f"{base_script.title} v{i + 2}",
            parent_script_id=base_script.id,
            version=i + 2,
            content=fake.text(max_nb_chars=600),
        )
        versions_list.append(version_script)
    return versions_list


def cleanup_test_scripts(scripts: Dict[str, ScriptData]):
    """
    清理測試腳本數據
    在測試完成後呼叫
    """
    # 清理腳本數據和相關檔案
