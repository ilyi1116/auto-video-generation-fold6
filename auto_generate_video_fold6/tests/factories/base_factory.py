# 基礎工廠類別
# 為 TDD 測試提供統一的數據生成接口

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic
from datetime import datetime, timezone
import uuid
import factory
from faker import Faker

fake = Faker(["zh_TW", "en_US"])  # 支援繁體中文和英文

T = TypeVar("T")


class BaseFactory(ABC, Generic[T]):
    """
    基礎工廠抽象類別
    為所有測試數據工廠提供統一接口
    """

    @abstractmethod
    def create(self, **kwargs) -> T:
        """建立一個測試實例"""
        pass

    @abstractmethod
    def build(self, **kwargs) -> T:
        """建構但不保存的測試實例（用於單元測試）"""
        pass

    @abstractmethod
    def create_batch(self, size: int, **kwargs) -> list[T]:
        """建立多個測試實例"""
        pass


class TDDFactoryMixin:
    """
    TDD 工廠混合類別
    提供 TDD 特定的工廠方法
    """

    @classmethod
    def create_for_red_phase(cls, **kwargs):
        """
        RED 階段：建立會導致測試失敗的數據
        例如：無效的輸入、邊界條件等
        """
        return cls.create(**kwargs)

    @classmethod
    def create_for_green_phase(cls, **kwargs):
        """
        GREEN 階段：建立讓測試通過的最簡數據
        """
        return cls.create(**kwargs)

    @classmethod
    def create_for_refactor_phase(cls, **kwargs):
        """
        REFACTOR 階段：建立測試重構的數據
        確保重構後行為不變
        """
        return cls.create(**kwargs)


class CommonFieldsMixin:
    """提供常用欄位的混合類別"""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    @factory.lazy_attribute
    def name(self):
        return fake.name()

    @factory.lazy_attribute
    def email(self):
        return fake.unique.email()

    @factory.lazy_attribute
    def description(self):
        return fake.text(max_nb_chars=200)


class FactoryRegistry:
    """
    工廠註冊器
    管理所有測試工廠的中央註冊表
    """

    _factories: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, factory_class: Any):
        """註冊工廠"""
        cls._factories[name] = factory_class

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """獲取工廠"""
        return cls._factories.get(name)

    @classmethod
    def list_all(cls) -> Dict[str, Any]:
        """列出所有工廠"""
        return cls._factories.copy()


def register_factory(name: str):
    """裝飾器：自動註冊工廠"""

    def decorator(factory_class):
        FactoryRegistry.register(name, factory_class)
        return factory_class

    return decorator
