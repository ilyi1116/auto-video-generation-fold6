#!/usr/bin/env python3
"""
簡單的API Gateway啟動腳本
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設置環境變數
os.environ.setdefault("ENVIRONMENT", "development")

# 直接啟動應用
if __name__ == "__main__":
    import uvicorn
    
    # 直接從檔案載入應用
    app_path = project_root / "src" / "services" / "api-gateway" / "main.py"
    
    # 使用相對導入方式
    uvicorn.run(
        "src.services.api-gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )