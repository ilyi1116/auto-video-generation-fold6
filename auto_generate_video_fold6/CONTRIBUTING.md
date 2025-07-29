# 🤝 貢獻指南

感謝您對 Auto Video 專案的興趣！我們歡迎各種形式的貢獻。

## 📋 目錄

- [開發環境設置](#開發環境設置)
- [貢獻流程](#貢獻流程)
- [代碼規範](#代碼規範)
- [測試要求](#測試要求)
- [提交訊息規範](#提交訊息規範)
- [Pull Request 指南](#pull-request-指南)
- [問題回報](#問題回報)
- [安全漏洞回報](#安全漏洞回報)

## 🚀 開發環境設置

### 系統要求
- Python 3.11+
- Node.js 18+
- Docker 20.10+
- Git 2.30+

### 快速開始
```bash
# 1. Fork 並克隆專案
git clone https://github.com/your-username/auto-video-generation.git
cd auto-video-generation

# 2. 執行自動化設置
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh

# 3. 啟動開發環境
docker-compose up -d
```

## 🔄 貢獻流程

### 1. 問題討論
- 在開始開發前，請先創建或參與相關的 Issue 討論
- 確保您的貢獻符合專案的發展方向

### 2. 分支策略
```bash
# 從 main 分支創建功能分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 或修復分支
git checkout -b fix/issue-number-description
```

### 3. 分支命名規範
- `feature/` - 新功能開發
- `fix/` - 問題修復
- `docs/` - 文檔更新
- `refactor/` - 代碼重構
- `test/` - 測試改進
- `ci/` - CI/CD 相關

## 📏 代碼規範

### Python 代碼規範
- 遵循 PEP 8 規範
- 使用 Black 格式化工具
- 行長度限制：79 字符
- 使用類型提示 (Type Hints)

```bash
# 格式化代碼
black services/
isort services/

# 代碼檢查
flake8 services/
mypy services/
```

### JavaScript/TypeScript 規範
- 使用 Prettier 格式化
- 遵循 ESLint 規則
- 使用 TypeScript 嚴格模式

```bash
# 前端代碼檢查
cd frontend
npm run lint
npm run format
npm run type-check
```

### 通用規範
- 使用有意義的變數和函數名稱
- 編寫清晰的註釋（僅在必要時）
- 保持函數簡潔，單一職責
- 避免深層巢狀結構

## 🧪 測試要求

### 測試覆蓋率要求
- **最低覆蓋率**: 80%
- **目標覆蓋率**: 90%+

### 測試類型
1. **單元測試** - 測試個別函數和類
2. **整合測試** - 測試服務間協作
3. **端對端測試** - 測試完整用戶流程

### 執行測試
```bash
# 後端測試
pytest tests/ -v --cov=services --cov-report=html

# 前端測試
cd frontend
npm run test
npm run test:e2e

# 完整測試套件
./scripts/run-all-tests.sh
```

### 測試編寫指南
- 每個新功能必須包含對應測試
- 測試應該獨立且可重複執行
- 使用描述性的測試名稱
- 遵循 AAA 模式 (Arrange, Act, Assert)

## 📝 提交訊息規範

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 類型 (Type)
- `feat` - 新功能
- `fix` - 問題修復
- `docs` - 文檔更新
- `style` - 代碼格式調整
- `refactor` - 代碼重構
- `test` - 測試相關
- `ci` - CI/CD 相關
- `perf` - 性能優化
- `chore` - 其他雜務

### 範例
```bash
feat(auth): add OAuth2 login support
fix(video): resolve rendering timeout issue
docs(api): update endpoint documentation
test(auth): add integration tests for login flow
```

## 🔍 Pull Request 指南

### PR 檢查清單
在提交 PR 前，請確保：

- [ ] 代碼通過所有測試
- [ ] 代碼覆蓋率符合要求
- [ ] 遵循代碼規範
- [ ] 更新相關文檔
- [ ] 填寫完整的 PR 描述
- [ ] 連結相關的 Issue
- [ ] 通過 CI/CD 檢查

### PR 模板
請使用以下模板描述您的 PR：

```markdown
## 📋 變更摘要
簡潔描述這個 PR 的主要變更

## 🔗 相關 Issue
Closes #issue-number

## 🧪 測試
- [ ] 單元測試通過
- [ ] 整合測試通過
- [ ] 手動測試完成

## 📸 截圖（如適用）
添加相關截圖

## 🔍 審查要點
請重點關注以下方面：
- 代碼邏輯
- 性能影響
- 安全性考量
```

### 審查流程
1. 自動化 CI/CD 檢查
2. 代碼審查 (至少 2 人)
3. 測試驗證
4. 部署到測試環境
5. 最終批准和合併

## 🐛 問題回報

### 回報流程
1. 搜尋現有 Issues 避免重複
2. 使用適當的 Issue 模板
3. 提供詳細的重現步驟
4. 包含系統環境資訊
5. 添加相關日誌和截圖

### 問題分類
- **Bug**: 系統錯誤或異常行為
- **Feature Request**: 新功能建議
- **Documentation**: 文檔改進
- **Question**: 使用問題或疑問

## 🔒 安全漏洞回報

**請勿在公開 Issue 中回報安全漏洞！**

### 安全漏洞回報流程
1. 發送郵件到：security@autovideo.com
2. 包含漏洞詳細描述
3. 提供重現步驟
4. 等待安全團隊回應

我們承諾在 48 小時內回應安全報告。

## 🏷️ 標籤系統

### Issue 標籤
- `bug` - 錯誤報告
- `enhancement` - 功能增強
- `documentation` - 文檔相關
- `good first issue` - 適合新貢獻者
- `help wanted` - 需要協助
- `priority: high/medium/low` - 優先級
- `status: in-progress` - 開發中
- `status: needs-review` - 待審查

### PR 標籤
- `WIP` - 工作進行中
- `ready for review` - 準備審查
- `needs changes` - 需要修改
- `approved` - 已批准

## 📞 社群與支援

### 溝通管道
- **GitHub Issues**: 問題回報和功能建議
- **GitHub Discussions**: 技術討論和問答
- **Email**: team@autovideo.com

### 貢獻認可
- 所有貢獻者將在 CONTRIBUTORS.md 中列出
- 重要貢獻者將獲得專案權限
- 定期表彰傑出貢獻者

## 📄 授權聲明

通過貢獻到此專案，您同意您的貢獻將在 MIT 授權條款下授權。

---

感謝您的貢獻！🎉

如有任何問題，請隨時聯繫我們。