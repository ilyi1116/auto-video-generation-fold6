#!/bin/bash
# 前端-後端整合測試腳本
# Frontend-Backend Integration Test Script

set -e

FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8001"

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試計數器
TESTS_PASSED=0
TESTS_FAILED=0

# 測試函數
test_api() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -n "測試 $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" -o /tmp/response.json)
    else
        response=$(curl -s -w "%{http_code}" "$url" -o /tmp/response.json)
    fi
    
    status_code="${response: -3}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (狀態碼: $status_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (預期: $expected_status, 實際: $status_code)"
        echo "回應內容: $(cat /tmp/response.json)"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_frontend_page() {
    local name="$1"
    local url="$2"
    local search_text="$3"
    
    echo -n "測試 $name... "
    
    response=$(curl -s -w "%{http_code}" "$url" -o /tmp/page.html)
    status_code="${response: -3}"
    
    if [ "$status_code" = "200" ] && grep -qi "$search_text" /tmp/page.html; then
        echo -e "${GREEN}✅ PASS${NC} (頁面載入正常)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (狀態碼: $status_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

performance_test() {
    local name="$1"
    local url="$2"
    
    echo -n "性能測試 $name... "
    
    start_time=$(date +%s%3N)
    curl -s "$url" > /dev/null
    end_time=$(date +%s%3N)
    
    response_time=$((end_time - start_time))
    
    if [ "$response_time" -lt 1000 ]; then
        echo -e "${GREEN}✅ PASS${NC} (${response_time}ms - 良好)"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  SLOW${NC} (${response_time}ms - 需優化)"
        ((TESTS_PASSED++))
    fi
}

echo -e "${BLUE}🚀 開始前端-後端整合測試...${NC}\n"
echo "📋 測試配置:"
echo "   前端URL: $FRONTEND_URL"
echo "   後端URL: $BACKEND_URL"
echo ""

# 檢查服務是否運行
echo -e "${BLUE}🔍 檢查服務狀態...${NC}"

if ! curl -s "$FRONTEND_URL" > /dev/null; then
    echo -e "${RED}❌ 前端服務未運行 ($FRONTEND_URL)${NC}"
    echo "請先啟動前端服務: npm run dev"
    exit 1
fi

if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo -e "${RED}❌ 後端服務未運行 ($BACKEND_URL)${NC}"
    echo "請先啟動後端服務: python3 mock_server.py"
    exit 1
fi

echo -e "${GREEN}✅ 所有服務正在運行${NC}\n"

# 測試後端API
echo -e "${BLUE}🔍 測試後端API...${NC}"
test_api "健康檢查" "GET" "$BACKEND_URL/health" "" "200"
test_api "登入API" "POST" "$BACKEND_URL/api/v1/auth/login" '{"email":"demo@example.com","password":"demo123"}' "200"
test_api "用戶資料API" "GET" "$BACKEND_URL/api/v1/auth/me" "" "200"
test_api "影片列表API" "GET" "$BACKEND_URL/api/v1/videos" "" "200"
test_api "儀表板分析API" "GET" "$BACKEND_URL/api/v1/analytics/dashboard" "" "200"
test_api "AI腳本生成API" "POST" "$BACKEND_URL/api/v1/ai/generate-script" '{"topic":"測試主題"}' "200"
test_api "AI圖像生成API" "POST" "$BACKEND_URL/api/v1/ai/generate-image" '{"prompt":"beautiful landscape"}' "200"

echo ""

# 測試前端頁面
echo -e "${BLUE}🌐 測試前端頁面...${NC}"
test_frontend_page "前端首頁" "$FRONTEND_URL" "AutoVideo"
test_api "登入頁面" "GET" "$FRONTEND_URL/login" "" "200"

echo ""

# 性能測試
echo -e "${BLUE}⚡ 基本性能測試...${NC}"
performance_test "健康檢查響應" "$BACKEND_URL/health"
performance_test "影片列表響應" "$BACKEND_URL/api/v1/videos"
performance_test "分析數據響應" "$BACKEND_URL/api/v1/analytics/dashboard"
performance_test "前端首頁響應" "$FRONTEND_URL"

echo ""

# 測試後端API數據結構
echo -e "${BLUE}📊 驗證API數據結構...${NC}"

echo -n "驗證登入API回應結構... "
curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"demo@example.com","password":"demo123"}' | \
    python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    assert data.get('success') == True, 'success field missing or false'
    assert 'data' in data, 'data field missing'
    assert 'user' in data['data'], 'user field missing'
    assert 'token' in data['data'], 'token field missing'
    print('✅ PASS')
    exit(0)
except Exception as e:
    print(f'❌ FAIL: {e}')
    exit(1)
" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

echo -n "驗證影片列表API回應結構... "
curl -s "$BACKEND_URL/api/v1/videos" | \
    python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    assert data.get('success') == True, 'success field missing or false'
    assert 'data' in data, 'data field missing'
    assert 'videos' in data['data'], 'videos field missing'
    assert isinstance(data['data']['videos'], list), 'videos should be a list'
    if data['data']['videos']:
        video = data['data']['videos'][0]
        assert 'id' in video, 'video id missing'
        assert 'title' in video, 'video title missing'
    print('✅ PASS')
    exit(0)
except Exception as e:
    print(f'❌ FAIL: {e}')
    exit(1)
" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

echo ""

# 輸出測試結果
echo -e "${BLUE}📊 測試結果總結:${NC}"
echo -e "   ${GREEN}✅ 通過: $TESTS_PASSED 個測試${NC}"
echo -e "   ${RED}❌ 失敗: $TESTS_FAILED 個測試${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc)
    echo -e "   📈 成功率: ${SUCCESS_RATE}%"
fi

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 所有測試通過！前端-後端整合正常運行${NC}"
    exit 0
else
    echo -e "\n${RED}❌ 有 $TESTS_FAILED 個測試失敗，請檢查上述錯誤${NC}"
    exit 1
fi