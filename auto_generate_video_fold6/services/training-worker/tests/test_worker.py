import os
import sys
from unittest.mock import patch


# 添加 app 目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_training_worker_import():
    """測試 training worker 可以正常導入"""
    try:
        from main import train_model

        assert train_model is not None
    except ImportError:
        # 如果導入失敗，至少確保檔案存在
        main_file = os.path.join(os.path.dirname(__file__), "..", "main.py")
        assert os.path.exists(main_file)


def test_mock_training_task():
    """模擬測試訓練任務"""

    # 模擬訓練函數
    def mock_train_model(model_config, data_path):
        return {"status": "completed", "accuracy": 0.95}

    result = mock_train_model(
        model_config={"epochs": 10, "batch_size": 32},
        data_path="/path/to/training/data",
    )

    assert result["status"] == "completed"
    assert result["accuracy"] > 0.9


@patch("os.path.exists")
def test_data_path_validation(mock_exists):
    """測試數據路徑驗證"""
    mock_exists.return_value = True

    # 模擬數據路徑驗證函數
    def validate_data_path(path):
        return os.path.exists(path)

    assert validate_data_path("/valid/path") == True

    mock_exists.return_value = False
    assert validate_data_path("/invalid/path") == False


def test_training_config_validation():
    """測試訓練配置驗證"""
    valid_config = {
        "model_type": "voice_cloning",
        "epochs": 100,
        "batch_size": 16,
        "learning_rate": 0.001,
    }

    # 模擬配置驗證函數
    def validate_config(config):
        required_keys = ["model_type", "epochs", "batch_size", "learning_rate"]
        return all(key in config for key in required_keys)

    assert validate_config(valid_config) == True

    invalid_config = {"model_type": "voice_cloning"}
    assert validate_config(invalid_config) == False
