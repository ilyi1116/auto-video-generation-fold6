# 主分支保護設定指南

## 🛡️ 分支保護策略

### 自動化分支保護設定

這個配置將自動保護主分支，確保所有變更都經過適當的審查和測試。

### 保護規則配置

#### 1. 基本保護設定
- **分支名稱**: `main`
- **需要審查**: 必須至少 1 人審查
- **需要狀態檢查**: 必須通過 CI/CD
- **強制推送保護**: 禁止強制推送
- **刪除保護**: 禁止刪除分支

#### 2. 高級保護設定
- **管理員包含在規則內**: 是
- **允許合併前更新**: 是
- **需要最新分支**: 是
- **對話解決**: 必須解決所有對話

## 📋 手動設定步驟

如果需要手動設定，請按照以下步驟：

### 在 GitHub 上設定

1. 進入 Repository → Settings → Branches
2. 點擊 "Add rule" 或編輯現有規則
3. 設定以下選項：

#### Branch name pattern
```
main
```

#### Protection settings
- [x] Require a pull request before merging
  - [x] Require approvals: 1
  - [x] Dismiss stale reviews when new commits are pushed
  - [x] Require review from code owners
  
- [x] Require status checks to pass before merging
  - [x] Require branches to be up to date before merging
  - Required status checks:
    - [x] CI / test
    - [x] CI / lint
    - [x] CI / build
    - [x] security / dependency-scan

- [x] Require signed commits
- [x] Require linear history
- [x] Include administrators
- [x] Restrict pushes that create files
- [x] Restrict force pushes
- [x] Allow deletions: ❌

## 🔧 自動化保護腳本

使用 GitHub CLI 可以自動設定分支保護：

```bash
#!/bin/bash

# 設定主分支保護規則
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["CI / test","CI / lint","CI / build","security / dependency-scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_linear_history=true
```

## 🚀 CI/CD 整合

確保以下 CI/CD 檢查通過才能合併：

### 必要檢查項目
- **測試通過**: 所有單元測試、整合測試
- **代碼風格**: ESLint、Prettier 檢查
- **構建成功**: 前端和後端構建
- **安全掃描**: 依賴漏洞掃描
- **類型檢查**: TypeScript 類型檢查

### 可選檢查項目
- **效能測試**: Lighthouse 分數
- **無障礙測試**: a11y 合規檢查
- **代碼覆蓋率**: 測試覆蓋率 > 80%

## 📝 工作流程

### 開發流程
1. 從 `main` 創建功能分支
2. 開發並提交變更
3. 創建 Pull Request
4. 通過所有自動檢查
5. 獲得代碼審查批准
6. 合併到 `main`

### 緊急修復流程
1. 創建 `hotfix/*` 分支
2. 修復問題並測試
3. 創建 Pull Request（標記為緊急）
4. 快速審查和合併
5. 回溯到開發分支

## 🎯 保護級別

### Level 1: 基本保護
- Pull Request 必須
- 1 人審查
- CI 檢查通過

### Level 2: 嚴格保護（推薦）
- Pull Request 必須
- 2 人審查
- 代碼擁有者審查
- 所有 CI 檢查通過
- 最新分支要求

### Level 3: 企業級保護
- 簽名提交要求
- 線性歷史要求
- 管理員包含在規則內
- 高級安全掃描

## 🔍 監控和報告

### 分支保護違規監控
- 自動通知違規嘗試
- 定期審查保護規則
- 合規性報告

### 指標追蹤
- Pull Request 合併時間
- 代碼審查效率
- CI/CD 成功率
- 安全漏洞發現率

## 📚 最佳實踐

### 代碼審查
- 專注於邏輯和設計
- 檢查安全漏洞
- 確保測試覆蓋
- 驗證文檔更新

### 自動化測試
- 單元測試覆蓋 > 80%
- 整合測試覆蓋關鍵路徑
- E2E 測試覆蓋用戶流程
- 效能回歸測試

### 安全檢查
- 依賴漏洞掃描
- 代碼靜態分析
- 秘密洩露檢測
- 授權檢查

這個配置確保了主分支的穩定性和安全性，同時保持開發效率。