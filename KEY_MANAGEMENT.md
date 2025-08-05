# 🔐 生產級密鑰管理方案

## 概述

本文檔說明 AutoVideo 系統在生產環境中的密鑰管理策略，涵蓋 Kubernetes、HashiCorp Vault 和雲端密鑰管理服務的最佳實踐。

## 📋 目錄

1. [現有密鑰管理現狀](#現有密鑰管理現狀)
2. [生產級密鑰管理架構](#生產級密鑰管理架構)
3. [Kubernetes Secrets 管理](#kubernetes-secrets-管理)
4. [HashiCorp Vault 整合](#hashicorp-vault-整合)
5. [雲端平台密鑰管理](#雲端平台密鑰管理)
6. [密鑰輪換策略](#密鑰輪換策略)
7. [安全最佳實踐](#安全最佳實踐)
8. [故障排除指南](#故障排除指南)

## 現有密鑰管理現狀

### 📁 當前文件結構
```
myProject/
├── .env.production          # 生產環境配置範本
├── .env.development        # 開發環境配置
├── .env.template           # 配置範本
├── scripts/
│   └── generate_production_keys.sh  # 密鑰生成腳本
└── keys/                   # 生成的密鑰文件 (本地)
    ├── production/
    ├── staging/
    └── development/
```

### 🔑 密鑰類型分析

| 密鑰類型 | 當前方案 | 安全級別 | 改善建議 |
|---------|---------|---------|---------|
| JWT 密鑰 | RSA 2048 + 環境變數 | ⚠️ 中等 | 使用 Kubernetes Secrets |
| 資料庫密碼 | 32位隨機生成 + 環境變數 | ⚠️ 中等 | 使用密鑰管理服務 |
| API 密鑰 | 手動設置環境變數 | ❌ 低 | 自動輪換 + 加密存儲 |
| 加密密鑰 | 隨機生成 + 本地文件 | ❌ 低 | 硬體安全模組 (HSM) |

## 生產級密鑰管理架構

### 🏗️ 三層架構設計

```mermaid
graph TB
    A[應用程式層] --> B[密鑰代理層]
    B --> C[密鑰存儲層]
    
    subgraph "應用程式層"
        A1[API Gateway]
        A2[Auth Service]
        A3[AI Service]
    end
    
    subgraph "密鑰代理層"
        B1[Kubernetes Secrets]
        B2[Vault Agent]
        B3[CSI Secret Store]
    end
    
    subgraph "密鑰存儲層"
        C1[HashiCorp Vault]
        C2[AWS Secrets Manager]
        C3[Azure Key Vault]
        C4[GCP Secret Manager]
    end
```

### 🔄 密鑰生命週期管理

```mermaid
sequenceDiagram
    participant App as 應用程式
    participant K8s as Kubernetes
    participant Vault as HashiCorp Vault
    participant HSM as 硬體安全模組
    
    Note over App,HSM: 密鑰初始化
    Vault->>HSM: 生成根密鑰
    Vault->>Vault: 創建密鑰策略
    
    Note over App,HSM: 密鑰注入
    App->>K8s: 請求密鑰
    K8s->>Vault: 獲取密鑰
    Vault->>K8s: 返回加密密鑰
    K8s->>App: 注入環境變數
    
    Note over App,HSM: 密鑰輪換
    Vault->>HSM: 生成新密鑰
    Vault->>K8s: 更新 Secret
    K8s->>App: 重載配置
```

## Kubernetes Secrets 管理

### 🚀 基礎 Secret 創建

```yaml
# config/k8s/secrets/jwt-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: jwt-secrets
  namespace: autovideo-prod
type: Opaque
data:
  # Base64 編碼的 RSA 私鑰
  jwt-private-key: LS0tLS1CRUdJTi...
  # Base64 編碼的 RSA 公鑰  
  jwt-public-key: LS0tLS1CRUdJTi...
---
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: autovideo-prod
type: Opaque
stringData:
  postgres-password: "YOUR_GENERATED_PASSWORD"
  redis-password: "YOUR_GENERATED_PASSWORD"
  postgres-url: "postgresql://user:pass@host:5432/db"
---
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: autovideo-prod
type: Opaque
stringData:
  openai-api-key: "sk-..."
  gemini-api-key: "..."
  suno-api-key: "..."
  anthropic-api-key: "..."
```

### 🔒 增強型 Secret 配置

```yaml
# config/k8s/secrets/sealed-secrets.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: production-secrets
  namespace: autovideo-prod
spec:
  encryptedData:
    # 使用 Sealed Secrets 加密
    jwt-secret: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
    db-password: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
  template:
    metadata:
      name: production-secrets
      namespace: autovideo-prod
    type: Opaque
```

### 📦 Secret Store CSI Driver

```yaml
# config/k8s/secrets/secret-provider-class.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-secrets
  namespace: autovideo-prod
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.company.com:8200"
    roleName: "autovideo-prod-role"
    objects: |
      - objectName: "jwt-private-key"
        secretPath: "secret/autovideo/prod/jwt"
        secretKey: "private-key"
      - objectName: "jwt-public-key"  
        secretPath: "secret/autovideo/prod/jwt"
        secretKey: "public-key"
      - objectName: "postgres-password"
        secretPath: "secret/autovideo/prod/database"
        secretKey: "postgres-password"
  secretObjects:
  - secretName: vault-secrets
    type: Opaque
    data:
    - objectName: jwt-private-key
      key: jwt-private-key
    - objectName: jwt-public-key
      key: jwt-public-key
    - objectName: postgres-password
      key: postgres-password
```

### 🚢 Pod 中使用 Secrets

```yaml
# config/k8s/deployments/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: autovideo-prod
spec:
  template:
    spec:
      containers:
      - name: api-gateway
        image: autovideo/api-gateway:latest
        env:
        # 從 Secret 注入環境變數
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secrets
              key: jwt-private-key
        - name: JWT_PUBLIC_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secrets
              key: jwt-public-key
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: postgres-password
        # 掛載 Secret 為文件
        volumeMounts:
        - name: vault-secrets
          mountPath: "/etc/secrets"
          readOnly: true
      volumes:
      - name: vault-secrets
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: "vault-secrets"
```

## HashiCorp Vault 整合

### 🏛️ Vault 架構配置

```hcl
# config/vault/autovideo-policy.hcl
# AutoVideo 生產環境密鑰策略
path "secret/data/autovideo/prod/*" {
  capabilities = ["read"]
}

path "secret/data/autovideo/staging/*" {
  capabilities = ["read", "create", "update"]
}

path "database/creds/autovideo-prod" {
  capabilities = ["read"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
```

```hcl
# config/vault/kubernetes-auth.hcl
# Kubernetes 認證配置
auth "kubernetes" {
  type = "kubernetes"
}

resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
}

resource "vault_kubernetes_auth_backend_config" "kubernetes" {
  backend         = vault_auth_backend.kubernetes.path
  kubernetes_host = "https://kubernetes.default.svc:443"
}

resource "vault_kubernetes_auth_backend_role" "autovideo_prod" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "autovideo-prod-role"
  bound_service_account_names      = ["autovideo-prod"]
  bound_service_account_namespaces = ["autovideo-prod"]
  token_ttl                        = 3600
  token_policies                   = ["autovideo-prod-policy"]
}
```

### 🔑 動態密鑰生成

```hcl
# config/vault/database-secrets.hcl
# 動態資料庫憑證
resource "vault_database_secrets_mount" "postgres" {
  path = "database"
  
  postgresql {
    name           = "autovideo-prod-db"
    plugin_name    = "postgresql-database-plugin"
    connection_url = "postgresql://{{username}}:{{password}}@postgres:5432/autovideo?sslmode=require"
    username       = "vault"
    password       = "vault-password"
  }
}

resource "vault_database_secret_backend_role" "autovideo_prod" {
  backend     = vault_database_secrets_mount.postgres.path
  name        = "autovideo-prod"
  db_name     = "autovideo-prod-db"
  default_ttl = 3600
  max_ttl     = 7200
  
  creation_statements = [
    "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";"
  ]
}
```

### 🤖 Vault Agent 配置

```hcl
# config/vault/vault-agent.hcl
pid_file = "/var/run/vault-agent.pid"

vault {
  address = "https://vault.company.com:8200"
}

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "autovideo-prod-role"
    }
  }
  
  sink "file" {
    config = {
      path = "/var/run/secrets/vault-token"
    }
  }
}

template {
  source      = "/etc/vault/templates/secrets.env.tpl"
  destination = "/etc/secrets/secrets.env"
}

template {
  source      = "/etc/vault/templates/jwt-private.pem.tpl"
  destination = "/etc/secrets/jwt-private.pem"
  perms       = 0600
}
```

## 雲端平台密鑰管理

### ☁️ AWS Secrets Manager

```yaml
# config/k8s/external-secrets/aws-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: autovideo-prod
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: autovideo-secrets
  namespace: autovideo-prod
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: autovideo-secrets
    creationPolicy: Owner
  data:
  - secretKey: jwt-private-key
    remoteRef:
      key: autovideo/prod/jwt
      property: private-key
  - secretKey: openai-api-key
    remoteRef:
      key: autovideo/prod/api-keys
      property: openai-key
```

### 🔷 Azure Key Vault

```yaml
# config/k8s/external-secrets/azure-keyvault.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: azure-keyvault
  namespace: autovideo-prod
spec:
  provider:
    azurekv:
      vaultUrl: "https://autovideo-prod-kv.vault.azure.net/"
      authType: ManagedIdentity
      identityId: "/subscriptions/.../resourceGroups/.../providers/Microsoft.ManagedIdentity/userAssignedIdentities/autovideo-prod-identity"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: azure-secrets
  namespace: autovideo-prod
spec:
  refreshInterval: 30m
  secretStoreRef:
    name: azure-keyvault
    kind: SecretStore
  target:
    name: azure-secrets
  data:
  - secretKey: postgres-password
    remoteRef:
      key: postgres-password
  - secretKey: redis-password
    remoteRef:
      key: redis-password
```

### 🟡 Google Secret Manager

```yaml
# config/k8s/external-secrets/gcp-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-manager
  namespace: autovideo-prod
spec:
  provider:
    gcpsm:
      projectId: "autovideo-prod-123456789"
      auth:
        workloadIdentity:
          clusterLocation: us-central1-a
          clusterName: autovideo-prod-cluster
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: gcp-secrets
  namespace: autovideo-prod
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: gcp-secret-manager
    kind: SecretStore
  target:
    name: gcp-secrets
  data:
  - secretKey: gemini-api-key
    remoteRef:
      key: gemini-api-key
      version: latest
  - secretKey: anthropic-api-key
    remoteRef:
      key: anthropic-api-key
      version: latest
```

## 密鑰輪換策略

### 🔄 自動化輪換流程

```yaml
# config/k8s/cronjobs/key-rotation.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: jwt-key-rotation
  namespace: autovideo-prod
spec:
  # 每 90 天執行一次
  schedule: "0 2 1 */3 *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: key-rotator
            image: autovideo/key-rotator:latest
            env:
            - name: VAULT_ADDR
              value: "https://vault.company.com:8200"
            - name: ROTATION_TYPE
              value: "jwt"
            command:
            - /bin/sh
            - -c
            - |
              # 生成新的 JWT 密鑰對
              openssl genrsa -out /tmp/jwt-private-new.pem 2048
              openssl rsa -in /tmp/jwt-private-new.pem -pubout -out /tmp/jwt-public-new.pem
              
              # 更新 Vault 中的密鑰
              vault kv put secret/autovideo/prod/jwt-new \
                private-key=@/tmp/jwt-private-new.pem \
                public-key=@/tmp/jwt-public-new.pem
              
              # 觸發應用程式重新載入
              kubectl rollout restart deployment/api-gateway
              kubectl rollout restart deployment/auth-service
          restartPolicy: OnFailure
```

### 📊 輪換監控

```yaml
# config/k8s/monitoring/key-rotation-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: key-rotation-monitor
  namespace: autovideo-prod
spec:
  selector:
    matchLabels:
      app: key-rotator
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: key-rotation-alerts
  namespace: autovideo-prod
spec:
  groups:
  - name: key-rotation
    rules:
    - alert: KeyRotationFailed
      expr: key_rotation_success == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "密鑰輪換失敗"
        description: "JWT 密鑰輪換在過去 5 分鐘內失敗"
    
    - alert: KeyExpiringWarning
      expr: (key_expiry_timestamp - time()) < 86400 * 7
      for: 1h
      labels: 
        severity: warning
      annotations:
        summary: "密鑰即將過期"
        description: "JWT 密鑰將在 7 天內過期，請準備輪換"
```

## 安全最佳實踐

### 🛡️ 密鑰安全檢查清單

#### ✅ 基礎安全要求
- [ ] 使用硬體安全模組 (HSM) 或雲端 HSM 生成根密鑰
- [ ] 啟用靜態加密 (Encryption at Rest)
- [ ] 啟用傳輸加密 (Encryption in Transit)
- [ ] 實施最小權限原則 (Principle of Least Privilege)
- [ ] 啟用詳細的審計日誌記錄
- [ ] 設置密鑰使用監控和告警

#### ✅ Kubernetes 安全配置
- [ ] 使用 RBAC 限制 Secret 訪問權限
- [ ] 啟用 Pod Security Standards
- [ ] 使用 Network Policies 限制網路訪問
- [ ] 實施 Admission Controllers 驗證配置
- [ ] 定期掃描容器鏡像漏洞
- [ ] 使用 Service Mesh 加密服務間通訊

#### ✅ 運維安全措施
- [ ] 實施多人審批流程 (4-eyes principle)
- [ ] 建立密鑰洩露應急響應計劃
- [ ] 定期進行安全滲透測試
- [ ] 設置自動化合規檢查
- [ ] 維護完整的密鑰清單和所有者記錄
- [ ] 實施定期安全培訓

### 🔐 密鑰分類與保護級別

| 密鑰類型 | 保護級別 | 存儲方式 | 輪換頻率 | 訪問控制 |
|---------|---------|---------|---------|---------|
| 根密鑰 | 🔴 極高 | HSM | 年度 | 多人授權 |
| JWT 簽名密鑰 | 🟠 高 | Vault + K8s Secrets | 季度 | 服務帳戶 |
| 資料庫密碼 | 🟠 高 | 動態生成 | 日/週 | 應用程式 |
| API 密鑰 | 🟡 中等 | 密鑰管理服務 | 月度 | 服務綁定 |
| 會話密鑰 | 🟡 中等 | 記憶體 | 小時 | 用戶綁定 |
| 開發環境密鑰 | 🟢 低 | 本地文件 | 手動 | 開發團隊 |

### 🚨 安全事件響應流程

```mermaid
flowchart TD
    A[密鑰洩露檢測] --> B{評估洩露範圍}
    B -->|限制| C[立即撤銷密鑰]
    B -->|廣泛| D[啟動緊急響應程序]
    
    C --> E[生成新密鑰]
    D --> F[通知安全團隊]
    
    E --> G[更新所有服務]
    F --> G
    
    G --> H[驗證服務正常]
    H --> I[完成事件報告]
    
    I --> J[更新安全策略]
```

## 故障排除指南

### 🔧 常見問題及解決方案

#### 問題 1: Kubernetes Secret 無法掛載
```bash
# 檢查 Secret 是否存在
kubectl get secrets -n autovideo-prod

# 檢查 Secret 內容
kubectl describe secret jwt-secrets -n autovideo-prod

# 檢查 Pod 事件
kubectl describe pod <pod-name> -n autovideo-prod

# 解決方案: 確保 Secret 名稱和命名空間正確
kubectl create secret generic jwt-secrets \
  --from-file=jwt-private-key=./keys/production/jwt-private.pem \
  --from-file=jwt-public-key=./keys/production/jwt-public.pem \
  -n autovideo-prod
```

#### 問題 2: Vault 認證失敗
```bash
# 檢查 Vault 服務狀態
kubectl logs -l app=vault -n vault-system

# 檢查 Kubernetes 認證配置
vault auth -method=kubernetes role=autovideo-prod-role jwt=$SA_JWT_TOKEN

# 檢查服務帳戶權限
kubectl auth can-i get secrets --as=system:serviceaccount:autovideo-prod:autovideo-prod

# 解決方案: 更新 ServiceAccount 和 RoleBinding
kubectl apply -f config/k8s/rbac/vault-auth.yaml
```

#### 問題 3: 密鑰輪換後服務無法啟動
```bash
# 檢查新密鑰格式
openssl rsa -in keys/production/jwt-private-new.pem -check

# 驗證密鑰配對
diff <(openssl rsa -in jwt-private.pem -pubout) jwt-public.pem

# 檢查應用程式日誌
kubectl logs deployment/api-gateway -n autovideo-prod

# 解決方案: 逐步重啟服務並驗證
kubectl rollout restart deployment/api-gateway -n autovideo-prod
kubectl rollout status deployment/api-gateway -n autovideo-prod
```

### 📈 監控和告警配置

```yaml
# config/monitoring/key-management-alerts.yaml
groups:
- name: key-management
  rules:
  - alert: SecretMountFailed
    expr: kube_pod_container_status_restarts_total{container=~".*autovideo.*"} > 5
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Secret 掛載失敗導致容器重啟"
      
  - alert: VaultUnsealed
    expr: vault_core_unsealed == 0
    for: 30s
    labels:
      severity: critical
    annotations:
      summary: "Vault 已密封，無法訪問密鑰"
      
  - alert: KeyRotationDue
    expr: (cert_expiry_timestamp - time()) < 86400 * 30
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "密鑰將在 30 天內過期"
```

## 📞 支援與聯絡資訊

### 🆘 緊急聯絡方式
- **安全事件熱線**: +1-xxx-xxx-xxxx
- **DevOps 24/7 值班**: devops-oncall@autovideo.com
- **安全團隊**: security@autovideo.com

### 📚 相關文檔
- [Kubernetes 安全最佳實踐](./docs/k8s-security.md)
- [HashiCorp Vault 操作手冊](./docs/vault-operations.md)
- [應急響應程序](./docs/incident-response.md)
- [合規要求檢查清單](./docs/compliance-checklist.md)

### 🔄 更新記錄
- **2025-08-05**: 初始版本，包含完整的密鑰管理策略
- **TBD**: 計劃加入 HSM 整合和零信任架構

---

📝 **文檔版本**: v1.0  
📅 **最後更新**: 2025-08-05  
👤 **維護者**: DevOps & Security Team  
🔒 **分類**: 機密 - 僅限授權人員