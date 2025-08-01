# 🧬 TDD 工作流程檢查清單

## 📋 每次開發前檢查

### 環境準備
- [ ] Git 工作區乾淨 (`git status` 沒有未提交變更)
- [ ] 拉取最新程式碼 (`git pull origin main`)
- [ ] 啟動測試監控模式 (`npm run test:watch` 或 `pytest --watch`)
- [ ] 確認測試覆蓋率工具正常運作

## 🔴 RED 階段 - 撰寫失敗測試

### 測試撰寫檢查
- [ ] 使用描述性的測試名稱 (`shouldReturnErrorWhenInputIsEmpty`)
- [ ] 遵循 AAA 模式 (Arrange-Act-Assert)
- [ ] 測試明確失敗並顯示正確的錯誤訊息
- [ ] 測試專注於單一行為
- [ ] 沒有實作任何產品程式碼

### 提交 RED 階段
```bash
# 執行測試確認失敗
npm run test:unit  # 或 pytest tests/

# 提交失敗測試
git add .
git commit -m "red: add failing test for [功能描述]"
```

## 🟢 GREEN 階段 - 實現最少程式碼

### 實作檢查
- [ ] 只撰寫讓測試通過的最少程式碼
- [ ] 避免過度設計或預期未來需求
- [ ] 不考慮程式碼優雅性，專注於功能實現
- [ ] 所有測試都通過
- [ ] 沒有修改既有測試

### 提交 GREEN 階段
```bash
# 執行測試確認通過
npm run test:unit  # 或 pytest tests/

# 檢查測試覆蓋率
npm run test:coverage  # 或 pytest --cov

# 提交實作程式碼
git add .
git commit -m "green: implement [功能] to pass tests"
```

## 🔵 REFACTOR 階段 - 改善程式碼

### 重構檢查
- [ ] 所有測試仍然通過
- [ ] 消除重複程式碼 (DRY 原則)
- [ ] 改善變數和函數命名
- [ ] 提取共用邏輯到適當的位置
- [ ] 程式碼符合品質標準 (複雜度 ≤ 10, 方法長度 ≤ 20 行)
- [ ] 沒有改變程式行為

### 提交 REFACTOR 階段
```bash
# 執行完整測試套件
npm run test:all  # 或 pytest tests/ --cov

# 檢查程式碼品質
npm run lint      # 或 flake8 .

# 提交重構程式碼
git add .
git commit -m "refactor: [重構描述]"
```

## 📊 品質檢查清單

### 每次提交前
- [ ] 測試覆蓋率 ≥ 90%
- [ ] 所有測試通過
- [ ] Linting 檢查通過
- [ ] 程式碼複雜度 ≤ 10
- [ ] 沒有 TODO 或 FIXME 註解
- [ ] 提交訊息符合 TDD 格式

### 功能完成後
- [ ] 執行完整測試套件 (單元、整合、E2E)
- [ ] 測試在 Docker 環境中通過
- [ ] 執行效能測試 (如適用)
- [ ] 更新相關文檔
- [ ] 程式碼審查通過

## 🚀 CI/CD 整合

### Pre-commit Hooks
```bash
# 安裝 pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg

# 測試 hooks
pre-commit run --all-files
```

### 本地驗證
```bash
# 前端完整檢查
cd frontend
npm run quality:check

# 後端完整檢查
python -m pytest --cov-fail-under=90 --cov-report=html
flake8 . --max-complexity=10
```

## 🎯 TDD 最佳實踐提醒

### 核心原則
- **紅燈時間最短化**: 快速寫出失敗測試
- **綠燈實作最簡化**: 只寫通過測試的程式碼
- **重構持續進行**: 每個綠燈後考慮重構
- **小步驟前進**: 頻繁的小提交勝過大型提交

### 常見陷阱避免
- ❌ 在 RED 階段寫產品程式碼
- ❌ 在 GREEN 階段過度設計
- ❌ 在 REFACTOR 階段改變行為
- ❌ 跳過任何階段
- ❌ 在測試未通過時提交

### 效率提升技巧
- 使用快捷鍵快速執行測試
- 設定 IDE 自動執行測試
- 利用測試驅動的除錯方式
- 保持測試運行速度快速

## 📈 度量指標

### 每日追蹤
- TDD 循環完成次數
- 平均 RED-GREEN-REFACTOR 循環時間
- 測試覆蓋率趨勢
- 程式碼複雜度分佈

### 每週回顧
- TDD 實踐一致性
- 程式碼品質改善
- 缺陷發現與修復效率
- 開發速度變化
