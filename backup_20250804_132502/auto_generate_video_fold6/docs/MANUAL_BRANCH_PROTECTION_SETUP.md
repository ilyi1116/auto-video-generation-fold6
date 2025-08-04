# 手動分支保護設定指南

由於環境限制無法自動執行，請按照以下步驟手動設定分支保護：

## 🎯 推薦設定：Strict 級別保護

### 第一步：進入 GitHub 設定
1. 開啟您的 GitHub 倉庫：https://github.com/ilyi1116/auto-video-generation-fold6
2. 點擊 **Settings** 標籤
3. 在左側選單點擊 **Branches**

### 第二步：新增分支保護規則
1. 點擊 **Add rule** 按鈕
2. 在 **Branch name pattern** 輸入：`main`

### 第三步：設定保護選項

#### ✅ Protect matching branches
勾選以下所有選項：

**Require a pull request before merging**
- ✅ 勾選此項
- **Required number of reviewers before merging**: 設定為 `2`
- ✅ **Dismiss stale reviews when new commits are pushed**
- ✅ **Require review from code owners** (這會使用我們的 CODEOWNERS 檔案)

**Require status checks to pass before merging**
- ✅ 勾選此項
- ✅ **Require branches to be up to date before merging**
- 在搜尋框中新增以下必要檢查項目：
  - `CI / test`
  - `CI / lint`
  - `CI / build`
  - `CI / typecheck`
  - `security / dependency-scan`
  - `security / code-scan`

**Require conversation resolution before merging**
- ✅ 勾選此項

**Require signed commits**
- ⚠️ 可選，但建議勾選

**Require linear history**
- ✅ 勾選此項（保持整潔的提交歷史）

**Include administrators**
- ✅ 勾選此項（連管理員也要遵守規則）

#### ❌ 不要勾選的選項
- ❌ **Restrict pushes that create files**
- ❌ **Allow force pushes**
- ❌ **Allow deletions**

### 第四步：儲存設定
點擊 **Create** 按鈕完成設定。

## 🔍 驗證設定

設定完成後，您應該看到：

### 成功指標
- ✅ 分支保護規則出現在 Branches 設定頁面
- ✅ `main` 分支旁邊顯示保護圖示
- ✅ 無法直接推送到 `main` 分支

### 測試方法
1. 嘗試直接推送到 `main` - 應該被拒絕
2. 創建功能分支和 PR - 應該要求審查
3. 檢查 CI/CD 檢查是否正常運行

## 📊 當前 CI/CD 檢查項目

我們的 GitHub Actions 工作流程會執行：

### 基本檢查 ✅
- **Code Quality**: ESLint, Prettier, Ruff, Black
- **Tests**: 前端和後端測試套件
- **TypeScript**: 類型檢查
- **Build**: 構建驗證

### 安全檢查 ✅
- **Security Scan**: Trivy 漏洞掃描
- **Dependency Scan**: npm audit 和 safety
- **Secret Detection**: 敏感資訊檢測

### PR 品質檢查 ✅
- **Title Format**: PR 標題格式驗證
- **Description**: PR 描述完整性
- **Sensitive Files**: 敏感檔案變更警告

## 🚀 設定完成後的工作流程

### 新的開發流程
1. **創建功能分支**：`git checkout -b feature/new-feature`
2. **開發和提交**：正常開發工作
3. **推送分支**：`git push origin feature/new-feature`
4. **創建 PR**：在 GitHub 上創建 Pull Request
5. **等待檢查**：自動 CI/CD 檢查執行
6. **獲得審查**：需要 2 人審查批准
7. **合併**：所有檢查通過後才能合併

### 緊急修復流程
1. **創建 hotfix 分支**：`git checkout -b hotfix/urgent-fix`
2. **快速修復**：修復關鍵問題
3. **創建緊急 PR**：標記為高優先級
4. **快速審查**：聯繫相關人員快速審查
5. **合併和部署**：通過後立即合併

## 💡 最佳實踐建議

### PR 創建時
- 使用清晰的標題格式：`type(scope): description`
- 填寫完整的 PR 描述
- 確保所有檢查項目都已完成
- 主動聯繫相關審查者

### 代碼審查時
- 專注於邏輯正確性和設計合理性
- 檢查測試覆蓋率和品質
- 驗證安全性考量
- 確認文檔更新

### 合併前確認
- 所有 CI/CD 檢查通過 ✅
- 獲得必要的審查批准 ✅
- 解決所有對話和建議 ✅
- 分支是最新的 ✅

## ⚠️ 常見問題

### Q: 無法推送到 main 分支
**A**: 這是正常的！現在必須通過 PR 流程。

### Q: CI/CD 檢查失敗
**A**: 檢查錯誤訊息，修復問題後重新推送。

### Q: 找不到審查者
**A**: CODEOWNERS 檔案會自動指派，也可以手動添加審查者。

### Q: 緊急修復怎麼辦
**A**: 創建 hotfix 分支，聯繫相關人員快速審查。

---

**🎉 設定完成後，您的主分支將獲得企業級的安全保護！**

如有任何問題，請參考 `.github/branch-protection.md` 檔案中的詳細說明。