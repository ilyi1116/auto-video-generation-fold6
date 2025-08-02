#!/usr/bin/env python3
"""
覆蓋率檢查腳本
"""
import subprocess
import sys

def check_coverage():
    """檢查測試覆蓋率"""
    print("Checking test coverage...")

    result = subprocess.run([
        'coverage',
        'report',
        '--show-missing'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Coverage report generated!")
        print(result.stdout)
        return True
    else:
        print("❌ Coverage check failed:")
        print(result.stderr)
        return False

if __name__ == "__main__":
    success = check_coverage()
    sys.exit(0 if success else 1) 