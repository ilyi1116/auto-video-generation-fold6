#!/usr/bin/env python3
"""
代碼格式化腳本
"""
import subprocess
import sys

def format_code():
    """格式化代碼"""
    print("Formatting code...")

    # 使用 black 格式化 Python 代碼
    result = subprocess.run([
        'black',
        'backend/',
        '--exclude',
        'venv/'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Code formatted successfully!")
        return True
    else:
        print("❌ Formatting failed:")
        print(result.stderr)
        return False

if __name__ == "__main__":
    success = format_code()
    sys.exit(0 if success else 1) 