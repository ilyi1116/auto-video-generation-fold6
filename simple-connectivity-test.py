#!/usr/bin/env python3
"""
簡化連通性測試工具 - 不依賴外部套件
"""

import socket
import time
import subprocess
import sys
from datetime import datetime

def test_tcp_connection(host, port, timeout=5):
    """測試 TCP 連接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((host, port))
        response_time = (time.time() - start_time) * 1000
        sock.close()
        return result == 0, response_time
    except Exception as e:
        return False, 0

def test_command(command, timeout=10):
    """測試命令執行"""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚀 開始簡化連通性測試")
    print(f"測試時間: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 測試目標
    tests = [
        # 基礎設施
        ("PostgreSQL", "localhost", 5432),
        ("Redis", "localhost", 6379),
        ("MinIO", "localhost", 9000),
        
        # 應用服務
        ("API Gateway", "localhost", 8000),
        ("Auth Service", "localhost", 8001),
        ("Video Service", "localhost", 8004),
        ("AI Service", "localhost", 8005),
        ("Social Service", "localhost", 8006),
        ("Trend Service", "localhost", 8007),
        ("Scheduler Service", "localhost", 8008),
        ("Storage Service", "localhost", 8009),
    ]
    
    results = []
    
    for name, host, port in tests:
        print(f"測試 {name} ({host}:{port})...", end=" ")
        
        success, response_time = test_tcp_connection(host, port)
        
        if success:
            print(f"✅ 連接成功 ({response_time:.1f}ms)")
            results.append((name, True, response_time))
        else:
            print(f"❌ 連接失敗")
            results.append((name, False, 0))
    
    print("\n" + "=" * 60)
    
    # 額外測試：檢查關鍵命令
    print("檢查關鍵命令可用性:")
    commands = [
        ("Docker", ["docker", "--version"]),
        ("Docker Compose", ["docker-compose", "--version"]),
        ("PostgreSQL Client", ["pg_isready", "--help"]),
        ("Redis Client", ["redis-cli", "--version"]),
        ("Node.js", ["node", "--version"]),
        ("Python", ["python", "--version"]),
    ]
    
    for name, cmd in commands:
        print(f"檢查 {name}...", end=" ")
        success, stdout, stderr = test_command(cmd, timeout=5)
        
        if success:
            version = stdout.strip().split('\n')[0] if stdout else "已安裝"
            print(f"✅ {version}")
        else:
            print(f"❌ 不可用")
    
    print("\n" + "=" * 60)
    
    # 總結
    total_tests = len(results)
    passed_tests = sum(1 for _, success, _ in results if success)
    
    print(f"連通性測試結果:")
    print(f"  總測試數: {total_tests}")
    print(f"  成功連接: {passed_tests}")
    print(f"  失敗連接: {total_tests - passed_tests}")
    print(f"  成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == 0:
        print("\n⚠️  所有服務連接失敗，請檢查:")
        print("  1. 服務是否已啟動")
        print("  2. 端口是否正確配置")
        print("  3. 防火墻設置")
        return 1
    elif passed_tests < total_tests:
        print(f"\n⚠️  {total_tests - passed_tests} 個服務連接失敗")
        print("部分服務可能未啟動或配置有誤")
        return 1
    else:
        print("\n🎉 所有連接測試通過!")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n用戶中斷測試")
        sys.exit(130)
    except Exception as e:
        print(f"\n測試異常: {str(e)}")
        sys.exit(1)