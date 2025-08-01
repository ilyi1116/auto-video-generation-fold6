#!/usr/bin/env python3
"""
E2E 測試運行器
啟動模擬服務並執行測試
"""

import asyncio
import subprocess
import time
import signal
import sys
import os
from concurrent.futures import ThreadPoolExecutor

class E2ETestRunner:
    def __init__(self):
        self.mock_process = None
        
    def start_mock_services(self):
        """啟動模擬服務"""
        print("🎭 啟動模擬服務...")
        self.mock_process = subprocess.Popen([
            sys.executable, "mock_services_e2e.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服務啟動
        time.sleep(5)
        return self.mock_process.poll() is None
    
    def stop_mock_services(self):
        """停止模擬服務"""
        if self.mock_process:
            print("🛑 停止模擬服務...")
            self.mock_process.terminate()
            try:
                self.mock_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.mock_process.kill()
                self.mock_process.wait()
    
    def run_tests(self):
        """運行 E2E 測試"""
        print("🧪 運行 E2E 測試...")
        test_process = subprocess.run([
            sys.executable, "test_e2e_simple.py"
        ], capture_output=True, text=True)
        
        print(test_process.stdout)
        if test_process.stderr:
            print("STDERR:", test_process.stderr)
            
        return test_process.returncode == 0
    
    def run(self):
        """執行完整的 E2E 測試流程"""
        try:
            # 啟動模擬服務
            if not self.start_mock_services():
                print("❌ 模擬服務啟動失敗")
                return False
            
            print("✅ 模擬服務已啟動")
            
            # 運行測試
            success = self.run_tests()
            
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷測試")
            return False
        except Exception as e:
            print(f"❌ 測試執行異常: {e}")
            return False
        finally:
            # 清理資源
            self.stop_mock_services()

def main():
    """主函數"""
    print("🚀 創業者模式 E2E 測試運行器")
    print("=" * 40)
    
    runner = E2ETestRunner()
    
    # 設定信號處理
    def signal_handler(signum, frame):
        print("\n🛑 收到終止信號，清理資源...")
        runner.stop_mock_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 執行測試
    success = runner.run()
    
    if success:
        print("\n🎉 E2E 測試完成並通過！")
        print("🎯 TDD Green 階段完成，準備進入 Refactor 階段")
        return 0
    else:
        print("\n💥 E2E 測試失敗")
        print("🔴 需要修復問題後重新運行測試")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)