#!/bin/bash

# Auto Video Generation System - 系統狀態檢查腳本
# 檢查所有服務的運行狀態和健康狀況

echo "📊 Auto Video Generation System Status Check"
echo "=" * 60

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 檢查服務狀態
check_service() {
    local url=$1
    local name=$2
    local port=$3
    
    # 檢查端口是否開放
    if lsof -i :$port > /dev/null 2>&1; then
        port_status="✅ 開放"
        
        # 檢查HTTP響應
        if curl -s -m 5 "$url" > /dev/null 2>&1; then
            http_status="✅ 響應正常"
            
            # 獲取詳細健康信息
            if [[ $url == *"/health" ]]; then
                health_info=$(curl -s -m 5 "$url" 2>/dev/null)
                if [ $? -eq 0 ] && [ -n "$health_info" ]; then
                    service_status="🟢 健康"
                else
                    service_status="🟡 部分功能"
                fi
            else
                service_status="🟢 運行中"
            fi
        else
            http_status="❌ 無響應"
            service_status="🔴 異常"
        fi
    else
        port_status="❌ 關閉"
        http_status="❌ 無響應" 
        service_status="🔴 停止"
    fi
    
    printf "%-15s %-12s %-15s %-12s %s\n" "$name" "$service_status" "$port_status" "$http_status" "$url"
    
    # 如果服務正常且有健康信息，顯示詳細信息
    if [[ $service_status == "🟢"* ]] && [[ $url == *"/health" ]] && [ -n "$health_info" ]; then
        echo "    詳細信息: $health_info" | head -1
        echo ""
    fi
}

# 檢查進程
check_processes() {
    echo ""
    echo -e "${CYAN}🔍 進程狀態:${NC}"
    echo "----------------------------------------"
    
    # API Gateway
    api_pids=$(pgrep -f "api_gateway_simple.py")
    if [ -n "$api_pids" ]; then
        echo "API Gateway: ✅ 運行中 (PID: $api_pids)"
    else
        echo "API Gateway: ❌ 未運行"
    fi
    
    # AI Service
    ai_pids=$(pgrep -f "main_simple.py")
    if [ -n "$ai_pids" ]; then
        echo "AI Service:  ✅ 運行中 (PID: $ai_pids)"
    else
        echo "AI Service:  ❌ 未運行"
    fi
    
    # Frontend
    frontend_pids=$(pgrep -f "npm run dev")
    if [ -n "$frontend_pids" ]; then
        echo "Frontend:    ✅ 運行中 (PID: $frontend_pids)"
    else
        echo "Frontend:    ❌ 未運行"
    fi
}

# 檢查資源使用
check_resources() {
    echo ""
    echo -e "${CYAN}💻 資源使用情況:${NC}"
    echo "----------------------------------------"
    
    # CPU和內存
    if command -v top >/dev/null 2>&1; then
        echo "系統負載:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            top -l 1 -s 0 | grep "CPU usage" | head -1
            top -l 1 -s 0 | grep "PhysMem" | head -1
        else
            # Linux
            top -bn1 | grep "Cpu(s)" | head -1
            top -bn1 | grep "MiB Mem" | head -1
        fi
    fi
    
    # 磁盤空間
    echo ""
    echo "磁盘使用:"
    df -h . | tail -1
    
    # 檢查上傳目錄大小
    if [ -d "uploads/dev" ]; then
        upload_size=$(du -sh uploads/dev 2>/dev/null | cut -f1)
        echo "上傳目錄大小: $upload_size"
    fi
}

# 檢查環境配置
check_environment() {
    echo ""
    echo -e "${CYAN}⚙️  環境配置:${NC}"
    echo "----------------------------------------"
    
    # 檢查環境文件
    if [ -f ".env.local" ]; then
        echo "環境配置: ✅ .env.local 存在"
        
        # 檢查API Keys（不顯示實際值）
        source .env.local 2>/dev/null
        
        echo "API Keys 狀態:"
        [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key-here" ] && echo "  OpenAI:   ✅ 已配置" || echo "  OpenAI:   ❌ 未配置"
        [ -n "$DEEPSEEK_API_KEY" ] && [ "$DEEPSEEK_API_KEY" != "your-deepseek-api-key-here" ] && echo "  DeepSeek: ✅ 已配置" || echo "  DeepSeek: ❌ 未配置"
        [ -n "$GEMINI_API_KEY" ] && [ "$GEMINI_API_KEY" != "your-gemini-api-key-here" ] && echo "  Gemini:   ✅ 已配置" || echo "  Gemini:   ❌ 未配置"
        
        echo "數據庫: ${DATABASE_URL:-sqlite:///./auto_video_dev.db}"
        echo "環境: ${ENVIRONMENT:-development}"
        
    else
        echo "環境配置: ❌ .env.local 不存在"
    fi
    
    # 檢查必要目錄
    echo ""
    echo "目錄結構:"
    [ -d "src/services/api-gateway" ] && echo "  API Gateway: ✅" || echo "  API Gateway: ❌"
    [ -d "src/services/ai-service" ] && echo "  AI Service:  ✅" || echo "  AI Service:  ❌"
    [ -d "src/frontend" ] && echo "  Frontend:    ✅" || echo "  Frontend:    ❌"
    [ -d "uploads/dev" ] && echo "  Uploads:     ✅" || echo "  Uploads:     ❌"
    [ -d "logs" ] && echo "  Logs:        ✅" || echo "  Logs:        ❌"
}

# 檢查日誌文件
check_logs() {
    echo ""
    echo -e "${CYAN}📋 最近日誌 (最後10行):${NC}"
    echo "----------------------------------------"
    
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            echo ""
            echo "📄 $(basename "$log_file"):"
            tail -5 "$log_file" | sed 's/^/    /'
        fi
    done
}

# 執行快速連通性測試
test_connectivity() {
    echo ""
    echo -e "${CYAN}🌐 連通性測試:${NC}"
    echo "----------------------------------------"
    
    # 測試API端點
    echo "正在測試API端點..."
    
    # 測試註冊
    test_email="status-test-$(date +%s)@example.com"
    register_result=$(curl -s -m 10 -X POST "http://localhost:8000/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$test_email\",\"password\":\"test123\",\"first_name\":\"Status\",\"last_name\":\"Test\"}" 2>/dev/null)
    
    if [[ $register_result == *"success"* ]]; then
        echo "  用戶註冊: ✅ 正常"
        
        # 提取token進行進一步測試
        token=$(echo "$register_result" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$token" ]; then
            # 測試AI服務
            script_result=$(curl -s -m 10 -X POST "http://localhost:8005/api/v1/generate/script" \
                -H "Content-Type: application/json" \
                -d '{"topic":"測試主題","platform":"youtube","style":"educational","duration":30}' 2>/dev/null)
            
            if [[ $script_result == *"success"* ]]; then
                echo "  AI腳本生成: ✅ 正常"
            else
                echo "  AI腳本生成: ❌ 異常"
            fi
            
            # 測試影片創建
            video_result=$(curl -s -m 10 -X POST "http://localhost:8000/api/v1/videos" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d '{"title":"狀態測試影片","description":"系統狀態檢查","topic":"測試","style":"modern","duration":15,"platform":"tiktok"}' 2>/dev/null)
            
            if [[ $video_result == *"success"* ]]; then
                echo "  影片創建: ✅ 正常"
            else
                echo "  影片創建: ❌ 異常"
            fi
        fi
    else
        echo "  用戶註冊: ❌ 異常"
    fi
}

# 主函數
main() {
    echo -e "${BLUE}服務名稱      狀態        端口狀態      HTTP狀態    URL${NC}"
    echo "================================================================="
    
    # 檢查各服務狀態
    check_service "http://localhost:8000/health" "API Gateway" "8000"
    check_service "http://localhost:8005/health" "AI Service" "8005"
    check_service "http://localhost:5173" "Frontend" "5173"
    
    # 檢查進程
    check_processes
    
    # 檢查資源使用
    check_resources
    
    # 檢查環境配置
    check_environment
    
    # 檢查日誌（如果存在）
    if [ -d "logs" ] && [ "$(ls -A logs/)" ]; then
        check_logs
    fi
    
    # 如果所有基礎服務都在運行，進行連通性測試
    if lsof -i :8000 > /dev/null 2>&1 && lsof -i :8005 > /dev/null 2>&1; then
        test_connectivity
    else
        echo ""
        echo -e "${YELLOW}⚠️  部分服務未運行，跳過連通性測試${NC}"
    fi
    
    echo ""
    echo "================================================================="
    
    # 總結狀態
    services_running=0
    [ $(lsof -i :8000 >/dev/null 2>&1; echo $?) -eq 0 ] && ((services_running++))
    [ $(lsof -i :8005 >/dev/null 2>&1; echo $?) -eq 0 ] && ((services_running++))
    [ $(lsof -i :5173 >/dev/null 2>&1; echo $?) -eq 0 ] && ((services_running++))
    
    echo -e "📈 系統狀態總結: ${services_running}/3 服務運行中"
    
    if [ $services_running -eq 3 ]; then
        echo -e "${GREEN}🎉 系統完全正常運行！${NC}"
        echo ""
        echo "🔗 快速鏈接:"
        echo "   • 前端應用: http://localhost:5173"  
        echo "   • API 文檔: http://localhost:8000/docs"
        echo "   • 系統健康: http://localhost:8000/health"
    elif [ $services_running -gt 0 ]; then
        echo -e "${YELLOW}⚠️  系統部分運行，部分服務可能異常${NC}"
        echo ""
        echo "🔧 建議操作:"
        echo "   • 檢查未運行的服務日誌"
        echo "   • 重啟系統: ./stop_system.sh && ./start_system.sh"
    else
        echo -e "${RED}🔴 系統完全停止${NC}"
        echo ""
        echo "🚀 啟動系統: ./start_system.sh"
    fi
    
    echo ""
    echo "📋 其他管理指令:"
    echo "   • 啟動系統: ./start_system.sh"
    echo "   • 停止系統: ./stop_system.sh"  
    echo "   • 查看日誌: tail -f logs/*.log"
    echo "   • 運行測試: python3 simple_video_test.py"
}

# 執行主函數
main "$@"