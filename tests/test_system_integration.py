"""
系統集成測試 - 簡化版本驗證核心功能
"""

import sys
from pathlib import Path

import pytest

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_database_models_import():
    """測試數據庫模型導入"""
    from src.shared.database import (
        ProcessingTask,
        User,
        Video,
        VideoAsset,
    )

    # 驗證模型類存在且正確定義
    assert hasattr(User, "__tablename__")
    assert hasattr(Video, "__tablename__")
    assert hasattr(VideoAsset, "__tablename__")
    assert hasattr(ProcessingTask, "__tablename__")

    # 驗證基本屬性
    assert hasattr(User, "email")
    assert hasattr(Video, "title")
    assert hasattr(VideoAsset, "asset_type")
    assert hasattr(ProcessingTask, "task_type")


@pytest.mark.asyncio
async def test_shared_services_import():
    """測試共享服務模塊導入"""
    from src.shared.services import (
        ServiceInstance,
        ServiceRegistry,
        ServiceStatus,
    )

    # 創建服務註冊表
    registry = ServiceRegistry()

    # 創建測試服務實例
    service = ServiceInstance("test-service", "localhost", 8888, status=ServiceStatus.HEALTHY)

    # 註冊服務
    registry.register_service(service)

    # 驗證服務註冊
    instances = registry.get_service_instances("test-service")
    assert len(instances) == 1
    assert instances[0].name == "test-service"


@pytest.mark.asyncio
async def test_service_communication():
    """測試服務間通訊功能"""
    from src.shared.services import (
        LoadBalancingStrategy,
        ServiceRegistry,
    )

    registry = ServiceRegistry()

    # 註冊多個測試服務
    from src.shared.services import ServiceInstance, ServiceStatus

    for i in range(3):
        service = ServiceInstance(
            "multi-service", f"host{i}", 8000 + i, status=ServiceStatus.HEALTHY
        )
        registry.register_service(service)

    # 測試負載均衡
    strategies = [
        LoadBalancingStrategy.ROUND_ROBIN,
        LoadBalancingStrategy.RANDOM,
        LoadBalancingStrategy.LEAST_CONNECTIONS,
        LoadBalancingStrategy.HEALTH_BASED,
    ]

    for strategy in strategies:
        instance = registry.select_instance("multi-service", strategy)
        assert instance is not None
        assert instance.name == "multi-service"


@pytest.mark.asyncio
async def test_message_queue_functionality():
    """測試消息隊列功能"""
    try:
        from src.shared.services.message_queue import (
            MessageQueue,
        )

        # 創建內存測試隊列
        queue = MessageQueue("redis://localhost:6379/15")

        # 測試基本隊列操作（模擬）
        test_message = {"type": "test_event", "data": {"key": "value"}}

        # 這裡我們只測試對象創建，不測試實際的Redis連接
        assert queue is not None
        assert hasattr(queue, "add_task")
        assert hasattr(queue, "publish_event")

    except ImportError:
        pytest.skip("消息隊列模塊不可用")


@pytest.mark.asyncio
async def test_configuration_loading():
    """測試配置加載"""
    import os

    # 設置測試環境變量
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

    from src.shared.database.connection import AsyncSessionLocal, async_engine

    # 驗證配置正確加載
    assert AsyncSessionLocal is not None
    assert async_engine is not None


def test_project_structure():
    """測試項目結構完整性"""
    project_root = Path(__file__).parent.parent

    # 驗證核心目錄存在
    essential_dirs = [
        "src",
        "src/shared",
        "src/shared/database",
        "src/shared/services",
        "src/services",
        "tests",
        "config",
    ]

    for dir_path in essential_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Missing directory: {dir_path}"


def test_core_files_exist():
    """測試核心文件存在"""
    project_root = Path(__file__).parent.parent

    core_files = [
        "docker-compose.yml",
        "pyproject.toml",
        "src/shared/database/models.py",
        "src/shared/database/connection.py",
        "src/shared/services/service_discovery.py",
    ]

    for file_path in core_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Missing file: {file_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
