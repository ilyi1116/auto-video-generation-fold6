#!/usr/bin/env python3
"""
Alembic 遷移系統驗證腳本
確保 Alembic 配置正確並可以執行遷移
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """驗證 Alembic 系統設置"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🔍 驗證 Alembic 資料庫遷移系統...")

    # 檢查 Alembic 配置文件
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        print("❌ 找不到 alembic.ini 配置文件")
        return False

    # 檢查遷移目錄
    alembic_dir = project_root / "alembic"
    if not alembic_dir.exists():
        print("❌ 找不到 alembic 遷移目錄")
        return False

    # 檢查版本目錄
    versions_dir = alembic_dir / "versions"
    if not versions_dir.exists():
        print("❌ 找不到 alembic/versions 目錄")
        return False

    # 檢查遷移文件
    migration_files = list(versions_dir.glob("*.py"))
    if not migration_files:
        print("⚠️  沒有找到遷移文件")
    else:
        print(f"✅ 找到 {len(migration_files)} 個遷移文件")

    # 測試 Alembic 命令
    try:
        result = subprocess.run(
            ["alembic", "current"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("✅ Alembic 命令可以正常執行")
            if result.stdout.strip():
                print(f"   當前版本: {result.stdout.strip()}")
            else:
                print("   資料庫未初始化")
        else:
            print(f"⚠️  Alembic 命令執行失敗: {result.stderr}")
    except FileNotFoundError:
        print("❌ 找不到 alembic 命令，請確保已安裝 alembic")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Alembic 命令執行超時")
        return False

    # 檢查環境變數
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("✅ 找到 DATABASE_URL 環境變數")
    else:
        print("⚠️  未設置 DATABASE_URL 環境變數")

    print("\n📋 Alembic 系統驗證完成")
    print("\n🚀 使用方法:")
    print("  # 創建新遷移")
    print('  alembic revision --autogenerate -m "Description"')
    print("  ")
    print("  # 升級資料庫到最新版本")
    print("  alembic upgrade head")
    print("  ")
    print("  # 檢視遷移歷史")
    print("  alembic history")
    print("  ")
    print("  # 檢視當前版本")
    print("  alembic current")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
