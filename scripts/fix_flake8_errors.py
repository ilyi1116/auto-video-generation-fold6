#!/usr/bin/env python3
"""
批量修復常見的 flake8 錯誤和語法問題
"""
import os
import subprocess
from pathlib import Path


def run_black_formatting():
    """運行 Black 格式化"""
    print("運行 Black 代碼格式化...")
    try:
        subprocess.run(
            ["black", ".", "--line-length=100"], capture_output=True, text=True, check=True
        )
        print("✅ Black 格式化完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Black 格式化失敗: {e}")
        return False
    except FileNotFoundError:
        print("❌ Black 未安裝")
        return False


def run_isort():
    """運行 isort 導入排序"""
    print("運行 isort 導入排序...")
    try:
        subprocess.run(
            ["isort", ".", "--profile=black"], capture_output=True, text=True, check=True
        )
        print("✅ isort 排序完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ isort 排序失敗: {e}")
        return False
    except FileNotFoundError:
        print("❌ isort 未安裝")
        return False


def run_autoflake():
    """運行 autoflake 移除未使用的導入"""
    print("運行 autoflake 清理未使用導入...")
    try:
        subprocess.run(
            [
                "autoflake",
                "--remove-all-unused-imports",
                "--remove-unused-variables",
                "--in-place",
                "--recursive",
                ".",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ autoflake 清理完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ autoflake 清理失敗: {e}")
        return False
    except FileNotFoundError:
        print("❌ autoflake 未安裝")
        return False


def install_formatting_tools():
    """安裝格式化工具"""
    tools = ["black", "isort", "autoflake"]
    for tool in tools:
        try:
            subprocess.run(["pip", "install", tool], capture_output=True, text=True, check=True)
            print(f"✅ {tool} 已安裝")
        except subprocess.CalledProcessError:
            print(f"❌ {tool} 安裝失敗")


def main():
    """主函數"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("開始修復代碼質量問題...")

    # 嘗試安裝工具
    print("檢查並安裝格式化工具...")
    install_formatting_tools()

    # 運行格式化工具
    success_count = 0

    if run_black_formatting():
        success_count += 1

    if run_isort():
        success_count += 1

    if run_autoflake():
        success_count += 1

    print(f"\n代碼質量修復完成: {success_count}/3 個工具成功運行")

    # 運行基本語法檢查
    print("\n檢查語法錯誤...")
    problematic_files = []

    # 檢查核心文件
    core_files = [
        "src/shared/database/models.py",
        "src/shared/services/service_discovery.py",
        "tests/test_system_integration.py",
    ]

    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                subprocess.run(
                    ["python", "-m", "py_compile", str(full_path)], check=True, capture_output=True
                )
                print(f"✅ {file_path} - 語法正確")
            except subprocess.CalledProcessError:
                problematic_files.append(file_path)
                print(f"❌ {file_path} - 語法錯誤")

    if problematic_files:
        print(f"\n需要手動修復的文件: {len(problematic_files)}")
        for file_path in problematic_files:
            print(f"  {file_path}")
    else:
        print("\n✅ 核心文件語法檢查通過")


if __name__ == "__main__":
    main()
