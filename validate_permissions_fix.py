#!/usr/bin/env python3
"""
驗證 GitHub Actions 權限問題修復腳本
確認所有安全掃描動作都有正確的權限配置
"""

from pathlib import Path

import yaml


def check_permissions_config(file_path):
    """檢查權限配置"""
    try:
        with open(file_path, "r") as f:
            content = yaml.safe_load(f)

        issues = []

        # 檢查是否有全域權限配置
        if "permissions" not in content:
            issues.append("缺少全域權限配置")
        else:
            permissions = content["permissions"]
            if "security-events" not in permissions or permissions["security-events"] != "write":
                issues.append("缺少 security-events: write 權限")
            if "actions" not in permissions or permissions["actions"] != "read":
                issues.append("缺少 actions: read 權限")
            if "contents" not in permissions or permissions["contents"] != "read":
                issues.append("缺少 contents: read 權限")

        return issues
    except Exception as e:
        return [f"讀取檔案時發生錯誤：{e}"]


def check_security_actions(file_path):
    """檢查安全相關動作"""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        security_actions = []

        # 檢查是否使用了安全相關的動作
        if "github/codeql-action/upload-sarif" in content:
            security_actions.append("github/codeql-action/upload-sarif")

        if "snyk/actions/python" in content:
            security_actions.append("snyk/actions/python")

        if "aquasecurity/trivy-action" in content:
            security_actions.append("aquasecurity/trivy-action")

        if "gitleaks/gitleaks-action" in content:
            security_actions.append("gitleaks/gitleaks-action")

        return security_actions
    except Exception as e:
        return [f"讀取檔案時發生錯誤：{e}"]


def main():
    """主函數"""
    print("🚀 驗證 GitHub Actions 權限問題修復...")
    print("=" * 60)

    workflows_dir = Path(".github/workflows")
    all_good = True

    # 檢查所有工作流程檔案
    for workflow_file in workflows_dir.glob("*.yml"):
        print(f"\n📋 檢查工作流程：{workflow_file.name}")

        # 檢查 YAML 語法
        try:
            with open(workflow_file, "r") as f:
                yaml.safe_load(f)
            print(f"✅ YAML 語法正確")
        except Exception as e:
            print(f"❌ YAML 語法錯誤：{e}")
            all_good = False

        # 檢查權限配置
        permission_issues = check_permissions_config(workflow_file)
        if permission_issues:
            print(f"❌ 權限配置問題：")
            for issue in permission_issues:
                print(f"  - {issue}")
            all_good = False
        else:
            print(f"✅ 權限配置正確")

        # 檢查安全動作
        security_actions = check_security_actions(workflow_file)
        if security_actions:
            print(f"✅ 發現安全動作：{', '.join(security_actions)}")
        else:
            print(f"ℹ️  沒有安全相關動作")

    # 檢查 auto_generate_video_fold6 目錄下的工作流程
    alt_workflows_dir = Path("auto_generate_video_fold6/.github/workflows")
    if alt_workflows_dir.exists():
        print(f"\n📋 檢查額外工作流程目錄...")
        for workflow_file in alt_workflows_dir.glob("*.yml"):
            print(f"\n📋 檢查工作流程：{workflow_file.name}")

            # 檢查 YAML 語法
            try:
                with open(workflow_file, "r") as f:
                    yaml.safe_load(f)
                print(f"✅ YAML 語法正確")
            except Exception as e:
                print(f"❌ YAML 語法錯誤：{e}")
                all_good = False

            # 檢查權限配置
            permission_issues = check_permissions_config(workflow_file)
            if permission_issues:
                print(f"❌ 權限配置問題：")
                for issue in permission_issues:
                    print(f"  - {issue}")
                all_good = False
            else:
                print(f"✅ 權限配置正確")

            # 檢查安全動作
            security_actions = check_security_actions(workflow_file)
            if security_actions:
                print(f"✅ 發現安全動作：{', '.join(security_actions)}")
            else:
                print(f"ℹ️  沒有安全相關動作")

    print("\n" + "=" * 60)

    if all_good:
        print("🎉 所有檢查都通過！GitHub Actions 權限問題修復成功！")
        print("\n📋 修復摘要：")
        print("✅ 添加了 security-events: write 權限")
        print("✅ 添加了 actions: read 權限")
        print("✅ 添加了 contents: read 權限")
        print("✅ 確認所有安全掃描動作都有正確權限")
        print("\n🚀 現在可以安全提交到 GitHub！")
        return 0
    else:
        print("❌ 仍有問題需要修復")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
