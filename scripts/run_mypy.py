#!/usr/bin/env python3
"""
MyPy 檢查腳本 - 專門處理包含連字號的目錄問題
"""

import subprocess
import sys
from pathlib import Path

def run_mypy_check():
    """運行 mypy 檢查，排除有問題的目錄"""
    
    # 可以檢查的目錄和文件
    checkable_paths = [
        "src/shared/",
        "src/services/common/",
        "src/config/",
        # 可以添加其他沒有連字號的目錄
    ]
    
    # 排除有連字號的服務目錄
    excluded_services = [
        "ai-service", "auth-service", "data-service", "inference-service",
        "api-gateway", "cache-service", "compliance-service", "data-ingestion",
        "graphql-gateway", "music-service", "payment-service", "scheduler-service",
        "social-service", "storage-service", "training-worker", "trend-service",
        "video-service", "voice-enhancement"
    ]
    
    print("🔍 開始 MyPy 型別檢查...")
    print(f"檢查路徑: {', '.join(checkable_paths)}")
    print(f"排除服務: {len(excluded_services)} 個包含連字號的服務目錄")
    print("-" * 60)
    
    # 構建 mypy 命令
    cmd = [
        "mypy",
        "--config-file", "mypy.ini",
        "--show-error-codes",
        "--show-column-numbers"
    ] + checkable_paths
    
    try:
        # 運行 mypy
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 輸出結果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("錯誤輸出:", result.stderr, file=sys.stderr)
        
        # 統計錯誤
        if result.returncode == 0:
            print("✅ MyPy 檢查通過，沒有發現型別錯誤！")
            return True
        else:
            error_lines = result.stdout.split('\n')
            error_count = len([line for line in error_lines if ": error:" in line])
            print(f"❌ 發現 {error_count} 個型別錯誤")
            
            # 按錯誤類型分類
            error_types = {}
            for line in error_lines:
                if ": error:" in line and "[" in line and "]" in line:
                    error_type = line.split("[")[-1].split("]")[0]
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            if error_types:
                print("\n📊 錯誤類型統計:")
                for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {error_type}: {count} 個")
            
            return False
            
    except FileNotFoundError:
        print("❌ 找不到 mypy 命令，請確認已安裝 mypy")
        return False
    except Exception as e:
        print(f"❌ 運行 mypy 時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 Auto Video Generation - MyPy 型別檢查工具")
    print("=" * 60)
    
    # 檢查是否在正確的目錄
    if not Path("src").exists():
        print("❌ 請在專案根目錄運行此腳本")
        sys.exit(1)
    
    # 運行檢查
    success = run_mypy_check()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 型別檢查完成，代碼質量良好！")
        sys.exit(0)
    else:
        print("⚠️  型別檢查發現問題，建議修復後再次檢查")
        sys.exit(1)

if __name__ == "__main__":
    main()