#!/usr/bin/env python3
"""
備份配置驗證腳本
驗證備份相關配置和依賴項的正確性
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# 設置日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """驗證結果"""

    component: str
    success: bool
    message: str
    details: Optional[Dict] = None


class BackupConfigValidator:
    """備份配置驗證器"""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.project_root = Path(__file__).parent.parent

    def validate_backup_scripts(self) -> ValidationResult:
        """驗證備份腳本存在性和可執行性"""
        try:
            backup_scripts = [
                "scripts/backup_manager.py",
                "scripts/backup-system.sh",
                "scripts/restore-system.sh",
                "scripts/disaster_recovery.py",
            ]

            missing_scripts = []
            non_executable = []

            for script_path in backup_scripts:
                full_path = self.project_root / script_path
                if not full_path.exists():
                    missing_scripts.append(script_path)
                elif not os.access(full_path, os.X_OK):
                    non_executable.append(script_path)

            if missing_scripts:
                return ValidationResult(
                    component="備份腳本",
                    success=False,
                    message=f"缺少備份腳本: {', '.join(missing_scripts)}",
                )

            if non_executable:
                return ValidationResult(
                    component="備份腳本",
                    success=False,
                    message=f"腳本不可執行: {', '.join(non_executable)}",
                )

            return ValidationResult(
                component="備份腳本",
                success=True,
                message="所有備份腳本都存在且可執行",
                details={"scripts": backup_scripts},
            )

        except Exception as e:
            return ValidationResult(
                component="備份腳本",
                success=False,
                message=f"驗證失敗: {str(e)}",
            )

    def validate_backup_dependencies(self) -> ValidationResult:
        """驗證備份所需的系統依賴"""
        try:
            required_commands = [
                ("pg_dump", "PostgreSQL 備份工具"),
                ("psql", "PostgreSQL 客戶端"),
                ("tar", "檔案歸檔工具"),
                ("gzip", "壓縮工具"),
                ("docker", "容器管理工具"),
            ]

            missing_deps = []
            available_deps = []

            for cmd, description in required_commands:
                try:
                    result = subprocess.run(
                        [cmd, "--version"],
                        capture_output=True,
                        check=True,
                        timeout=10,
                    )
                    available_deps.append((cmd, description))
                except (
                    subprocess.CalledProcessError,
                    FileNotFoundError,
                    subprocess.TimeoutExpired,
                ):
                    missing_deps.append((cmd, description))

            if missing_deps:
                return ValidationResult(
                    component="系統依賴",
                    success=False,
                    message=f"缺少必要工具: {', '.join([cmd for cmd, _ in missing_deps])}",
                    details={
                        "missing": [
                            {"command": cmd, "description": desc} for cmd, desc in missing_deps
                        ]
                    },
                )

            return ValidationResult(
                component="系統依賴",
                success=True,
                message="所有必要的系統工具都可用",
                details={
                    "available": [
                        {"command": cmd, "description": desc} for cmd, desc in available_deps
                    ]
                },
            )

        except Exception as e:
            return ValidationResult(
                component="系統依賴",
                success=False,
                message=f"驗證失敗: {str(e)}",
            )

    def validate_backup_configuration(self) -> ValidationResult:
        """驗證備份配置文件"""
        try:
            config_files = [
                "config/backup-config.json",
                "config/disaster-recovery-config.json",
                "scripts/backup/config.yaml",
            ]

            validation_issues = []
            valid_configs = []

            for config_path in config_files:
                full_path = self.project_root / config_path
                if not full_path.exists():
                    validation_issues.append(f"配置文件不存在: {config_path}")
                    continue

                try:
                    if config_path.endswith(".json"):
                        with open(full_path, "r", encoding="utf-8") as f:
                            json.load(f)
                    elif config_path.endswith(".yaml") or config_path.endswith(".yml"):
                        # 簡單驗證 YAML 文件格式
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if not content.strip():
                                validation_issues.append(f"配置文件為空: {config_path}")
                                continue

                    valid_configs.append(config_path)

                except json.JSONDecodeError as e:
                    validation_issues.append(f"JSON 格式錯誤 {config_path}: {str(e)}")
                except Exception as e:
                    validation_issues.append(f"配置文件讀取失敗 {config_path}: {str(e)}")

            if validation_issues:
                return ValidationResult(
                    component="備份配置",
                    success=False,
                    message=f"配置驗證失敗: {'; '.join(validation_issues)}",
                    details={
                        "issues": validation_issues,
                        "valid_configs": valid_configs,
                    },
                )

            return ValidationResult(
                component="備份配置",
                success=True,
                message="所有備份配置文件格式正確",
                details={"valid_configs": valid_configs},
            )

        except Exception as e:
            return ValidationResult(
                component="備份配置",
                success=False,
                message=f"驗證失敗: {str(e)}",
            )

    def validate_backup_directories(self) -> ValidationResult:
        """驗證備份目錄結構"""
        try:
            required_dirs = ["scripts/backup", "monitoring/backup", "config"]

            missing_dirs = []
            existing_dirs = []

            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if not full_path.exists() or not full_path.is_dir():
                    missing_dirs.append(dir_path)
                else:
                    existing_dirs.append(dir_path)

            # 檢查臨時備份目錄權限
            temp_backup_dirs = ["/tmp/backups", "/var/backups", "/opt/backups"]
            writable_temp_dirs = []

            for temp_dir in temp_backup_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists() and os.access(temp_path, os.W_OK):
                    writable_temp_dirs.append(temp_dir)

            if missing_dirs and not writable_temp_dirs:
                return ValidationResult(
                    component="備份目錄",
                    success=False,
                    message=f"缺少必要目錄: {', '.join(missing_dirs)}，且沒有可寫的臨時備份目錄",
                    details={
                        "missing_dirs": missing_dirs,
                        "temp_dirs_checked": temp_backup_dirs,
                    },
                )

            return ValidationResult(
                component="備份目錄",
                success=True,
                message="備份目錄結構正確",
                details={
                    "existing_dirs": existing_dirs,
                    "missing_dirs": missing_dirs,
                    "writable_temp_dirs": writable_temp_dirs,
                },
            )

        except Exception as e:
            return ValidationResult(
                component="備份目錄",
                success=False,
                message=f"驗證失敗: {str(e)}",
            )

    def validate_docker_compose_backup_config(self) -> ValidationResult:
        """驗證 Docker Compose 中的備份相關配置"""
        try:
            docker_compose_files = [
                "docker-compose.yml",
                "docker/docker-compose.prod.yml",
            ]

            backup_volume_configs = []
            missing_configs = []

            for compose_file in docker_compose_files:
                full_path = self.project_root / compose_file
                if not full_path.exists():
                    continue

                content = full_path.read_text(encoding="utf-8")

                # 檢查是否有備份相關的卷配置
                backup_indicators = [
                    "postgres_data:",
                    "redis_data:",
                    "minio_data:",
                    "backup:",
                    "/var/backups",
                    "/opt/backups",
                ]

                found_configs = []
                for indicator in backup_indicators:
                    if indicator in content:
                        found_configs.append(indicator)

                if found_configs:
                    backup_volume_configs.append({"file": compose_file, "configs": found_configs})
                else:
                    missing_configs.append(compose_file)

            if not backup_volume_configs:
                return ValidationResult(
                    component="Docker 備份配置",
                    success=False,
                    message="Docker Compose 文件中缺少備份相關配置",
                )

            return ValidationResult(
                component="Docker 備份配置",
                success=True,
                message="Docker Compose 備份配置正確",
                details={"backup_configs": backup_volume_configs},
            )

        except Exception as e:
            return ValidationResult(
                component="Docker 備份配置",
                success=False,
                message=f"驗證失敗: {str(e)}",
            )

    def validate_environment_variables(self) -> ValidationResult:
        """驗證備份相關的環境變數"""
        try:
            backup_env_vars = [
                "BACKUP_ENABLED",
                "BACKUP_SCHEDULE",
                "BACKUP_RETENTION_DAYS",
                "BACKUP_S3_BUCKET",
                "DATABASE_URL",
                "REDIS_URL",
                "S3_ACCESS_KEY_ID",
                "S3_SECRET_ACCESS_KEY",
            ]

            missing_vars = []
            configured_vars = []

            for var_name in backup_env_vars:
                if os.getenv(var_name):
                    configured_vars.append(var_name)
                else:
                    missing_vars.append(var_name)

            # 檢查 .env.example 文件中是否包含這些變數
            env_example_files = [
                ".env.example",
                "src/.env.example",
            ]

            documented_vars = []
            for env_file in env_example_files:
                env_path = (
                    self.project_root / env_file
                    if not env_file.startswith("src")
                    else self.project_root.parent / env_file
                )
                if env_path.exists():
                    content = env_path.read_text(encoding="utf-8")
                    for var_name in backup_env_vars:
                        if var_name in content:
                            documented_vars.append(var_name)

            undocumented_vars = [var for var in backup_env_vars if var not in documented_vars]

            success = len(missing_vars) <= len(backup_env_vars) * 0.5  # 允許最多 50% 的變數未設置

            return ValidationResult(
                component="環境變數",
                success=success,
                message=f"備份環境變數配置: {len(configured_vars)}/{len(backup_env_vars)} 已配置",
                details={
                    "configured": configured_vars,
                    "missing": missing_vars,
                    "documented": documented_vars,
                    "undocumented": undocumented_vars,
                },
            )

        except Exception as e:
            return ValidationResult(
                component="環境變數",
                success=False,
                message=f"驗證失敗: {str(e)}",
            )

    def run_validation(self) -> Dict:
        """執行所有驗證"""
        logger.info("開始備份配置驗證")

        validators = [
            self.validate_backup_scripts,
            self.validate_backup_dependencies,
            self.validate_backup_configuration,
            self.validate_backup_directories,
            self.validate_docker_compose_backup_config,
            self.validate_environment_variables,
        ]

        self.results = []
        for validator in validators:
            try:
                result = validator()
                self.results.append(result)

                status = "✅" if result.success else "❌"
                logger.info(f"{status} {result.component}: {result.message}")

            except Exception as e:
                error_result = ValidationResult(
                    component=validator.__name__,
                    success=False,
                    message=f"驗證器執行失敗: {str(e)}",
                )
                self.results.append(error_result)
                logger.error(f"❌ {error_result.component}: {error_result.message}")

        # 生成總結報告
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_validations": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": ((passed_tests / total_tests) * 100 if total_tests > 0 else 0),
            },
            "results": [
                {
                    "component": r.component,
                    "success": r.success,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }

        logger.info(
            f"驗證完成: {passed_tests}/{total_tests} 通過 ({report['summary']['success_rate']:.1f}%)"
        )
        return report

    def generate_report(self, report: Dict) -> str:
        """生成人類可讀的驗證報告"""
        report["summary"]

        report_text = """
=================================================
備份配置驗證報告
=================================================
總驗證項: {summary["total_validations"]}
通過項目: {summary["passed"]}
失敗項目: {summary["failed"]}
成功率: {summary["success_rate"]:.1f}%

詳細結果:
-------------------------------------------------
"""

        for result in report["results"]:
            "✅ 通過" if result["success"] else "❌ 失敗"
            report_text += """
{status} {result["component"]}
   訊息: {result["message"]}
"""
            if result["details"]:
                for key, value in result["details"].items():
                    if isinstance(value, list):
                        report_text += f"   {key}: {len(value)} 項\n"
                    else:
                        report_text += f"   {key}: {value}\n"

        report_text += "\n================================================="
        return report_text


def main():
    """主函數"""
    validator = BackupConfigValidator()

    try:
        report = validator.run_validation()

        # 輸出報告
        print(validator.generate_report(report))

        # 保存 JSON 報告
        report_file = Path("backup_config_validation_report.json")
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        logger.info(f"詳細報告已保存到: {report_file}")

        # 返回適當的退出碼
        if report["summary"]["failed"] > 0:
            logger.warning("某些備份配置驗證失敗，建議檢查並修復")
            exit(1)
        else:
            logger.info("所有備份配置驗證通過!")
            exit(0)

    except Exception as e:
        logger.error(f"驗證執行失敗: {e}")
        exit(1)


if __name__ == "__main__":
    main()
