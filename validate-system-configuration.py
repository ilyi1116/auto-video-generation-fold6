#!/usr/bin/env python3
"""
系統配置驗證工具
驗證系統現代化後的所有關鍵組件
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class SystemConfigurationValidator:
    """系統配置驗證器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = []
    
    def log_result(self, component: str, status: bool, message: str, details: Dict = None):
        """記錄驗證結果"""
        result = {
            "component": component,
            "status": "✅ PASS" if status else "❌ FAIL",
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}: {message}")
        if details and not status:
            print(f"   詳情: {details}")
    
    def validate_project_structure(self) -> bool:
        """驗證專案結構"""
        print("\n🏗️ 驗證專案結構...")
        
        required_dirs = [
            "src/services",
            "src/frontend", 
            "src/shared",
            "config/environments",
            "infra/monitoring",
            "infra/docker",
            "scripts"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            self.log_result(
                "專案結構",
                False,
                f"缺少 {len(missing_dirs)} 個關鍵目錄",
                {"missing_directories": missing_dirs}
            )
            return False
        
        self.log_result("專案結構", True, "所有關鍵目錄存在")
        return True
    
    def validate_docker_configuration(self) -> bool:
        """驗證 Docker 配置"""
        print("\n🐳 驗證 Docker 配置...")
        
        docker_files = [
            "docker-compose.yml",
            "docker-compose.unified.yml"
        ]
        
        issues = []
        
        for docker_file in docker_files:
            file_path = self.project_root / docker_file
            if not file_path.exists():
                issues.append(f"缺少 {docker_file}")
                continue
            
            # 檢查是否使用新的服務路徑
            content = file_path.read_text()
            if "./services/" in content and "./src/services/" not in content:
                issues.append(f"{docker_file} 仍使用舊路徑 ./services/")
            elif "./src/services/" in content:
                self.log_result(f"Docker {docker_file}", True, "路徑已更新為新結構")
        
        if issues:
            self.log_result(
                "Docker 配置",
                False,
                f"發現 {len(issues)} 個問題",
                {"issues": issues}
            )
            return False
        
        return True
    
    def validate_service_dockerfiles(self) -> bool:
        """驗證服務 Dockerfile"""
        print("\n📦 驗證服務 Dockerfile...")
        
        services_dir = self.project_root / "src" / "services"
        if not services_dir.exists():
            self.log_result("服務 Dockerfile", False, "src/services 目錄不存在")
            return False
        
        services_with_dockerfiles = []
        services_without_dockerfiles = []
        
        for service_dir in services_dir.iterdir():
            if service_dir.is_dir():
                dockerfile = service_dir / "Dockerfile"
                if dockerfile.exists():
                    services_with_dockerfiles.append(service_dir.name)
                else:
                    services_without_dockerfiles.append(service_dir.name)
        
        self.log_result(
            "服務 Dockerfile",
            len(services_without_dockerfiles) == 0,
            f"{len(services_with_dockerfiles)} 個服務有 Dockerfile，{len(services_without_dockerfiles)} 個缺少",
            {
                "with_dockerfile": services_with_dockerfiles,
                "without_dockerfile": services_without_dockerfiles
            }
        )
        
        return len(services_without_dockerfiles) == 0
    
    def validate_configuration_files(self) -> bool:
        """驗證配置檔案"""
        print("\n⚙️ 驗證配置檔案...")
        
        required_configs = [
            "config/environments/development.env",
            "config/environments/production.env",
            "config/load_env.py",
            "pyproject.toml",
            "alembic.ini"
        ]
        
        missing_configs = []
        for config_path in required_configs:
            full_path = self.project_root / config_path
            if not full_path.exists():
                missing_configs.append(config_path)
        
        if missing_configs:
            self.log_result(
                "配置檔案",
                False,
                f"缺少 {len(missing_configs)} 個配置檔案",
                {"missing_configs": missing_configs}
            )
            return False
        
        self.log_result("配置檔案", True, "所有關鍵配置檔案存在")
        return True
    
    def validate_shared_libraries(self) -> bool:
        """驗證共享庫"""
        print("\n📚 驗證共享庫...")
        
        shared_dir = self.project_root / "src" / "shared"
        if not shared_dir.exists():
            self.log_result("共享庫", False, "src/shared 目錄不存在")
            return False
        
        shared_files = [
            "config.py",
            "__init__.py"
        ]
        
        missing_files = []
        for file_name in shared_files:
            file_path = shared_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            self.log_result(
                "共享庫",
                False,
                f"src/shared 缺少 {len(missing_files)} 個檔案",
                {"missing_files": missing_files}
            )
            return False
        
        self.log_result("共享庫", True, "共享庫配置完整")
        return True
    
    def validate_monitoring_configuration(self) -> bool:
        """驗證監控配置"""
        print("\n📊 驗證監控配置...")
        
        monitoring_files = [
            "infra/monitoring/prometheus/prometheus.yml",
            "infra/monitoring/grafana/provisioning/datasources/prometheus.yml"
        ]
        
        missing_files = []
        outdated_configs = []
        
        for config_path in monitoring_files:
            full_path = self.project_root / config_path
            if not full_path.exists():
                missing_files.append(config_path)
                continue
            
            # 檢查 Prometheus 配置是否包含所有服務
            if "prometheus.yml" in config_path:
                content = full_path.read_text()
                required_services = [
                    "storage-service:8009",
                    "api-gateway:8000", 
                    "auth-service:8001"
                ]
                
                for service in required_services:
                    service_name = service.split(':')[0]  # 提取服務名稱
                    service_port = service.split(':')[1]  # 提取端口
                    
                    # 檢查服務是否在配置中
                    if service_name in content and service_port in content:
                        continue  # 服務存在
                    else:
                        outdated_configs.append(f"Prometheus 配置缺少 {service}")
        
        issues = missing_files + outdated_configs
        if issues:
            self.log_result(
                "監控配置",
                False,
                f"發現 {len(issues)} 個問題",
                {"issues": issues}
            )
            return False
        
        self.log_result("監控配置", True, "監控配置完整且最新")
        return True
    
    def validate_ci_cd_configuration(self) -> bool:
        """驗證 CI/CD 配置"""
        print("\n🚀 驗證 CI/CD 配置...")
        
        workflow_dir = self.project_root / ".github" / "workflows"
        if not workflow_dir.exists():
            self.log_result("CI/CD 配置", False, ".github/workflows 目錄不存在")
            return False
        
        required_workflows = [
            "ci-cd-main.yml",
            "dependency-security.yml", 
            "performance-monitoring.yml"
        ]
        
        missing_workflows = []
        for workflow in required_workflows:
            workflow_path = workflow_dir / workflow
            if not workflow_path.exists():
                missing_workflows.append(workflow)
        
        if missing_workflows:
            self.log_result(
                "CI/CD 配置",
                False,
                f"缺少 {len(missing_workflows)} 個工作流程",
                {"missing_workflows": missing_workflows}
            )
            return False
        
        self.log_result("CI/CD 配置", True, "所有 CI/CD 工作流程配置完整")
        return True
    
    def run_full_validation(self) -> Dict:
        """運行完整驗證"""
        print("🔍 開始系統配置驗證...")
        print("=" * 60)
        
        validations = [
            ("專案結構", self.validate_project_structure),
            ("Docker 配置", self.validate_docker_configuration),
            ("服務 Dockerfile", self.validate_service_dockerfiles),
            ("配置檔案", self.validate_configuration_files),
            ("共享庫", self.validate_shared_libraries),
            ("監控配置", self.validate_monitoring_configuration),
            ("CI/CD 配置", self.validate_ci_cd_configuration),
        ]
        
        passed_validations = 0
        total_validations = len(validations)
        
        for name, validation_func in validations:
            try:
                if validation_func():
                    passed_validations += 1
            except Exception as e:
                self.log_result(name, False, f"驗證過程中出現異常: {str(e)}")
        
        # 生成總結報告
        success_rate = (passed_validations / total_validations) * 100
        
        print("\n" + "=" * 60)
        print("📋 驗證總結:")
        print(f"   通過驗證: {passed_validations}/{total_validations}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("   🎉 所有驗證通過！系統配置正確。")
        elif success_rate >= 80:
            print("   ⚠️  大部分驗證通過，但有少數問題需要修復。")
        else:
            print("   ❌ 發現多個問題，需要優先修復。")
        
        # 生成詳細報告
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "success_rate": success_rate
            },
            "results": self.results
        }
        
        # 保存報告
        report_path = self.project_root / "system-validation-report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 詳細報告已保存: {report_path}")
        
        return report


def main():
    """主函數"""
    validator = SystemConfigurationValidator()
    report = validator.run_full_validation()
    
    # 根據結果返回適當的退出碼
    if report['summary']['success_rate'] == 100:
        sys.exit(0)
    elif report['summary']['success_rate'] >= 80:
        sys.exit(1)  # 警告
    else:
        sys.exit(2)  # 錯誤


if __name__ == "__main__":
    main()