#!/usr/bin/env python3
"""
代碼檢查腳本
"""
import subprocess
import sys

def check_code():
    """檢查代碼質量"""
    print("Checking code quality...")

    # 使用 flake8 檢查代碼風格
    result = subprocess.run([
        'flake8',
        'backend/',
        '--exclude=venv/',
        '--max-line-length=88'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Code quality check passed!")
        return True
    else:
        print("❌ Code quality issues found:")
        print(result.stdout)
        return False

if __name__ == "__main__":
    success = check_code()
    sys.exit(0 if success else 1) 