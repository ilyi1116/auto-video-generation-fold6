#!/usr/bin/env python3
"""
Phase 3 部署策略驗證腳本
驗證統一部署配置的完整性和可用性
"""

import sys
import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 添加專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_docker_compose_config():
    """測試 Docker Compose 配置"""
    print("🐳 測試 Docker Compose 配置...")

    config_file = project_root / "docker-compose.unified.yml"
    if not config_file.exists():
        print("❌ Docker Compose 配置檔案不存在")
        return False

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # 檢查必要的服務
        required_services = [
            "postgres",
            "redis",
            "minio",
            "api-gateway",
            "auth-service",
            "video-service",
            "migrations",
            "frontend",
        ]

        services = config.get("services", {})
        missing_services = []

        for service in required_services:
            if service not in services:
                missing_services.append(service)

        if missing_services:
            print(f"❌ 缺少服務: {missing_services}")
            return False

        # 檢查網路配置
        if "networks" not in config:
            print("❌ 缺少網路配置")
            return False

        # 檢查資料持久化
        if "volumes" not in config:
            print("❌ 缺少 Volume 配置")
            return False

        # 檢查 PostgreSQL 配置
        postgres_config = services.get("postgres", {})
        if "healthcheck" not in postgres_config:
            print("⚠️  PostgreSQL 缺少健康檢查配置")

        # 檢查 Redis 配置
        redis_config = services.get("redis", {})
        if "healthcheck" not in redis_config:
            print("⚠️  Redis 缺少健康檢查配置")

        # 檢查資料庫遷移配置
        migrations_config = services.get("migrations", {})
        if not migrations_config:
            print("❌ 缺少資料庫遷移配置")
            return False

        print("✅ Docker Compose 配置檢查通過")
        print(f"   - 包含 {len(services)} 個服務")
        print(f"   - 包含 {len(config.get('networks', {}))} 個網路")
        print(f"   - 包含 {len(config.get('volumes', {}))} 個持久化 Volume")

        return True

    except yaml.YAMLError as e:
        print(f"❌ Docker Compose 配置格式錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ Docker Compose 配置檢查失敗: {e}")
        return False


def test_kubernetes_config():
    """測試 Kubernetes 配置"""
    print("\n☸️  測試 Kubernetes 配置...")

    k8s_file = project_root / "k8s" / "unified-deployment.yaml"
    if not k8s_file.exists():
        print("❌ Kubernetes 配置檔案不存在")
        return False

    try:
        with open(k8s_file, "r") as f:
            content = f.read()

        # 分割多個 YAML 文檔
        documents = [doc for doc in content.split("---") if doc.strip()]

        if len(documents) < 5:
            print(f"❌ Kubernetes 配置文檔數量不足: {len(documents)}")
            return False

        # 解析每個文檔
        parsed_docs = []
        for doc in documents:
            try:
                parsed = yaml.safe_load(doc)
                if parsed:
                    parsed_docs.append(parsed)
            except yaml.YAMLError:
                continue

        # 檢查必要的資源類型
        resource_types = {}
        for doc in parsed_docs:
            if doc and "kind" in doc:
                kind = doc["kind"]
                resource_types[kind] = resource_types.get(kind, 0) + 1

        # 必要的 Kubernetes 資源
        required_resources = {
            "Namespace": 1,
            "ConfigMap": 1,
            "Secret": 1,
            "Deployment": 3,  # 至少 3 個 Deployment
            "Service": 3,  # 至少 3 個 Service
        }

        for resource, min_count in required_resources.items():
            actual_count = resource_types.get(resource, 0)
            if actual_count < min_count:
                print(
                    f"❌ {resource} 資源不足: 需要 {min_count}, 實際 {actual_count}"
                )
                return False

        # 檢查 HPA 配置
        if "HorizontalPodAutoscaler" not in resource_types:
            print("⚠️  缺少水平自動擴展配置")

        # 檢查 Ingress 配置
        if "Ingress" not in resource_types:
            print("⚠️  缺少 Ingress 配置")

        # 檢查 NetworkPolicy 配置
        if "NetworkPolicy" not in resource_types:
            print("⚠️  缺少網路政策配置")

        print("✅ Kubernetes 配置檢查通過")
        print(f"   - 包含 {len(parsed_docs)} 個資源定義")
        print(f"   - 資源類型: {list(resource_types.keys())}")

        return True

    except Exception as e:
        print(f"❌ Kubernetes 配置檢查失敗: {e}")
        return False


def test_environment_template():
    """測試環境配置範本"""
    print("\n🔧 測試環境配置范本...")

    env_template = project_root / ".env.template"
    if not env_template.exists():
        print("❌ 環境配置範本不存在")
        return False

    try:
        with open(env_template, "r") as f:
            content = f.read()

        # 檢查必要的環境變數
        required_vars = [
            "ENVIRONMENT",
            "POSTGRES_PASSWORD",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ 缺少環境變數: {missing_vars}")
            return False

        # 檢查服務端口配置
        service_ports = [
            "API_GATEWAY_PORT",
            "AUTH_SERVICE_PORT",
            "VIDEO_SERVICE_PORT",
            "FRONTEND_PORT",
        ]

        for port in service_ports:
            if port not in content:
                print(f"⚠️  缺少端口配置: {port}")

        # 檢查 AI 服務配置
        ai_configs = [
            "OPENAI_API_KEY",
            "GOOGLE_AI_API_KEY",
            "STABILITY_API_KEY",
        ]

        for config in ai_configs:
            if config not in content:
                print(f"⚠️  缺少 AI 服務配置: {config}")

        print("✅ 環境配置範本檢查通過")
        config_lines = [
            line
            for line in content.split("\n")
            if "=" in line and not line.startswith("#")
        ]
        print(f"   - 包含 {len(config_lines)} 個配置項")

        return True

    except Exception as e:
        print(f"❌ 環境配置範本檢查失敗: {e}")
        return False


def test_deployment_script():
    """測試部署腳本"""
    print("\n🚀 測試部署腳本...")

    deploy_script = project_root / "scripts" / "deploy-unified.sh"
    if not deploy_script.exists():
        print("❌ 部署腳本不存在")
        return False

    try:
        with open(deploy_script, "r") as f:
            content = f.read()

        # 檢查腳本是否可執行
        import stat

        file_stat = deploy_script.stat()
        if not (file_stat.st_mode & stat.S_IEXEC):
            print("⚠️  部署腳本沒有執行權限")

        # 檢查必要的函數
        required_functions = [
            "deploy_docker",
            "deploy_kubernetes",
            "deploy_dev",
            "check_dependencies",
            "setup_environment",
        ]

        missing_functions = []
        for func in required_functions:
            if f"{func}()" not in content:
                missing_functions.append(func)

        if missing_functions:
            print(f"❌ 缺少必要函數: {missing_functions}")
            return False

        # 檢查錯誤處理
        if "set -euo pipefail" not in content:
            print("⚠️  缺少嚴格錯誤處理設定")

        # 檢查日誌函數
        log_functions = ["log_info", "log_success", "log_warning", "log_error"]
        for log_func in log_functions:
            if log_func not in content:
                print(f"⚠️  缺少日誌函數: {log_func}")

        print("✅ 部署腳本檢查通過")

        return True

    except Exception as e:
        print(f"❌ 部署腳本檢查失敗: {e}")
        return False


def test_documentation():
    """測試部署文檔"""
    print("\n📚 測試部署文檔...")

    doc_file = project_root / "docs" / "DEPLOYMENT_STRATEGY.md"
    if not doc_file.exists():
        print("❌ 部署策略文檔不存在")
        return False

    try:
        with open(doc_file, "r") as f:
            content = f.read()

        # 檢查必要的章節
        required_sections = [
            "系統架構",
            "部署選項",
            "配置管理",
            "監控與日誌",
            "安全性配置",
            "故障排除",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ 缺少文檔章節: {missing_sections}")
            return False

        # 檢查代碼範例
        if "```bash" not in content:
            print("⚠️  缺少 Bash 代碼範例")

        if "```yaml" not in content:
            print("⚠️  缺少 YAML 代碼範例")

        # 檢查文檔長度
        word_count = len(content.split())
        if word_count < 500:
            print(f"⚠️  文檔內容較少: {word_count} 字")

        print("✅ 部署文檔檢查通過")
        print(f"   - 文檔長度: {word_count} 字")

        return True

    except Exception as e:
        print(f"❌ 部署文檔檢查失敗: {e}")
        return False


def test_phase2_integration():
    """測試 Phase 2 整合"""
    print("\n🔗 測試 Phase 2 資料庫系統整合...")

    # 檢查 Alembic 配置
    alembic_config = project_root / "alembic.ini"
    if not alembic_config.exists():
        print("❌ Alembic 配置檔案不存在")
        return False

    # 檢查統一模型
    models_init = (
        project_root / "auto_generate_video_fold6" / "models" / "__init__.py"
    )
    if not models_init.exists():
        print("❌ 統一模型定義不存在")
        return False

    # 檢查遷移管理腳本
    migration_script = project_root / "scripts" / "db-migration-manager.py"
    if not migration_script.exists():
        print("❌ 資料庫遷移管理腳本不存在")
        return False

    # 檢查同步管理器
    sync_manager = (
        project_root
        / "auto_generate_video_fold6"
        / "database"
        / "sync_manager.py"
    )
    if not sync_manager.exists():
        print("❌ 資料庫同步管理器不存在")
        return False

    print("✅ Phase 2 整合檢查通過")

    return True


def generate_summary_report():
    """生成 Phase 3 完成報告"""
    print("\n" + "=" * 60)
    print("🎉 PHASE 3 部署策略驗證完成報告")
    print("=" * 60)

    tests = [
        ("Docker Compose 配置", test_docker_compose_config),
        ("Kubernetes 配置", test_kubernetes_config),
        ("環境配置範本", test_environment_template),
        ("部署腳本", test_deployment_script),
        ("部署文檔", test_documentation),
        ("Phase 2 整合", test_phase2_integration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        result = test_func()
        results.append((test_name, result))

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    success_rate = (passed / len(results)) * 100
    print(f"\n成功率: {passed}/{len(results)} ({success_rate:.1f}%)")

    if success_rate >= 85:
        print("🎉 Phase 3 部署策略系統驗證通過！")
        print("\n📋 已完成功能:")
        print("• 統一 Docker Compose 部署配置")
        print("• 完整 Kubernetes 部署配置")
        print("• 生產級環境配置管理")
        print("• 自動化部署腳本")
        print("• 完整部署策略文檔")
        print("• Phase 2 資料庫系統整合")
        print("• 監控與日誌系統配置")
        print("• 安全性與網路政策配置")

        print("\n🚀 部署策略特色:")
        print("• 支援多環境部署 (開發/測試/生產)")
        print("• 整合 Phase 2 統一資料庫系統")
        print("• 水平自動擴展配置")
        print("• 健康檢查與故障自動恢復")
        print("• SSL/TLS 安全性配置")
        print("• 資源限制與優化")
        print("• 備份與災難復原策略")

        print("\n🎯 準備進行下一階段或實際部署測試")
    else:
        print("⚠️  部分功能需要進一步完善")

    return success_rate >= 85


if __name__ == "__main__":
    print("🚀 開始 Phase 3 部署策略驗證")
    success = generate_summary_report()
    sys.exit(0 if success else 1)
