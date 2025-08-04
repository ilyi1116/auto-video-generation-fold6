# 用戶測試數據工廠
# 遵循 TDD 原則的用戶數據生成

import factory
from faker import Faker
from datetime import datetime, timezone
from typing import Dict

from .base_factory import (
    TDDFactoryMixin,
    CommonFieldsMixin,
    register_factory,
)

fake = Faker(["zh_TW", "en_US"])


class UserData:
    """用戶數據類別（用於不需要 ORM 的測試）"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@register_factory("user")
class UserFactory(factory.Factory, TDDFactoryMixin, CommonFieldsMixin):
    """
    用戶工廠
    為 TDD 測試提供各種用戶數據情境
    """

    class Meta:
        model = UserData

    # 基本欄位
    username = factory.LazyAttribute(lambda o: fake.user_name())
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    full_name = factory.LazyAttribute(lambda o: fake.name())

    # 密碼相關
    hashed_password = factory.LazyFunction(
        lambda: "$2b$12$test_hash_for_password_123"
    )

    # 狀態欄位
    is_active = True
    is_verified = True
    is_premium = False

    # 個人資訊
    avatar_url = factory.LazyAttribute(
        lambda o: f"https://example.com/avatars/{o.username}.jpg"
    )
    bio = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=150))
    website = factory.LazyAttribute(lambda o: fake.url())

    # 偏好設定
    language = "zh-TW"
    timezone = "Asia/Taipei"
    theme = "light"

    # 統計數據
    video_count = factory.LazyFunction(lambda: fake.random_int(0, 100))
    follower_count = factory.LazyFunction(lambda: fake.random_int(0, 1000))
    following_count = factory.LazyFunction(lambda: fake.random_int(0, 500))

    # 時間戳記
    last_login_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    premium_expires_at = None

    @classmethod
    def create_admin_user(cls, **kwargs):
        """建立管理員用戶"""
        return cls.create(
            username="admin",
            email="admin@example.com",
            is_premium=True,
            **kwargs,
        )

    @classmethod
    def create_premium_user(cls, **kwargs):
        """建立高級用戶"""
        return cls.create(
            is_premium=True,
            premium_expires_at=factory.LazyFunction(
                lambda: datetime.now(timezone.utc).replace(year=2025)
            ),
            **kwargs,
        )

    @classmethod
    def create_inactive_user(cls, **kwargs):
        """建立未啟用用戶"""
        return cls.create(is_active=False, is_verified=False, **kwargs)

    @classmethod
    def create_for_red_phase(cls, **kwargs):
        """RED 階段：建立會導致測試失敗的用戶數據"""
        # 例如：無效的 email 格式
        return cls.create(
            email="invalid-email",  # 無效 email
            username="",  # 空用戶名
            **kwargs,
        )

    @classmethod
    def create_for_green_phase(cls, **kwargs):
        """GREEN 階段：建立讓測試通過的最簡用戶數據"""
        return cls.create(
            username="testuser", email="test@example.com", **kwargs
        )


@register_factory("create_user")
class CreateUserFactory(factory.Factory, TDDFactoryMixin):
    """
    建立用戶請求數據工廠
    模擬 API 請求中的用戶建立數據
    """

    class Meta:
        model = dict

    username = factory.LazyAttribute(lambda o: fake.user_name())
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    password = "SecurePassword123!"
    full_name = factory.LazyAttribute(lambda o: fake.name())
    language = "zh-TW"
    timezone = "Asia/Taipei"

    @classmethod
    def create_invalid_request(cls, **kwargs):
        """建立無效的用戶建立請求"""
        return cls.build(
            username="",  # 無效：空用戶名
            email="invalid-email",  # 無效：錯誤格式
            password="123",  # 無效：密碼太短
            **kwargs,
        )

    @classmethod
    def create_duplicate_request(cls, existing_user: UserData, **kwargs):
        """建立重複的用戶建立請求"""
        return cls.build(
            username=existing_user.username,  # 重複用戶名
            email=existing_user.email,  # 重複 email
            **kwargs,
        )


# TDD 輔助函數
def create_test_users_scenario() -> Dict[str, UserData]:
    """
    建立完整的測試用戶情境
    用於複雜的 TDD 測試場景
    """
    return {
        "active_user": UserFactory.create_for_green_phase(),
        "inactive_user": UserFactory.create_inactive_user(),
        "premium_user": UserFactory.create_premium_user(),
        "admin_user": UserFactory.create_admin_user(),
        "invalid_user": UserFactory.create_for_red_phase(),
    }


def cleanup_test_users(users: Dict[str, UserData]):
    """
    清理測試用戶數據
    在測試完成後呼叫
    """
    # 這裡可以加入清理邏輯
    # 例如：從資料庫刪除測試數據
