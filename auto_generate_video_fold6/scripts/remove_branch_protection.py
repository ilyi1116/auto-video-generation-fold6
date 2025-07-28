#!/usr/bin/env python3
"""
移除 GitHub 分支保護規則的腳本
"""

import requests
import os
import sys
import json


def remove_branch_protection():
    """移除 main 分支的保護規則"""

    # GitHub API 配置
    repo_owner = "ilyi1116"
    repo_name = "auto-video-generation-fold6"
    branch = "main"

    # 從環境變數獲取 GitHub token
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("❌ 請設置 GITHUB_TOKEN 環境變數")
        print("方法：export GITHUB_TOKEN=your_personal_access_token")
        print("獲取 token: https://github.com/settings/tokens")
        return False

    # API 端點
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches/{branch}/protection"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        print(f"🔍 檢查 {branch} 分支保護狀態...")

        # 首先檢查當前保護設定
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            protection_info = response.json()
            print("📋 當前分支保護設定:")
            print(json.dumps(protection_info, indent=2))

            print(f"\n🗑️  移除 {branch} 分支保護...")

            # 刪除分支保護
            delete_response = requests.delete(url, headers=headers)

            if delete_response.status_code == 204:
                print("✅ 分支保護已成功移除！")
                return True
            else:
                print(f"❌ 移除分支保護失敗: {delete_response.status_code}")
                print(f"錯誤訊息: {delete_response.text}")
                return False

        elif response.status_code == 404:
            print("ℹ️  分支沒有設置保護規則")
            return True
        else:
            print(f"❌ 檢查分支保護失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 操作失敗: {e}")
        return False


def show_current_protection():
    """顯示當前保護設定"""
    repo_owner = "ilyi1116"
    repo_name = "auto-video-generation-fold6"
    branch = "main"

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ 需要 GITHUB_TOKEN 環境變數")
        return

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches/{branch}/protection"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("當前分支保護設定:")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 404:
            print("✅ 分支沒有保護規則")
        else:
            print(f"無法獲取保護設定: {response.status_code}")
    except Exception as e:
        print(f"錯誤: {e}")


def main():
    print("🛡️  GitHub 分支保護管理工具")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_current_protection()
        return

    success = remove_branch_protection()

    if success:
        print("\n🎉 操作完成！現在可以直接推送到 main 分支了")
        print("\n💡 建議的後續操作:")
        print("1. git push origin main")
        print("\n⚠️  注意: 移除保護後記得在適當時候重新設置保護規則")
    else:
        print("\n❌ 操作失敗，請檢查:")
        print("1. GITHUB_TOKEN 是否正確設置")
        print("2. Token 是否有足夠權限 (需要 repo 權限)")
        print("3. 倉庫名稱是否正確")
        print("\n💡 或者直接在 GitHub 網頁移除:")
        print("https://github.com/ilyi1116/auto-video-generation-fold6/settings/branches")


if __name__ == "__main__":
    main()
