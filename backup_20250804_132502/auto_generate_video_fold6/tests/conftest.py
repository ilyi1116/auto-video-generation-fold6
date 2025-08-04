"""
測試配置文件 - 全域測試固件和設定
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import sys

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """創建事件迴圈"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """測試數據目錄"""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_dir():
    """臨時目錄"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_env_vars():
    """模擬環境變數"""
    original_env = os.environ.copy()

    # 設置測試環境變數
    test_env = {
        "OPENAI_API_KEY": "test-openai-key",
        "STABILITY_API_KEY": "test-stability-key",
        "ELEVENLABS_API_KEY": "test-elevenlabs-key",
        "JWT_SECRET": "test-jwt-secret-key",
        "DATABASE_URL": "sqlite:///test.db",
        "REDIS_URL": "redis://localhost:6379/15",  # 使用測試資料庫
        "NODE_ENV": "test",
        "PYTHON_ENV": "test",
    }

    os.environ.update(test_env)
    yield test_env

    # 恢復原始環境變數
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_config_manager():
    """模擬配置管理器"""

    class MockConfigManager:
        def __init__(self):
            self.current_mode = "test"
            self.config_data = {
                "generation": {
                    "daily_video_limit": 5,
                    "batch_size": 2,
                    "platforms": ["tiktok", "instagram"],
                },
                "cost_control": {
                    "daily_budget_usd": 10.0,
                    "stop_on_budget_exceeded": True,
                },
                "ai_services": {
                    "text_generation": {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                    },
                    "image_generation": {
                        "provider": "stability",
                        "model": "stable-diffusion-xl",
                    },
                    "voice_synthesis": {
                        "provider": "elevenlabs",
                        "voice_id": "test-voice",
                    },
                },
            }

        def get(self, key_path, default=None):
            keys = key_path.split(".")
            current = self.config_data
            try:
                for key in keys:
                    current = current[key]
                return current
            except (KeyError, TypeError):
                return default

        def set(self, key_path, value):
            keys = key_path.split(".")
            current = self.config_data
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value

    return MockConfigManager()


@pytest.fixture
def mock_cost_tracker():
    """模擬成本追蹤器"""

    class MockCostTracker:
        def __init__(self):
            self.total_cost = 0.0
            self.calls = []

        async def track_api_call(
            self, provider, model, operation_type, **kwargs
        ):
            cost = 0.1  # 固定測試成本
            self.total_cost += cost
            self.calls.append(
                {
                    "provider": provider,
                    "model": model,
                    "operation_type": operation_type,
                    "cost": cost,
                    **kwargs,
                }
            )
            return cost

        async def get_daily_summary(self):
            return {
                "total_cost": self.total_cost,
                "api_calls_count": len(self.calls),
                "budget_remaining": 10.0 - self.total_cost,
                "is_over_budget": self.total_cost > 10.0,
            }

        async def check_budget_status(self):
            return {
                "current_cost": self.total_cost,
                "budget_limit": 10.0,
                "budget_remaining": 10.0 - self.total_cost,
                "usage_percentage": (self.total_cost / 10.0) * 100,
                "is_over_budget": self.total_cost > 10.0,
                "can_continue": self.total_cost <= 10.0,
            }

    return MockCostTracker()


@pytest.fixture
def mock_redis_client():
    """模擬 Redis 客戶端"""

    class MockRedis:
        def __init__(self):
            self.data = {}

        async def get(self, key):
            return self.data.get(key)

        async def set(self, key, value, ex=None):
            self.data[key] = value
            return True

        async def delete(self, key):
            return self.data.pop(key, None) is not None

        async def exists(self, key):
            return key in self.data

        async def ping(self):
            return True

        def close(self):
            pass

    return MockRedis()


@pytest.fixture
def mock_openai_client():
    """模擬 OpenAI 客戶端"""

    class MockOpenAI:
        def __init__(self):
            self.chat = MagicMock()
            self.chat.completions = MagicMock()
            self.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[
                        MagicMock(message=MagicMock(content="測試生成的內容"))
                    ],
                    usage=MagicMock(
                        prompt_tokens=10, completion_tokens=20, total_tokens=30
                    ),
                )
            )

    return MockOpenAI()


@pytest.fixture
def sample_video_data():
    """範例影片數據"""
    return {
        "title": "測試影片標題",
        "description": "這是一個測試影片的描述",
        "script": "這是測試影片腳本內容",
        "platforms": ["tiktok", "instagram"],
        "style": {
            "theme": "technology",
            "tone": "professional",
            "duration": 60,
        },
        "generated_content": {
            "images": ["image1.jpg", "image2.jpg"],
            "audio": "audio.mp3",
            "video": "final_video.mp4",
        },
    }


@pytest.fixture
def sample_trends_data():
    """範例趨勢數據"""
    return [
        {
            "keyword": "AI technology",
            "search_volume": 1000000,
            "trend_score": 95,
            "region": "US",
            "category": "Technology",
        },
        {
            "keyword": "machine learning",
            "search_volume": 800000,
            "trend_score": 87,
            "region": "US",
            "category": "Technology",
        },
        {
            "keyword": "automation tools",
            "search_volume": 500000,
            "trend_score": 73,
            "region": "US",
            "category": "Business",
        },
    ]


@pytest.fixture
def mock_http_client():
    """模擬 HTTP 客戶端"""

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.status = status_code

        async def json(self):
            return self.json_data

        async def text(self):
            return str(self.json_data)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockHTTPClient:
        def __init__(self):
            self.responses = {}

        def set_response(self, url, response_data, status_code=200):
            self.responses[url] = MockResponse(response_data, status_code)

        async def get(self, url, **kwargs):
            return self.responses.get(
                url, MockResponse({"error": "Not mocked"}, 404)
            )

        async def post(self, url, **kwargs):
            return self.responses.get(
                url, MockResponse({"success": True}, 200)
            )

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockHTTPClient()


@pytest.fixture(autouse=True)
def setup_test_logging():
    """設置測試日誌"""
    import logging

    # 設置測試日誌級別
    logging.getLogger().setLevel(logging.DEBUG)

    # 禁用某些模組的日誌避免干擾
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


@pytest.fixture
def mock_file_system(temp_dir):
    """模擬文件系統"""

    class MockFileSystem:
        def __init__(self, base_dir):
            self.base_dir = Path(base_dir)
            self.base_dir.mkdir(exist_ok=True)

        def create_file(self, path, content=""):
            file_path = self.base_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return file_path

        def create_dir(self, path):
            dir_path = self.base_dir / path
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path

        def get_path(self, path):
            return self.base_dir / path

    return MockFileSystem(temp_dir)


# 測試標記的跳過條件
def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow running tests")


def pytest_collection_modifyitems(config, items):
    """修改測試項目"""
    if config.getoption("--runslow"):
        # 如果指定了 --runslow，不跳過任何測試
        return

    skip_slow = pytest.mark.skip(reason="使用 --runslow 來執行緩慢測試")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """添加命令行選項"""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="執行標記為 slow 的測試",
    )
    parser.addoption(
        "--runintegration",
        action="store_true",
        default=False,
        help="執行整合測試",
    )
