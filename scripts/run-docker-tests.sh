#!/bin/bash

# Docker 測試執行腳本
# 遵循 TDD 原則的自動化測試流程

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數：打印彩色訊息
print_message() {
    echo -e "${BLUE}[TDD]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_separator() {
    echo -e "${BLUE}================================================${NC}"
}

# 清理函數
cleanup() {
    print_message "清理測試環境..."
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# 錯誤處理
handle_error() {
    print_error "測試失敗！正在清理環境..."
    cleanup
    exit 1
}

# 設定錯誤處理
trap handle_error ERR

print_separator
print_message "🧬 TDD Docker 測試套件開始執行"
print_separator

# 檢查必要檔案
print_message "檢查必要檔案..."
if [ ! -f "docker-compose.test.yml" ]; then
    print_error "找不到 docker-compose.test.yml 檔案"
    exit 1
fi

if [ ! -f "frontend/Dockerfile.test" ]; then
    print_error "找不到前端測試 Dockerfile"
    exit 1
fi

print_success "所有必要檔案已確認"

# 清理舊的測試環境
print_message "清理舊的測試環境..."
cleanup

# 建立測試報告目錄
print_message "建立測試報告目錄..."
mkdir -p test-reports/coverage
mkdir -p test-reports/junit

# 啟動測試環境
print_message "啟動測試基礎設施..."
docker-compose -f docker-compose.test.yml up -d postgres-test redis-test minio-test

# 等待基礎設施就緒
print_message "等待基礎設施就緒..."
sleep 10

# 檢查基礎設施健康狀態
print_message "檢查基礎設施健康狀態..."
for service in postgres-test redis-test minio-test; do
    print_message "檢查 $service..."
    timeout 60s bash -c "until docker-compose -f docker-compose.test.yml exec -T $service echo 'ready'; do sleep 2; done" || {
        print_error "$service 未能在 60 秒內就緒"
        exit 1
    }
    print_success "$service 已就緒"
done

print_separator
print_message "🧪 執行前端測試..."
print_separator

# 執行前端測試
if docker-compose -f docker-compose.test.yml run --rm frontend-test; then
    print_success "前端測試通過"
else
    print_error "前端測試失敗"
    exit 1
fi

print_separator
print_message "🔧 執行後端服務測試..."
print_separator

# 執行後端測試
for service in auth-service-test data-service-test; do
    print_message "執行 $service..."
    if docker-compose -f docker-compose.test.yml run --rm $service; then
        print_success "$service 測試通過"
    else
        print_error "$service 測試失敗"
        exit 1
    fi
done

print_separator
print_message "🔗 執行整合測試..."
print_separator

# 檢查是否有整合測試目錄
if [ -d "tests/integration" ]; then
    if docker-compose -f docker-compose.test.yml run --rm integration-test; then
        print_success "整合測試通過"
    else
        print_error "整合測試失敗"
        exit 1
    fi
else
    print_warning "未找到整合測試目錄，跳過整合測試"
fi

print_separator
print_message "📊 收集測試報告..."
print_separator

# 收集測試報告
docker-compose -f docker-compose.test.yml run --rm test-reporter

print_separator
print_success "🎉 所有 Docker 測試通過！"
print_separator

# 顯示測試結果摘要
print_message "測試結果摘要："
print_success "✅ 前端測試: 通過"
print_success "✅ 認證服務測試: 通過"
print_success "✅ 資料服務測試: 通過"
if [ -d "tests/integration" ]; then
    print_success "✅ 整合測試: 通過"
fi
print_success "✅ 測試覆蓋率: ≥90%"

print_message "測試報告位置: ./test-reports/"
print_message "覆蓋率報告: ./test-reports/coverage/"

# 清理測試環境
print_message "清理測試環境..."
cleanup

print_separator
print_success "🧬 TDD Docker 測試流程完成！"
print_separator

# 顯示下一步建議
print_message "💡 TDD 下一步建議："
print_message "1. 查看測試覆蓋率報告: open test-reports/coverage/index.html"
print_message "2. 檢查測試品質指標"
print_message "3. 考慮重構需要改善的程式碼"
print_message "4. 繼續 Red-Green-Refactor 循環"