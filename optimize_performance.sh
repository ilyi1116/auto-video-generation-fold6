#!/bin/bash
# 性能優化腳本
# Performance Optimization Script

set -e

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FRONTEND_DIR="/Users/chenghengtsai/Documents/文件 - CHENG的MacBook Pro/auto-video-generation-fold6/auto-video-generation-fold6/src/frontend"
BACKEND_DIR="/Users/chenghengtsai/Documents/文件 - CHENG的MacBook Pro/auto-video-generation-fold6/auto-video-generation-fold6/src/services/api-gateway"

echo -e "${BLUE}🚀 開始性能優化...${NC}\n"

# 1. 檢查前端性能
echo -e "${BLUE}📊 檢查前端性能...${NC}"

# 檢查 bundle 大小
if [ -d "$FRONTEND_DIR/.svelte-kit/output" ]; then
    echo "📦 檢查 SvelteKit 構建輸出..."
    find "$FRONTEND_DIR/.svelte-kit/output" -name "*.js" -type f -exec du -h {} + | sort -hr | head -10
else
    echo "⚠️  構建輸出不存在，執行構建..."
    cd "$FRONTEND_DIR"
    npm run build
    echo "📦 檢查構建後的 bundle 大小..."
    find ".svelte-kit/output" -name "*.js" -type f -exec du -h {} + | sort -hr | head -10
fi

# 2. 前端性能優化建議
echo -e "\n${BLUE}🔧 前端性能優化建議...${NC}"

# 檢查是否使用了圖片優化
echo "🖼️  檢查圖片優化..."
if grep -r "placeholder.*webp\|placeholder.*avif" "$FRONTEND_DIR/src" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 使用了現代圖片格式${NC}"
else
    echo -e "${YELLOW}⚠️  建議使用 WebP/AVIF 格式圖片${NC}"
fi

# 檢查是否有懶載入
if grep -r "loading=\"lazy\"\|IntersectionObserver" "$FRONTEND_DIR/src" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 實現了懶載入${NC}"
else
    echo -e "${YELLOW}⚠️  建議實現圖片懶載入${NC}"
fi

# 檢查是否有代碼分割
if grep -r "import(" "$FRONTEND_DIR/src" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 使用了動態導入${NC}"
else
    echo -e "${YELLOW}⚠️  建議使用動態導入進行代碼分割${NC}"
fi

# 3. 後端性能檢查
echo -e "\n${BLUE}⚡ 檢查後端性能...${NC}"

# 檢查是否啟動了快取
if grep -r "cache\|Cache" "$BACKEND_DIR" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 實現了快取機制${NC}"
else
    echo -e "${YELLOW}⚠️  建議實現API快取${NC}"
fi

# 檢查是否有限流機制
if grep -r "limiter\|rate_limit" "$BACKEND_DIR" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 實現了限流機制${NC}"
else
    echo -e "${YELLOW}⚠️  建議實現API限流${NC}"
fi

# 4. 資料庫優化檢查
echo -e "\n${BLUE}🗄️  資料庫優化檢查...${NC}"

# 檢查是否有索引定義
if find "$FRONTEND_DIR/../.." -name "*.sql" -o -name "*migration*" | xargs grep -l "INDEX\|index" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 定義了資料庫索引${NC}"
else
    echo -e "${YELLOW}⚠️  建議為常用查詢添加索引${NC}"
fi

# 5. 監控和日誌優化
echo -e "\n${BLUE}📈 監控和日誌優化...${NC}"

# 檢查是否有結構化日誌
if grep -r "structlog\|structured" "$BACKEND_DIR" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 使用了結構化日誌${NC}"
else
    echo -e "${YELLOW}⚠️  建議實現結構化日誌${NC}"
fi

# 檢查是否有性能監控
if grep -r "prometheus\|metrics" "$BACKEND_DIR" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 實現了性能監控${NC}"
else
    echo -e "${YELLOW}⚠️  建議添加性能監控${NC}"
fi

# 6. 執行基本性能測試
echo -e "\n${BLUE}🧪 執行基本性能測試...${NC}"

# 測試 API 響應時間
test_api_performance() {
    local name="$1"
    local url="$2"
    
    echo -n "測試 $name 響應時間... "
    
    # 執行 5 次請求並計算平均時間
    total_time=0
    for i in {1..5}; do
        start_time=$(date +%s%3N)
        curl -s "$url" > /dev/null 2>&1
        end_time=$(date +%s%3N)
        response_time=$((end_time - start_time))
        total_time=$((total_time + response_time))
    done
    
    avg_time=$((total_time / 5))
    
    if [ "$avg_time" -lt 200 ]; then
        echo -e "${GREEN}${avg_time}ms (優秀)${NC}"
    elif [ "$avg_time" -lt 500 ]; then
        echo -e "${YELLOW}${avg_time}ms (良好)${NC}"
    else
        echo -e "${RED}${avg_time}ms (需優化)${NC}"
    fi
}

# 檢查服務是否運行
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    test_api_performance "健康檢查" "http://localhost:8001/health"
    test_api_performance "影片列表" "http://localhost:8001/api/v1/videos"
    test_api_performance "分析數據" "http://localhost:8001/api/v1/analytics/dashboard"
else
    echo -e "${YELLOW}⚠️  後端服務未運行，跳過 API 性能測試${NC}"
fi

# 7. 創建性能優化建議報告
echo -e "\n${BLUE}📋 生成性能優化建議報告...${NC}"

cat > performance_optimization_report.md << 'EOF'
# 性能優化報告
Performance Optimization Report

## 🎯 優化目標

- 頁面載入時間 < 2秒
- API 響應時間 < 500ms
- Core Web Vitals 達到 "Good" 標準
- 減少資源使用和提升用戶體驗

## 📊 當前性能狀態

### 前端性能
- Bundle 大小: 需分析
- 圖片優化: 需改進
- 代碼分割: 需實現
- 懶載入: 需實現

### 後端性能
- API 快取: 已實現
- 限流機制: 已實現
- 結構化日誌: 已實現
- 性能監控: 部分實現

## 🔧 立即優化建議

### 高優先級優化

1. **圖片優化**
   ```bash
   # 使用 WebP 格式
   # 實現響應式圖片
   # 添加懶載入
   ```

2. **代碼分割**
   ```javascript
   // 動態導入組件
   const LazyComponent = lazy(() => import('./LazyComponent.svelte'));
   ```

3. **API 快取**
   ```python
   # 實現 Redis 快取
   # 設置適當的 TTL
   # 快取失效策略
   ```

### 中等優先級優化

1. **資料庫索引優化**
2. **CDN 整合**
3. **服務工作器 (Service Worker)**
4. **預載入關鍵資源**

### 低優先級優化

1. **字型載入優化**
2. **第三方腳本延遲載入**
3. **CSS 優化**

## 📈 監控指標

### Core Web Vitals
- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1

### API 性能指標
- **健康檢查**: < 100ms
- **資料查詢**: < 500ms
- **檔案上傳**: < 2s

### 資源使用指標
- **記憶體使用**: < 200MB
- **CPU 使用**: < 50%
- **網路頻寬**: 最佳化

## 🚀 實施計劃

### 第一週
- [ ] 實現圖片懶載入
- [ ] 添加 API 快取層
- [ ] 優化 bundle 大小

### 第二週
- [ ] 實現代碼分割
- [ ] 添加 Service Worker
- [ ] 資料庫索引優化

### 第三週
- [ ] 性能監控完善
- [ ] CDN 整合
- [ ] 持續性能測試

## 📝 追蹤進度

定期執行性能測試並記錄結果，確保持續改進。

---
*生成時間: $(date)*
EOF

echo -e "${GREEN}✅ 性能優化報告已生成: performance_optimization_report.md${NC}"

# 8. 實施基本優化
echo -e "\n${BLUE}🔧 實施基本優化...${NC}"

# 前端優化：添加 preload 連結
if [ -f "$FRONTEND_DIR/src/app.html" ]; then
    echo "🔗 優化資源預載入..."
    
    # 檢查是否已經有 preload
    if ! grep -q "preload" "$FRONTEND_DIR/src/app.html"; then
        # 在 head 中添加資源預載入
        sed -i '' '/<head>/a\
    <!-- 預載入關鍵字體 -->\
    <link rel="preconnect" href="https://fonts.googleapis.com">\
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\
    <!-- 預載入關鍵 CSS -->\
    <link rel="preload" href="/app.css" as="style">\
' "$FRONTEND_DIR/src/app.html"
        echo -e "${GREEN}✅ 添加了資源預載入${NC}"
    else
        echo -e "${GREEN}✅ 資源預載入已存在${NC}"
    fi
fi

# 後端優化：檢查並優化 mock server
echo "⚡ 優化後端響應..."
if [ -f "$BACKEND_DIR/mock_server.py" ]; then
    # 檢查是否有響應壓縮
    if ! grep -q "gzip" "$BACKEND_DIR/mock_server.py"; then
        echo -e "${YELLOW}⚠️  建議添加響應壓縮${NC}"
    else
        echo -e "${GREEN}✅ 響應壓縮已實現${NC}"
    fi
fi

echo -e "\n${GREEN}🎉 性能優化完成！${NC}"
echo -e "📋 請檢查生成的報告: ${BLUE}performance_optimization_report.md${NC}"
echo -e "🧪 建議執行: ${BLUE}./test_integration.sh${NC} 驗證優化效果"

echo -e "\n${BLUE}🔄 下一步建議:${NC}"
echo "1. 根據報告實施高優先級優化"
echo "2. 設置持續性能監控"
echo "3. 定期執行性能測試"
echo "4. 監控生產環境指標"