#!/bin/bash

# 排程器啟動腳本

echo "啟動 Auto Video Generation 排程器..."

# 設置環境變數
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# 創建必要目錄
mkdir -p /app/logs /app/data

# 啟動 cron 服務
service cron start

# 健康檢查 HTTP 服務器 (簡單版)
cat > /app/health_server.py << 'EOF'
#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import os
from pathlib import Path

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # 檢查排程器狀態
            health_file = Path('/app/logs/health_check.json')
            if health_file.exists() and health_file.stat().st_mtime > (time.time() - 300):
                status = {"status": "healthy", "service": "scheduler"}
            else:
                status = {"status": "unhealthy", "service": "scheduler"}
            
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8003), HealthHandler)
    server.serve_forever()

if __name__ == '__main__':
    import time
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # 保持主程序運行
    while True:
        time.sleep(60)
EOF

# 在背景啟動健康檢查服務器
python /app/health_server.py &

echo "排程器已啟動，健康檢查端口: 8003"

# 啟動主排程器
exec python /app/scheduler.py