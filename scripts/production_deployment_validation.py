#!/usr/bin/env python3
"""
生產環境部署驗證腳本
驗證系統是否準備好進行生產部署
"""

import asyncio
import importlib
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.paren
sys.path.insert(0, str(project_root))


class ProductionValidator:
    """生產環境驗證器"""

    def __init__(self):
        self.results = []
        self.passed_tests = 0
        self.total_tests = 0

    def test(self, name: str, result: bool, details: str = ""):
        """記錄測試結果"""
        self.total_tests += 1
        if result:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        self.results.append(f"{status} {name}")
        if details:
            self.results.append(f"    {details}")

    def validate_project_structure(self) -> bool:
        """驗證項目結構"""
        print("🔍 驗證項目結構...")

        essential_dirs = [
            "src",
            "src/shared",
            "src/shared/database",
            "src/shared/services",
            "src/services",
            "tests",
            "config",
        ]

        all_exist = True
        for dir_path in essential_dirs:
            full_path = project_root / dir_path
            exists = full_path.exists()
            self.test(f"Directory exists: {dir_path}", exists)
            if not exists:
                all_exist = False

        return all_exis

    def validate_core_files(self) -> bool:
        """驗證核心文件存在"""
        print("📁 驗證核心文件...")

        core_files = [
            "docker-compose.yml",
            "pyproject.toml",
            "src/shared/database/models.py",
            "src/shared/database/connection.py",
            "src/shared/services/service_discovery.py",
            "src/shared/services/message_queue.py",
        ]

        all_exist = True
        for file_path in core_files:
            full_path = project_root / file_path
            exists = full_path.exists()
            self.test(f"Core file exists: {file_path}", exists)
            if not exists:
                all_exist = False

        return all_exis

    def validate_configuration_files(self) -> bool:
        """驗證配置文件"""
        print("⚙️ 驗證配置文件...")

        config_files = [
            "config/environments/development.env",
            "config/environments/production.env",
            "config/environments/testing.env",
            "config/monitoring-config.yaml",
            "config/logging-config.yaml",
        ]

        all_exist = True
        for file_path in config_files:
            full_path = project_root / file_path
            exists = full_path.exists()
            self.test(f"Config file exists: {file_path}", exists)
            if not exists:
                all_exist = False

        return all_exis

    def validate_service_directories(self) -> bool:
        """驗證服務目錄結構"""
        print("🏢 驗證服務目錄結構...")

        services = [
            "api-gateway",
            "auth-service",
            "video-service",
            "ai-service",
        ]

        all_exist = True
        for service in services:
            service_dir = project_root / "src" / "services" / service
            exists = service_dir.exists()
            self.test(f"Service directory: {service}", exists)

            if exists:
                # 檢查Dockerfile
                dockerfile = service_dir / "Dockerfile"
                has_dockerfile = dockerfile.exists()
                self.test(f"Dockerfile for {service}", has_dockerfile)
                if not has_dockerfile:
                    all_exist = False
            else:
                all_exist = False

        return all_exis

    def validate_imports(self) -> bool:
        """驗證關鍵模塊可以導入"""
        print("📦 驗證關鍵模塊導入...")

        modules_to_test = [
            "src.shared.database.models",
            "src.shared.database.connection",
            "src.shared.services.service_discovery",
            "src.shared.services.message_queue",
            "src.shared.config",
        ]

        all_imported = True
        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
                self.test(f"Import {module_name}", True)
            except Exception as e:
                self.test(f"Import {module_name}", False, f"Error: {str(e)}")
                all_imported = False

        return all_imported

    async def validate_database_models(self) -> bool:
        """驗證數據庫模型"""
        print("🗄️ 驗證數據庫模型...")

        try:
            from src.shared.database import User, Video, VideoAsset, ProcessingTask

            # 檢查模型屬性
            models_ok = True

            # 檢查User模型
            user_attrs = hasattr(User, '__tablename__') and hasattr(User, 'email')
            self.test("User model structure", user_attrs)
            if not user_attrs:
                models_ok = False

            # 檢查Video模型
            video_attrs = hasattr(Video, '__tablename__') and hasattr(Video, 'title')
            self.test("Video model structure", video_attrs)
            if not video_attrs:
                models_ok = False

            # 檢查VideoAsset模型
            asset_attrs = hasattr(VideoAsset, '__tablename__') and hasattr(VideoAsset, 'asset_type')
            self.test("VideoAsset model structure", asset_attrs)
            if not asset_attrs:
                models_ok = False

            # 檢查ProcessingTask模型
            task_attrs = hasattr(ProcessingTask, '__tablename__') and hasattr(ProcessingTask, 'task_type')
            self.test("ProcessingTask model structure", task_attrs)
            if not task_attrs:
                models_ok = False

            return models_ok

        except Exception as e:
            self.test("Database models import", False, f"Error: {str(e)}")
            return False

    async def validate_service_discovery(self) -> bool:
        """驗證服務發現功能"""
        print("🔍 驗證服務發現功能...")

        try:
            from src.shared.services import ServiceRegistry, ServiceInstance, ServiceStatus

            registry = ServiceRegistry()

            # 創建測試服務
            test_service = ServiceInstance(
                "test-validation-service",
                "localhost",
                9999,
                status=ServiceStatus.HEALTHY
            )

            # 註冊服務
            registry.register_service(test_service)

            # 驗證服務註冊
            instances = registry.get_service_instances("test-validation-service")
            service_registered = len(instances) == 1 and instances[0].name == "test-validation-service"
            self.test("Service registration", service_registered)

            return service_registered

        except Exception as e:
            self.test("Service discovery validation", False, f"Error: {str(e)}")
            return False

    async def validate_message_queue(self) -> bool:
        """驗證消息隊列功能"""
        print("💌 驗證消息隊列功能...")

        try:
            from src.shared.services.message_queue import MessageQueue

            # 創建測試隊列
            queue = MessageQueue("redis://localhost:6379/15")

            # 檢查基本方法存在
            has_methods = (
                hasattr(queue, 'add_task')
                and hasattr(queue, 'publish_event')
                and hasattr(queue, 'publish')
            )

            self.test("MessageQueue methods available", has_methods)
            return has_methods

        except Exception as e:
            self.test("Message queue validation", False, f"Error: {str(e)}")
            return False

    def validate_docker_compose(self) -> bool:
        """驗證Docker Compose配置"""
        print("🐳 驗證Docker Compose配置...")

        try:
            import subprocess

            # 檢查docker-compose命令
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True
            )
            docker_available = result.returncode == 0
            self.test("Docker Compose available", docker_available)

            if not docker_available:
                return False

            # 驗證docker-compose.yml語法
            result = subprocess.run(
                ["docker-compose", "config", "--quiet"],
                capture_output=True,
                text=True,
                cwd=project_roo
            )
            config_valid = result.returncode == 0
            self.test("Docker Compose config syntax", config_valid)

            return config_valid

        except Exception as e:
            self.test("Docker Compose validation", False, f"Error: {str(e)}")
            return False

    async def run_validation(self) -> Tuple[bool, List[str]]:
        """運行完整驗證"""
        print("🚀 開始生產環境部署驗證...\n")
        start_time = time.time()

        # 運行所有驗證
        validations = [
            self.validate_project_structure(),
            self.validate_core_files(),
            self.validate_configuration_files(),
            self.validate_service_directories(),
            self.validate_imports(),
            await self.validate_database_models(),
            await self.validate_service_discovery(),
            await self.validate_message_queue(),
            self.validate_docker_compose(),
        ]

        all_passed = all(validations)
        end_time = time.time()

        # 生成報告
        print(f"\n{'='*60}")
        print("📊 生產環境部署驗證報告")
        print(f"{'='*60}")

        for result in self.results:
            print(result)

        print("\n📈 驗證統計:")
        print(f"   總測試數量: {self.total_tests}")
        print(f"   通過測試: {self.passed_tests}")
        print(f"   失敗測試: {self.total_tests - self.passed_tests}")
        print(f"   成功率: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"   驗證時間: {end_time - start_time:.2f}秒")

        if all_passed:
            print("\n🎉 生產環境部署驗證通過！")
            print("   系統已準備好進行生產部署。")
        else:
            print("\n⚠️ 生產環境部署驗證失敗！")
            print("   請修復失敗的項目後重新驗證。")

        return all_passed, self.results


async def main():
    """主函數"""
    validator = ProductionValidator()
    success, results = await validator.run_validation()

    # 返回適當的退出碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
