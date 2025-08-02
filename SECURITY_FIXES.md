# 🔒 安全漏洞修復指南

## 🚨 緊急修復 (Critical & High)

### 1. Python 依賴更新

```bash
# 更新到安全版本
pip install --upgrade \
    requests>=2.32.4 \
    Pillow>=10.3.0 \
    aiohttp>=3.10.11 \
    fastapi>=0.109.1 \
    python-multipart>=0.0.7
```

### 2. Node.js 依賴更新

```bash
# 前端安全更新
cd auto_generate_video_fold6/frontend
npm install @sveltejs/kit@latest
npm install esbuild@latest
npm install cookie@latest
npm audit fix --force
```

## 📝 具體修復步驟

### Phase 1: 關鍵依賴升級 (1-2天)

1. **更新 requirements.txt**
```text
# 替換現有版本
requests==2.32.4        # 從 2.31.0 升級
Pillow==10.3.0          # 從 10.1.0 升級  
aiohttp==3.10.11        # 從 3.9.1 升級
fastapi==0.109.1        # 從 0.104.1 升級
python-multipart==0.0.7  # 從 0.0.6 升級
```

2. **測試依賴兼容性**
```bash
# 每個服務分別測試
cd services/video-service
pip install -r requirements.txt
python -m pytest tests/
```

### Phase 2: 前端安全更新 (1天)

1. **更新 package.json**
```json
{
  "dependencies": {
    "@sveltejs/kit": "^2.27.0",
    "cookie": "^0.7.0"
  },
  "devDependencies": {
    "esbuild": "^0.25.8",
    "vite": "^6.1.7"
  }
}
```

### Phase 3: 安全配置強化 (2-3天)

1. **JWT 安全加強**
```python
# auth-service/app/security.py
JWT_ALGORITHM = "RS256"  # 使用非對稱加密
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 縮短過期時間
```

2. **Docker 安全優化**
```dockerfile
# 添加安全掃描
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    security-package-list \
    && rm -rf /var/lib/apt/lists/*

# 使用非特權用戶
USER 1001:1001
```

3. **CORS 安全配置**
```python
# 嚴格的 CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 明確指定域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## 🛡️ 安全檢查清單

### 即時檢查
- [ ] 更新所有 Critical 和 High 風險依賴
- [ ] 測試所有微服務功能正常
- [ ] 運行完整測試套件
- [ ] 檢查 API 端點安全性

### 持續監控
- [ ] 設置 Dependabot 自動更新
- [ ] 集成 Snyk/Trivy 掃描到 CI/CD
- [ ] 建立安全事件響應流程
- [ ] 定期安全審查 (每月)

## 📊 修復優先級

### 🔴 Critical (立即修復)
1. `requests` CVE-2024-47081 - 憑證洩漏
2. `Pillow` CVE-2023-50447 - 任意代碼執行
3. `aiohttp` CVE-2024-52304 - HTTP 請求走私

### 🟠 High (本週修復)  
1. `FastAPI` multipart 漏洞
2. `SvelteKit` XSS 漏洞
3. `esbuild` 開發服務器問題

### 🟡 Medium (兩週內修復)
1. 其餘 Pillow DoS 漏洞
2. aiohttp 快取污染
3. Cookie 邊界問題

## 🔧 自動化工具配置

### GitHub Actions 安全掃描
```yaml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
      - name: Python security check
        run: |
          pip install safety
          safety scan
```

### 依賴更新自動化
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/services"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
  
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
```

## 📈 長期安全策略

1. **Zero Trust 架構** - 服務間認證
2. **密鑰輪換** - 定期更新 JWT 密鑰
3. **監控告警** - 異常行為檢測
4. **備份加密** - 敏感資料保護
5. **合規審查** - GDPR/SOC2 準備

## 🆘 緊急聯絡

如遇安全事件：
1. 立即隔離受影響系統
2. 記錄事件詳情
3. 通知相關團隊
4. 啟動恢復程序

---
最後更新：2025-08-02
負責人：DevSecOps Team