#!/bin/bash
"""
測試運行腳本
提供統一的測試運行和覆蓋率報告功能
"""

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 微服務測試套件${NC}"
echo "=========================================="

# 檢查 pytest 是否安裝
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest 未安裝，請先安裝: pip install pytest pytest-cov pytest-asyncio${NC}"
    exit 1
fi

# 默認參數
SERVICE=""
COVERAGE=false
VERBOSE=false
INTEGRATION=false

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -i|--integration)
            INTEGRATION=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [選項]"
            echo "選項:"
            echo "  -s, --service SERVICE    只測試指定服務"
            echo "  -c, --coverage          生成覆蓋率報告"
            echo "  -v, --verbose           詳細輸出"
            echo "  -i, --integration       運行集成測試"
            echo "  -h, --help              顯示此幫助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知選項: $1${NC}"
            exit 1
            ;;
    esac
done

# 構建 pytest 命令
PYTEST_CMD="pytest"
TEST_PATH="src/services"

if [[ -n "$SERVICE" ]]; then
    TEST_PATH="src/services/$SERVICE/tests"
    echo -e "${BLUE}🎯 測試服務: $SERVICE${NC}"
fi

if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src/services --cov-report=html --cov-report=term-missing"
    echo -e "${BLUE}📊 包含覆蓋率報告${NC}"
fi

if [[ "$INTEGRATION" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -m integration"
    echo -e "${BLUE}🔗 運行集成測試${NC}"
fi

# 運行測試
echo -e "${BLUE}🚀 開始測試...${NC}"
echo "命令: $PYTEST_CMD $TEST_PATH"
echo ""

if $PYTEST_CMD $TEST_PATH; then
    echo ""
    echo -e "${GREEN}✅ 測試完成！${NC}"
    
    if [[ "$COVERAGE" == true ]]; then
        echo -e "${BLUE}📊 覆蓋率報告已生成: htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ 測試失敗！${NC}"
    exit 1
fi
