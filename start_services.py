#!/usr/bin/env python3
"""
服務啟動腳本
同時啟動所有必要的服務
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

# 專案根目錄
project_root = Path(__file__).parent

def print_banner():
    """打印啟動橫幅"""
    print("="*60)
    print("🚀 AutoVideo - AI 影片生成系統")
    print("="*60)
    print("正在啟動服務...")
    print()

def check_python_version():
    """檢查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 錯誤: 需要 Python 3.8 或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")

def check_dependencies():
    """檢查依賴"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ 核心依賴已安裝")
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("請執行: pip install -r requirements.txt")
        sys.exit(1)

def init_database():
    """初始化資料庫"""
    print("🗄️ 初始化資料庫...")
    try:
        sys.path.insert(0, str(project_root))
        from src.shared.database.init_data import init_database
        init_database()
        print("✅ 資料庫初始化完成")
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        return False
    return True

def start_service(name, script_path, port):
    """啟動單個服務"""
    print(f"🚀 啟動 {name} (port {port})...")
    try:
        # 使用 python -m 運行以確保正確的模組解析
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待一小段時間讓服務啟動
        time.sleep(2)
        
        # 檢查程序是否仍在運行
        if process.poll() is None:
            print(f"✅ {name} 啟動成功 (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {name} 啟動失敗")
            if stderr:
                print(f"錯誤: {stderr}")
            return None
    except Exception as e:
        print(f"❌ {name} 啟動失敗: {e}")
        return None

def main():
    """主函數"""
    print_banner()
    
    # 檢查環境
    check_python_version()
    check_dependencies()
    
    # 初始化資料庫
    if not init_database():
        print("❌ 無法初始化資料庫，停止啟動")
        sys.exit(1)
    
    print("\n🔧 啟動服務...")
    
    # 要啟動的服務列表
    services = [
        ("API Gateway", project_root / "src/services/api-gateway/main.py", 8000),
        ("AI Service", project_root / "src/services/ai-service/main.py", 8005),
        ("Video Processing Service", project_root / "src/services/video-processing-service/main.py", 8006),
    ]
    
    processes = []
    
    for name, script_path, port in services:
        if script_path.exists():
            process = start_service(name, script_path, port)
            if process:
                processes.append((name, process, port))
            else:
                print(f"⚠️ {name} 啟動失敗，繼續啟動其他服務...")
        else:
            print(f"❌ 找不到服務腳本: {script_path}")
    
    if not processes:
        print("❌ 沒有服務成功啟動")
        sys.exit(1)
    
    print(f"\n🎉 成功啟動 {len(processes)} 個服務:")
    for name, process, port in processes:
        print(f"   - {name}: http://localhost:{port}")
    
    print("\n📚 API 文檔:")
    print("   - API Gateway: http://localhost:8000/docs")
    print("   - AI Service: http://localhost:8005/docs")
    print("   - Video Processing: http://localhost:8006/docs")
    
    print("\n🔧 測試系統:")
    print("   - 運行整合測試: python test_integration.py")
    print("   - 啟動前端: cd src/frontend && npm run dev")
    
    print("\n🎯 系統就緒!")
    print("   - 前端地址: http://localhost:5173")
    print("   - 測試帳號: test1@example.com / password123")
    
    print("\n按 Ctrl+C 停止所有服務...")
    
    try:
        # 等待用戶中斷
        while True:
            # 檢查所有程序是否仍在運行
            running_count = 0
            for name, process, port in processes:
                if process.poll() is None:
                    running_count += 1
                else:
                    print(f"⚠️ {name} 已停止運行")
            
            if running_count == 0:
                print("❌ 所有服務都已停止")
                break
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止所有服務...")
        
        # 停止所有程序
        for name, process, port in processes:
            if process.poll() is None:
                print(f"   停止 {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   強制停止 {name}...")
                    process.kill()
        
        print("✅ 所有服務已停止")

if __name__ == "__main__":
    main()