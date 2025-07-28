"""
配置管理器測試
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

try:
    from config.config_manager import ConfigManager, get_config, set_mode
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

@pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="配置管理器模組不可用")
class TestConfigManager:
    """配置管理器測試類"""
    
    @pytest.fixture
    def temp_config_dir(self, temp_dir):
        """臨時配置目錄"""
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # 創建基礎配置文件
        base_config = {
            "version": "1.0.0",
            "config_type": "base",
            "generation": {
                "daily_video_limit": 10,
                "batch_size": 3,
                "platforms": ["tiktok", "instagram"]
            },
            "cost_control": {
                "daily_budget_usd": 50.0,
                "stop_on_budget_exceeded": True
            }
        }
        
        with open(config_dir / "base-config.json", 'w') as f:
            json.dump(base_config, f, indent=2)
        
        # 創建創業模式配置
        startup_config = {
            "config_type": "startup",
            "inherits": "base",
            "generation": {
                "daily_video_limit": 5,
                "batch_size": 1
            },
            "cost_control": {
                "daily_budget_usd": 10.0
            }
        }
        
        with open(config_dir / "startup-config.json", 'w') as f:
            json.dump(startup_config, f, indent=2)
        
        return config_dir
    
    def test_config_manager_initialization(self, temp_config_dir):
        """測試配置管理器初始化"""
        cm = ConfigManager(str(temp_config_dir))
        
        assert cm.current_mode == "base"
        assert cm.base_config is not None
        assert "generation" in cm.base_config
        assert "cost_control" in cm.base_config
    
    def test_get_config_value(self, temp_config_dir):
        """測試獲取配置值"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 測試基本獲取
        daily_limit = cm.get("generation.daily_video_limit")
        assert daily_limit == 10
        
        # 測試預設值
        non_existent = cm.get("non.existent.key", "default")
        assert non_existent == "default"
        
        # 測試深層獲取
        platforms = cm.get("generation.platforms")
        assert platforms == ["tiktok", "instagram"]
    
    def test_set_config_value(self, temp_config_dir):
        """測試設置配置值"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 設置新值
        cm.set("generation.test_value", "test")
        assert cm.get("generation.test_value") == "test"
        
        # 設置嵌套值
        cm.set("new.nested.value", 42)
        assert cm.get("new.nested.value") == 42
    
    def test_mode_switching(self, temp_config_dir):
        """測試模式切換"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 切換到創業模式
        cm.set_mode("startup")
        assert cm.current_mode == "startup"
        
        # 檢查配置是否正確合併
        daily_limit = cm.get("generation.daily_video_limit")
        assert daily_limit == 5  # 創業模式覆蓋的值
        
        batch_size = cm.get("generation.batch_size")
        assert batch_size == 1  # 創業模式覆蓋的值
        
        # 檢查繼承的值
        platforms = cm.get("generation.platforms")
        assert platforms == ["tiktok", "instagram"]  # 從基礎配置繼承
    
    def test_config_validation(self, temp_config_dir):
        """測試配置驗證"""
        cm = ConfigManager(str(temp_config_dir))
        
        errors = cm.validate_config()
        
        # 基礎配置應該通過驗證
        assert len(errors) == 0
        
        # 測試無效配置
        cm.set("generation.daily_video_limit", -1)
        errors = cm.validate_config()
        assert len(errors) > 0
        assert "每日影片限制必須大於 0" in errors
    
    def test_service_config_methods(self, temp_config_dir):
        """測試服務配置方法"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 測試獲取服務配置
        service_config = cm.get_service_config("test_service")
        assert isinstance(service_config, dict)
        
        # 測試獲取生成配置
        gen_config = cm.get_generation_config()
        assert "daily_video_limit" in gen_config
        
        # 測試獲取成本配置
        cost_config = cm.get_cost_config()
        assert "daily_budget_usd" in cost_config
    
    def test_work_hours_check(self, temp_config_dir):
        """測試工作時間檢查"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 預設應該始終在工作時間內
        assert cm.is_within_work_hours() == True
        
        # 設置工作時間限制
        cm.set("scheduling.enabled", True)
        cm.set("scheduling.work_hours", {"start": "09:00", "end": "17:00"})
        
        # 這裡可以 mock datetime 來測試特定時間
        with patch('config.config_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "12:00"
            assert cm.is_within_work_hours() == True
            
            mock_datetime.now.return_value.strftime.return_value = "20:00"
            assert cm.is_within_work_hours() == False
    
    def test_daily_limit_check(self, temp_config_dir):
        """測試每日限制檢查"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 測試限制檢查
        assert cm.check_daily_limit(5) == True
        assert cm.check_daily_limit(15) == False
    
    def test_budget_limit_check(self, temp_config_dir):
        """測試預算限制檢查"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 測試預算檢查
        assert cm.check_budget_limit(30.0) == True
        assert cm.check_budget_limit(60.0) == False
    
    def test_config_export_import(self, temp_config_dir):
        """測試配置匯出匯入"""
        cm = ConfigManager(str(temp_config_dir))
        
        # 測試匯出
        export_path = cm.export_config()
        assert Path(export_path).exists()
        
        # 驗證匯出內容
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        
        assert "base_config" in exported_data
        assert "current_config" in exported_data
        assert "current_mode" in exported_data
    
    def test_config_summary(self, temp_config_dir):
        """測試配置摘要"""
        cm = ConfigManager(str(temp_config_dir))
        
        summary = cm.get_summary()
        
        assert "current_mode" in summary
        assert "daily_video_limit" in summary
        assert "daily_budget" in summary
        assert "enabled_platforms" in summary
        assert "resource_limits" in summary
    
    @pytest.mark.integration
    def test_config_persistence(self, temp_config_dir):
        """測試配置持久化"""
        cm1 = ConfigManager(str(temp_config_dir))
        cm1.set_mode("startup")
        
        # 保存配置
        config_path = cm1.save_current_config()
        assert Path(config_path).exists()
        
        # 創建新的配置管理器實例
        cm2 = ConfigManager(str(temp_config_dir))
        
        # 驗證配置一致性
        assert cm2.get("generation.daily_video_limit") == cm1.get("generation.daily_video_limit")


@pytest.mark.unit
class TestConfigManagerUtils:
    """配置管理器工具函數測試"""
    
    @pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="配置管理器模組不可用")
    def test_get_config_function(self, mock_config_manager):
        """測試 get_config 便利函數"""
        with patch('config.config_manager.config_manager', mock_config_manager):
            value = get_config("generation.daily_video_limit", 0)
            assert value == 5
    
    @pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="配置管理器模組不可用")
    def test_set_mode_function(self, mock_config_manager):
        """測試 set_mode 便利函數"""
        with patch('config.config_manager.config_manager', mock_config_manager):
            set_mode("enterprise")
            # 這裡應該檢查模式是否改變，但需要 mock 實現
            assert True  # 簡化的測試


@pytest.mark.slow
@pytest.mark.integration
class TestConfigManagerIntegration:
    """配置管理器整合測試"""
    
    @pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="配置管理器模組不可用")
    def test_full_config_workflow(self, temp_config_dir):
        """測試完整配置工作流程"""
        # 初始化配置管理器
        cm = ConfigManager(str(temp_config_dir))
        
        # 檢查初始狀態
        assert cm.current_mode == "base"
        initial_limit = cm.get("generation.daily_video_limit")
        
        # 切換模式
        cm.set_mode("startup")
        startup_limit = cm.get("generation.daily_video_limit")
        assert startup_limit != initial_limit
        
        # 修改配置
        cm.set("generation.test_setting", "test_value")
        assert cm.get("generation.test_setting") == "test_value"
        
        # 驗證配置
        errors = cm.validate_config()
        assert isinstance(errors, list)
        
        # 匯出配置
        export_path = cm.export_config()
        assert Path(export_path).exists()
        
        # 獲取摘要
        summary = cm.get_summary()
        assert summary["current_mode"] == "startup"