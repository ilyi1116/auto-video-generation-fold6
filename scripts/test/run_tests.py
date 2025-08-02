#!/usr/bin/env python3
"""
測試執行腳本
"""
import subprocess
import sys
import os

def run_tests():
    """執行所有測試"""
    print("Running tests...")

    # 執行 Python 測試
    result = subprocess.run([
        'pytest',
        'tests/',
        '-v',
        '--cov=backend',
        '--cov-report=html'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 