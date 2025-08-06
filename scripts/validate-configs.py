#!/usr/bin/env python3
"""
配置檔案驗證腳本
驗證所有配置檔案的正確性和一致性
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_env_file(file_path: Path) -> Dict[str, Any]:
    """驗證 .env 檔案"""
    errors = []
    warnings = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return {"errors": errors, "warnings": warnings}

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET_KEY",
            "API_GATEWAY_PORT",
            "AUTH_SERVICE_PORT",
        ]

        found_vars = set()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                var_name = line.split("=")[0]
                found_vars.add(var_name)

        # 檢查必需變數
        missing_vars = set(required_vars) - found_vars
        if missing_vars:
            warnings.extend([f"Missing variable: {var}" for var in missing_vars])

        logger.info(f"✅ Environment file validated: {file_path}")

    except Exception as e:
        errors.append(f"Error reading {file_path}: {str(e)}")

    return {"errors": errors, "warnings": warnings}


def validate_yaml_file(file_path: Path) -> Dict[str, Any]:
    """驗證 YAML 檔案"""
    errors = []
    warnings = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return {"errors": errors, "warnings": warnings}

    try:
        with open(file_path, "r") as f:
            yaml.safe_load(f)
        logger.info(f"✅ YAML file validated: {file_path}")
    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error in {file_path}: {str(e)}")
    except Exception as e:
        errors.append(f"Error reading {file_path}: {str(e)}")

    return {"errors": errors, "warnings": warnings}


def validate_json_file(file_path: Path) -> Dict[str, Any]:
    """驗證 JSON 檔案"""
    errors = []
    warnings = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return {"errors": errors, "warnings": warnings}

    try:
        with open(file_path, "r") as f:
            json.load(f)
        logger.info(f"✅ JSON file validated: {file_path}")
    except json.JSONDecodeError as e:
        errors.append(f"JSON syntax error in {file_path}: {str(e)}")
    except Exception as e:
        errors.append(f"Error reading {file_path}: {str(e)}")

    return {"errors": errors, "warnings": warnings}


def validate_docker_compose() -> Dict[str, Any]:
    """驗證 Docker Compose 檔案"""
    errors = []
    warnings = []

    compose_files = [
        "docker-compose.yml",
        "docker-compose.dev.yml",
        "docker-compose.prod.yml",
    ]

    for compose_file in compose_files:
        file_path = Path(compose_file)
        if file_path.exists():
            result = validate_yaml_file(file_path)
            errors.extend(result["errors"])
            warnings.extend(result["warnings"])

    return {"errors": errors, "warnings": warnings}


def validate_pyproject_toml() -> Dict[str, Any]:
    """驗證 pyproject.toml"""
    errors = []
    warnings = []

    file_path = Path("pyproject.toml")
    if not file_path.exists():
        errors.append("pyproject.toml not found")
        return {"errors": errors, "warnings": warnings}

    try:
        import tomli

        with open(file_path, "rb") as f:
            tomli.load(f)
        logger.info("✅ pyproject.toml validated")
    except ImportError:
        try:
            import tomllib

            with open(file_path, "rb") as f:
                tomllib.load(f)
            logger.info("✅ pyproject.toml validated")
        except ImportError:
            warnings.append("Cannot validate pyproject.toml: tomli/tomllib not available")
    except Exception as e:
        errors.append(f"Error in pyproject.toml: {str(e)}")

    return {"errors": errors, "warnings": warnings}


def main():
    """主要驗證流程"""
    project_root = Path.cwd()
    os.chdir(project_root)

    logger.info("🔍 Starting configuration validation...")

    all_errors = []
    all_warnings = []

    # 驗證環境配置檔案
    env_files = [
        Path("config/environments/development.env"),
        Path("config/environments/testing.env"),
        Path("config/environments/production.env"),
        Path("config/environments/production-advanced.env"),
    ]

    for env_file in env_files:
        result = validate_env_file(env_file)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])

    # 驗證 YAML 檔案
    yaml_files = [
        Path(".pre-commit-config.yaml"),
        Path("infra/monitoring/prometheus.yml"),
        Path("infra/kubernetes/api-gateway.yaml"),
    ]

    for yaml_file in yaml_files:
        if yaml_file.exists():
            result = validate_yaml_file(yaml_file)
            all_errors.extend(result["errors"])
            all_warnings.extend(result["warnings"])

    # 驗證 JSON 檔案
    json_files = [
        Path("package.json"),
        Path("src/frontend/package.json"),
        Path(".claude/settings.local.json"),
    ]

    for json_file in json_files:
        if json_file.exists():
            result = validate_json_file(json_file)
            all_errors.extend(result["errors"])
            all_warnings.extend(result["warnings"])

    # 驗證 Docker Compose
    result = validate_docker_compose()
    all_errors.extend(result["errors"])
    all_warnings.extend(result["warnings"])

    # 驗證 pyproject.toml
    result = validate_pyproject_toml()
    all_errors.extend(result["errors"])
    all_warnings.extend(result["warnings"])

    # 報告結果
    logger.info("\n" + "=" * 50)
    logger.info("📊 VALIDATION SUMMARY")
    logger.info("=" * 50)

    if all_errors:
        logger.error(f"❌ {len(all_errors)} ERRORS found:")
        for error in all_errors:
            logger.error(f"  • {error}")

    if all_warnings:
        logger.warning(f"⚠️  {len(all_warnings)} WARNINGS found:")
        for warning in all_warnings:
            logger.warning(f"  • {warning}")

    if not all_errors and not all_warnings:
        logger.info("✅ All configurations are valid!")
    elif not all_errors:
        logger.info("✅ No critical errors found")

    logger.info("=" * 50)

    # 返回適當的退出碼
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
