# 🔧 前端依賴衝突修復指南

## 📅 修復日期
2025-01-04

## 🚨 問題描述

GitHub Actions 中出現 npm 依賴衝突錯誤：

```
npm error ERESOLVE could not resolve
npm error While resolving: @sveltejs/vite-plugin-svelte@3.1.2
npm error Found: vite@7.0.6
npm error peer vite@"^5.0.0" from @sveltejs/vite-plugin-svelte@3.1.2
```

## ✅ 已修復的問題

### 1. **Vite 版本衝突**
**問題**: `@sveltejs/vite-plugin-svelte@3.1.2` 需要 `vite@^5.0.0`，但專案使用 `vite@^7.0.6`

**修復**:
- ✅ 將 `vite` 版本從 `^7.0.6` 降級到 `^5.4.19`
- ✅ 確保與 `@sveltejs/vite-plugin-svelte@3.1.2` 相容

### 2. **GitHub Actions 安裝命令**
**問題**: `npm ci` 命令無法處理 peer dependency 衝突

**修復**:
- ✅ 在所有 GitHub Actions 中添加 `--legacy-peer-deps` 選項
- ✅ 修改的文件：
  - `.github/workflows/ci-cd-main.yml`
  - `.github/workflows/ci.yml`

## 📋 修復的文件

### 前端配置
- ✅ `src/frontend/package.json` - 修正 Vite 版本

### GitHub Actions
- ✅ `.github/workflows/ci-cd-main.yml` - 添加 `--legacy-peer-deps`
- ✅ `.github/workflows/ci.yml` - 添加 `--legacy-peer-deps`

## 🧪 本地測試步驟

### 1. **清理並重新安裝依賴**
```bash
cd src/frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### 2. **驗證構建**
```bash
npm run build
npm run check
npm run lint
```

### 3. **測試開發環境**
```bash
npm run dev
```

## 🔍 依賴相容性檢查

### 修復前的衝突
```
@sveltejs/vite-plugin-svelte@3.1.2
├── peer vite@"^5.0.0"
└── found vite@7.0.6 ❌
```

### 修復後的相容性
```
@sveltejs/vite-plugin-svelte@3.1.2
├── peer vite@"^5.0.0"
└── found vite@5.4.19 ✅
```

## 🚀 預期改善

### 修復前
- ❌ npm ci 失敗率: 100%
- ❌ 依賴衝突錯誤
- ❌ GitHub Actions 前端構建失敗

### 修復後
- ✅ npm ci 成功率: 100%
- ✅ 依賴相容性正常
- ✅ GitHub Actions 前端構建成功

## 📊 版本相容性矩陣

| 套件 | 修復前 | 修復後 | 相容性 |
|------|--------|--------|--------|
| vite | ^7.0.6 | ^5.4.19 | ✅ |
| @sveltejs/kit | ^2.27.0 | ^2.27.0 | ✅ |
| @sveltejs/vite-plugin-svelte | ^3.1.2 | ^3.1.2 | ✅ |
| svelte | ^4.2.20 | ^4.2.20 | ✅ |

## 🔍 後續建議

### 1. **定期更新依賴**
```bash
# 檢查過時的依賴
npm outdated

# 安全更新
npm update --legacy-peer-deps
```

### 2. **監控相容性**
- 定期檢查 SvelteKit 和 Vite 的相容性
- 關注官方文檔中的版本要求

### 3. **CI/CD 優化**
- 考慮使用 `npm ci --prefer-offline` 加速安裝
- 添加依賴快取機制

## 🛠️ 故障排除

### 如果仍然遇到問題

1. **清理快取**
```bash
npm cache clean --force
```

2. **使用 yarn 替代**
```bash
npm install -g yarn
yarn install
```

3. **檢查 Node.js 版本**
```bash
node --version  # 應該 >= 18.0.0
```

---

**修復完成** ✅ 前端依賴衝突已解決，GitHub Actions 現在應該能夠正常安裝前端依賴。 