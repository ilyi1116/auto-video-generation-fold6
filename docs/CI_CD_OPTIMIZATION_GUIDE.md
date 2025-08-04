# CI/CD 优化指南

## 概述

本文档描述了为适应新的 `src/` 项目结构而优化的 GitHub Actions CI/CD 工作流程。优化后的流程包含自动化微服务发现、性能监控、安全扫描和零停机部署策略。

## 🚀 主要改进

### 1. 项目结构适配
- ✅ 更新所有路径引用从 `services/` 到 `src/services/`
- ✅ 更新前端路径从 `frontend/` 到 `src/frontend/`
- ✅ 支持新的 `pyproject.toml` 依赖管理
- ✅ 适配新的测试结构 `src/services/*/tests`

### 2. 智能微服务构建
- ✅ **动态服务发现**：自动发现所有包含 Dockerfile 的微服务
- ✅ **并行构建**：微服务和前端并行构建，提升效率
- ✅ **缓存优化**：每个服务独立缓存，减少构建时间
- ✅ **多架构支持**：支持 linux/amd64 和 linux/arm64

### 3. 增强的安全扫描
- ✅ **多层安全检查**：CodeQL、Snyk、Safety、Bandit、Semgrep
- ✅ **容器安全扫描**：Trivy 扫描基础镜像和构建的容器
- ✅ **依赖监控**：定期检查依赖更新和安全漏洞
- ✅ **SARIF 报告**：统一的安全报告格式

### 4. 性能监控
- ✅ **API 性能基准测试**：自动化 API 响应时间和成功率测试
- ✅ **前端性能测试**：Lighthouse 性能评分
- ✅ **负载测试**：Locust 压力测试
- ✅ **性能趋势监控**：定期性能报告和警报

### 5. 生产级部署
- ✅ **零停机部署**：滚动更新策略
- ✅ **健康检查**：全面的服务健康验证
- ✅ **自动回滚**：健康检查失败时自动回滚
- ✅ **多环境支持**：development、staging、production

## 📁 工作流程文件结构

```
.github/workflows/
├── ci-cd-main.yml              # 主要 CI/CD 流程
├── dependency-security.yml     # 依赖和安全监控
├── performance-monitoring.yml  # 性能监控和基准测试
├── ci.yml                      # 基础 CI 检查
├── codeql-analysis.yml         # 代码安全分析
├── deploy-staging.yml          # 预发布部署
└── security-audit.yml          # 安全审计
```

## 🔄 工作流程详解

### 主要 CI/CD 流程 (`ci-cd-main.yml`)

#### 1. 代码质量检查 (`code-quality`)
```yaml
触发条件: 所有推送和 PR
检查内容:
- Python 代码格式化 (Black)
- Python 代码检查 (Flake8)
- Python 类型检查 (MyPy)
- Python 安全检查 (Bandit)
- 前端代码格式化 (Prettier)
- 前端代码检查 (ESLint)
- 前端类型检查 (TypeScript)
```

#### 2. 安全扫描 (`security-scan`)
```yaml
扫描工具:
- CodeQL (静态代码分析)
- Snyk (依赖漏洞扫描)
- Safety (Python 安全检查)
- Semgrep (静态安全分析)
- Trivy (容器安全扫描)
```

#### 3. 测试阶段
```yaml
后端测试 (backend-tests):
- 单元测试 (pytest)
- 集成测试
- 代码覆盖率报告

前端测试 (frontend-tests):
- 单元测试 (Vitest)
- 组件测试
- 代码覆盖率报告

E2E 测试 (e2e-tests):
- 端到端功能测试
- 服务集成测试
```

#### 4. 动态服务发现 (`discover-services`)
```yaml
功能:
- 自动发现所有微服务
- 检查前端构建需求
- 生成构建矩阵
```

#### 5. 容器构建
```yaml
微服务构建 (build-microservices):
- 并行构建所有微服务
- 独立缓存策略
- 多架构支持

前端构建 (build-frontend):
- SvelteKit 应用构建
- 静态资源优化
- 容器镜像推送
```

#### 6. 部署阶段 (`deploy`)
```yaml
部署策略:
- 环境自动判断
- Docker Compose (开发/测试)
- Kubernetes (生产环境)
- 健康检查和自动回滚
```

### 依赖和安全监控 (`dependency-security.yml`)

#### 定期安全扫描
```yaml
触发时间: 每周一早上 6:00 UTC
扫描内容:
- Python 依赖安全检查
- Node.js 依赖安全检查
- 容器镜像安全扫描
- 依赖更新建议
```

#### 自动化报告
- 生成安全摘要报告
- 创建 GitHub Issues 跟踪更新
- 在提交时添加安全评论

### 性能监控 (`performance-monitoring.yml`)

#### 性能基准测试
```yaml
API 性能测试:
- 响应时间基准 (< 2秒)
- 成功率基准 (> 95%)
- 并发测试
- 负载测试

前端性能测试:
- Lighthouse 评分 (> 80)
- 首次内容绘制时间
- 最大内容绘制时间
- 累计布局偏移
```

#### 负载测试
- Locust 压力测试
- 并发用户模拟
- 性能瓶颈识别

## 🛠️ 使用指南

### 1. 基本工作流程

#### 开发阶段
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和提交
git add .
git commit -m "feat: 添加新功能"

# 3. 推送并创建 PR
git push origin feature/new-feature
```

这将触发：
- 代码质量检查
- 安全扫描
- 单元测试
- 前端测试

#### 部署到 Staging
```bash
# 合并到 develop 分支
git checkout develop
git merge feature/new-feature
git push origin develop
```

这将触发：
- 完整的 CI/CD 流程
- 容器构建
- 部署到 staging 环境
- E2E 测试

#### 生产部署
```bash
# 合并到 main 分支
git checkout main
git merge develop
git push origin main
```

这将触发：
- 完整的 CI/CD 流程
- 生产容器构建
- Kubernetes 部署
- 健康检查和监控

### 2. 手动触发工作流程

#### 手动部署
```yaml
# 在 GitHub Actions 页面手动触发
workflow_dispatch:
  inputs:
    environment: production  # 或 staging, development
    skip_tests: false
```

#### 手动安全扫描
```yaml
# 在 GitHub Actions 页面手动触发
workflow_dispatch:
  inputs:
    scan_type: full  # 或 dependencies-only, containers-only
```

#### 手动性能测试
```yaml
# 在 GitHub Actions 页面手动触发
workflow_dispatch:
  inputs:
    test_type: full      # 或 api-only, frontend-only, load-test
    duration: "10"       # 测试持续时间(分钟)
```

### 3. 环境变量配置

#### 必需的 GitHub Secrets
```yaml
# 容器注册表
GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # 自动提供

# 安全扫描
SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}      # Snyk API Token
SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}  # Semgrep Token

# Kubernetes 部署 (生产环境)
KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}    # Base64 编码的 kubeconfig

# 数据库 (测试环境)
DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
REDIS_URL: redis://localhost:6379/0
```

#### 环境配置文件
```bash
# development
config/environments/development.env

# staging  
config/environments/staging.env

# production
config/environments/production.env
```

## 📊 监控和报告

### 1. 代码质量指标
- 代码覆盖率 (目标: > 80%)
- 代码质量评分
- 安全漏洞数量
- 依赖健康状况

### 2. 性能指标
- API 响应时间 (目标: < 2秒)
- API 成功率 (目标: > 95%)
- 前端 Lighthouse 评分 (目标: > 80)
- 负载测试结果

### 3. 部署指标
- 部署成功率
- 部署时间
- 回滚频率
- 健康检查成功率

### 4. 安全指标
- 安全漏洞数量趋势
- 依赖更新及时性
- 安全扫描覆盖率

## 🔧 故障排除

### 常见问题

#### 1. 微服务发现失败
```bash
# 检查微服务是否有 Dockerfile
find src/services -name Dockerfile

# 确保服务目录结构正确
src/services/service-name/Dockerfile
```

#### 2. 构建缓存问题
```bash
# 清理 GitHub Actions 缓存
# 在 GitHub 仓库设置 > Actions > Caches 中手动清理
```

#### 3. 测试失败
```bash
# 本地运行测试
pytest src/services/*/tests -v
npm test --prefix src/frontend
```

#### 4. 部署健康检查失败
```bash
# 检查服务健康端点
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health

# 查看服务日志
docker-compose -f docker-compose.unified.yml logs
```

### 性能优化建议

#### 1. 构建优化
- 使用多阶段 Docker 构建
- 启用 BuildKit 缓存
- 并行构建微服务

#### 2. 测试优化
- 使用测试数据缓存
- 并行运行测试
- 智能测试选择

#### 3. 部署优化
- 蓝绿部署策略
- 预热新版本
- 渐进式流量切换

## 📈 未来改进计划

### 短期 (1-2个月)
- [ ] 添加更多性能指标监控
- [ ] 实现自动化依赖更新
- [ ] 增加更多安全扫描工具
- [ ] 优化构建缓存策略

### 中期 (3-6个月)
- [ ] 实现渐进式部署
- [ ] 添加 A/B 测试支持
- [ ] 集成外部监控工具
- [ ] 实现自动化回滚策略

### 长期 (6个月以上)
- [ ] 实现 GitOps 工作流程
- [ ] 添加多云部署支持
- [ ] 集成 AI 驱动的性能优化
- [ ] 实现自愈系统

## 📚 参考资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes 部署指南](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [安全扫描工具比较](https://owasp.org/www-community/Source_Code_Analysis_Tools)
- [性能测试最佳实践](https://martinfowler.com/articles/practical-test-pyramid.html)

---

## 总结

优化后的 CI/CD 工作流程提供了：

✅ **完全适配新项目结构**  
✅ **自动化微服务管理**  
✅ **全面的安全保障**  
✅ **持续的性能监控**  
✅ **生产级部署策略**  
✅ **零停机部署能力**  

这些改进确保了项目的可维护性、安全性和可扩展性，为团队提供了现代化的 DevOps 工作流程。