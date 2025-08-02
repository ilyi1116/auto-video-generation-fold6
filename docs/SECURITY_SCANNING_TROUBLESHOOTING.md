# 安全掃描故障排除指南

## 問題概述

本指南旨在解決 GitHub Actions 中的安全掃描問題，特別是 CodeQL Action 的權限和配置問題。

## 常見錯誤及解決方案

### 1. "Resource not accessible by integration" 錯誤

**錯誤訊息：**
```
🛡️ Security Scanning
Resource not accessible by integration - https://docs.github.com/rest
```

**原因：**
- CodeQL Action 缺少必要的權限
- 從 fork 倉庫發起的 PR 受到權限限制
- 工作流程配置不完整

**解決方案：**

#### A. 檢查權限配置
確保在工作流程檔案中正確設定權限：

```yaml
permissions:
  security-events: write
  actions: read
  contents: read
  pull-requests: read
```

#### B. 處理 Fork PR 限制
在安全掃描工作中添加條件檢查：

```yaml
if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
```

#### C. 完整的 CodeQL 配置
確保包含所有必要的 CodeQL 步驟：

```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: python, javascript
    queries: security-extended,security-and-quality

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

### 2. "This run of the CodeQL Action does not have permission" 錯誤

**錯誤訊息：**
```
This run of the CodeQL Action does not have permission to access Code Scanning API endpoints.
```

**解決方案：**

#### A. 檢查倉庫設定
1. 前往 GitHub 倉庫設定
2. 進入 "Security" → "Code security and analysis"
3. 確保 "Code scanning" 已啟用
4. 選擇 "GitHub Advanced Security" 或 "CodeQL"

#### B. 檢查組織權限
如果是組織倉庫：
1. 確保組織已啟用 GitHub Advanced Security
2. 檢查倉庫的權限設定
3. 確認 CodeQL 功能已啟用

### 3. 安全掃描工具配置

#### A. Snyk 配置
```yaml
- name: Run Snyk Security Scan
  uses: snyk/actions/python@master
  continue-on-error: true
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    args: --severity-threshold=high --file=requirements.txt --sarif-file-output=snyk.sarif
```

#### B. Trivy 配置
```yaml
- name: Run Trivy Container Scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: '.'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

#### C. GitLeaks 配置
```yaml
- name: Run GitLeaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    config-path: .gitleaks.toml
```

## 最佳實踐

### 1. 權限管理
- 使用最小權限原則
- 只在必要的工作中設定權限
- 定期檢查權限設定

### 2. 錯誤處理
- 使用 `continue-on-error: true` 避免單一工具失敗影響整個流程
- 添加條件檢查避免不必要的執行
- 提供詳細的錯誤日誌

### 3. 效能優化
- 使用快取減少重複下載
- 並行執行獨立的安全掃描
- 設定適當的超時時間

## 故障排除檢查清單

### 權限檢查
- [ ] 工作流程檔案包含正確的權限設定
- [ ] 倉庫已啟用 Code scanning
- [ ] 組織權限設定正確（如果是組織倉庫）

### 配置檢查
- [ ] CodeQL 初始化步驟存在
- [ ] 語言設定正確（python, javascript）
- [ ] 查詢設定適當（security-extended, security-and-quality）

### 環境檢查
- [ ] GitHub Secrets 設定正確
- [ ] 環境變數配置完整
- [ ] 依賴項安裝成功

### 執行檢查
- [ ] 工作流程觸發條件正確
- [ ] 分支保護規則設定適當
- [ ] 錯誤處理機制完善

## 常見問題 FAQ

### Q: 為什麼從 fork 倉庫發起的 PR 會失敗？
A: GitHub 基於安全考量，限制 fork 倉庫對主倉庫的某些權限。解決方案是在工作流程中添加條件檢查。

### Q: 如何啟用 GitHub Advanced Security？
A: 需要 GitHub Enterprise 帳戶或 GitHub Pro 帳戶。在倉庫設定中啟用 Code scanning。

### Q: 安全掃描失敗會影響部署嗎？
A: 建議設定 `continue-on-error: true` 避免安全掃描失敗影響主要 CI/CD 流程。

### Q: 如何自定義安全掃描規則？
A: 可以修改 `.gitleaks.toml` 檔案或使用自定義的 CodeQL 查詢。

## 聯絡支援

如果問題持續存在，請：
1. 檢查 GitHub Actions 日誌獲取詳細錯誤資訊
2. 參考 GitHub 官方文件
3. 在 GitHub Community 中尋求協助 