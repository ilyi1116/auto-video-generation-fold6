#!/usr/bin/env python3
"""
CI/CD 配置验证脚本
验证 GitHub Actions 工作流程配置的正确性
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

class CICDValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """运行所有验证检查"""
        print("🔍 开始 CI/CD 配置验证...")
        
        # 验证项目结构
        self.validate_project_structure()
        
        # 验证工作流程文件
        self.validate_workflow_files()
        
        # 验证微服务结构
        self.validate_microservices()
        
        # 验证依赖配置
        self.validate_dependencies()
        
        # 验证 Docker 配置
        self.validate_docker_configs()
        
        # 生成报告
        self.generate_report()
        
        return len(self.errors) == 0
    
    def validate_project_structure(self):
        """验证项目结构"""
        print("📁 验证项目结构...")
        
        required_paths = [
            "src/services",
            "src/frontend", 
            "src/shared",
            "src/config",
            "infra/k8s",
            "infra/docker",
            "scripts",
            "tests",
            ".github/workflows"
        ]
        
        for path in required_paths:
            full_path = self.project_root / path
            if not full_path.exists():
                self.warnings.append(f"推荐路径不存在: {path}")
        
        # 检查关键文件
        key_files = [
            "pyproject.toml",
            "docker-compose.unified.yml",
            "alembic.ini"
        ]
        
        for file in key_files:
            file_path = self.project_root / file
            if not file_path.exists():
                self.errors.append(f"关键文件缺失: {file}")
    
    def validate_workflow_files(self):
        """验证工作流程文件"""
        print("⚙️ 验证工作流程文件...")
        
        if not self.workflows_dir.exists():
            self.errors.append("GitHub Actions 工作流程目录不存在")
            return
        
        workflow_files = list(self.workflows_dir.glob("*.yml"))
        if not workflow_files:
            self.errors.append("没有找到工作流程文件")
            return
        
        for workflow_file in workflow_files:
            self.validate_single_workflow(workflow_file)
    
    def validate_single_workflow(self, workflow_file: Path):
        """验证单个工作流程文件"""
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
            
            # 检查必需的字段
            if 'name' not in workflow:
                self.warnings.append(f"{workflow_file.name}: 缺少工作流程名称")
            
            if 'on' not in workflow:
                self.errors.append(f"{workflow_file.name}: 缺少触发条件")
            
            if 'jobs' not in workflow:
                self.errors.append(f"{workflow_file.name}: 缺少作业定义")
                return
            
            # 检查路径引用
            self.validate_workflow_paths(workflow_file.name, workflow)
            
        except yaml.YAMLError as e:
            self.errors.append(f"{workflow_file.name}: YAML 语法错误 - {e}")
        except Exception as e:
            self.errors.append(f"{workflow_file.name}: 验证失败 - {e}")
    
    def validate_workflow_paths(self, filename: str, workflow: Dict[Any, Any]):
        """验证工作流程中的路径引用"""
        workflow_str = yaml.dump(workflow)
        
        # 检查过时的路径引用
        outdated_paths = [
            "frontend/",
            "services/",
            "requirements.txt"
        ]
        
        for path in outdated_paths:
            if path in workflow_str:
                self.warnings.append(f"{filename}: 包含过时的路径引用 '{path}'")
        
        # 检查推荐的路径引用
        if filename == "ci-cd-main.yml":
            recommended_paths = [
                "src/services/",
                "src/frontend/",
                "pyproject.toml"
            ]
            
            for path in recommended_paths:
                if path not in workflow_str:
                    self.warnings.append(f"{filename}: 缺少推荐的路径引用 '{path}'")
    
    def validate_microservices(self):
        """验证微服务结构"""
        print("🔧 验证微服务结构...")
        
        services_dir = self.project_root / "src" / "services"
        if not services_dir.exists():
            self.errors.append("微服务目录 src/services 不存在")
            return
        
        services = [d for d in services_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if not services:
            self.warnings.append("没有找到微服务")
            return
        
        print(f"发现 {len(services)} 个微服务")
        
        for service in services:
            self.validate_single_service(service)
    
    def validate_single_service(self, service_path: Path):
        """验证单个微服务"""
        service_name = service_path.name
        
        # 检查 Dockerfile
        dockerfile = service_path / "Dockerfile"
        if not dockerfile.exists():
            self.warnings.append(f"微服务 {service_name} 缺少 Dockerfile")
        
        # 检查应用目录
        app_dir = service_path / "app"
        if not app_dir.exists():
            self.warnings.append(f"微服务 {service_name} 缺少 app 目录")
        else:
            # 检查主入口文件
            main_file = app_dir / "main.py"
            if not main_file.exists():
                self.warnings.append(f"微服务 {service_name} 缺少 main.py")
        
        # 检查测试目录
        tests_dir = service_path / "tests"
        if not tests_dir.exists():
            self.warnings.append(f"微服务 {service_name} 缺少测试目录")
        
        # 检查依赖文件
        req_files = [
            "requirements.txt",
            "requirements-dev.txt"
        ]
        
        for req_file in req_files:
            if not (service_path / req_file).exists():
                self.warnings.append(f"微服务 {service_name} 缺少 {req_file}")
    
    def validate_dependencies(self):
        """验证依赖配置"""
        print("📦 验证依赖配置...")
        
        # 检查 pyproject.toml
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    pyproject = tomllib.load(f)
                
                # 检查必需的部分
                if 'project' not in pyproject:
                    self.errors.append("pyproject.toml 缺少 [project] 部分")
                
                if 'project' in pyproject and 'dependencies' not in pyproject['project']:
                    self.warnings.append("pyproject.toml 缺少依赖定义")
                
                # 检查开发依赖
                if 'project' in pyproject and 'optional-dependencies' not in pyproject['project']:
                    self.warnings.append("pyproject.toml 缺少可选依赖定义")
                
            except Exception as e:
                self.errors.append(f"pyproject.toml 解析失败: {e}")
        
        # 检查前端依赖
        frontend_dir = self.project_root / "src" / "frontend"
        if frontend_dir.exists():
            package_json = frontend_dir / "package.json"
            if not package_json.exists():
                self.errors.append("前端缺少 package.json")
            else:
                try:
                    with open(package_json, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                    
                    if 'scripts' not in package_data:
                        self.warnings.append("package.json 缺少 scripts 定义")
                    
                    required_scripts = ['build', 'test', 'lint']
                    missing_scripts = [s for s in required_scripts if s not in package_data.get('scripts', {})]
                    if missing_scripts:
                        self.warnings.append(f"package.json 缺少必需的脚本: {missing_scripts}")
                
                except Exception as e:
                    self.errors.append(f"package.json 解析失败: {e}")
    
    def validate_docker_configs(self):
        """验证 Docker 配置"""
        print("🐳 验证 Docker 配置...")
        
        # 检查 docker-compose 文件
        compose_files = [
            "docker-compose.yml",
            "docker-compose.unified.yml"
        ]
        
        found_compose = False
        for compose_file in compose_files:
            compose_path = self.project_root / compose_file
            if compose_path.exists():
                found_compose = True
                try:
                    with open(compose_path, 'r', encoding='utf-8') as f:
                        compose_data = yaml.safe_load(f)
                    
                    if 'services' not in compose_data:
                        self.errors.append(f"{compose_file}: 缺少服务定义")
                    
                    # 检查常见服务
                    if 'services' in compose_data:
                        services = compose_data['services']
                        recommended_services = ['postgres', 'redis']
                        for service in recommended_services:
                            if service not in services:
                                self.warnings.append(f"{compose_file}: 缺少推荐服务 {service}")
                
                except Exception as e:
                    self.errors.append(f"{compose_file}: 解析失败 - {e}")
        
        if not found_compose:
            self.warnings.append("没有找到 docker-compose 配置文件")
    
    def check_git_hooks(self):
        """检查 Git hooks 配置"""
        print("🪝 检查 Git hooks 配置...")
        
        pre_commit_config = self.project_root / ".pre-commit-config.yaml"
        if pre_commit_config.exists():
            try:
                with open(pre_commit_config, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                if 'repos' in config:
                    print(f"✅ 找到 {len(config['repos'])} 个 pre-commit hooks")
                else:
                    self.warnings.append("pre-commit 配置文件格式不正确")
            
            except Exception as e:
                self.errors.append(f"pre-commit 配置解析失败: {e}")
        else:
            self.warnings.append("缺少 pre-commit 配置文件")
    
    def generate_report(self):
        """生成验证报告"""
        print("\n" + "="*60)
        print("📊 CI/CD 配置验证报告")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️ 发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 所有检查都通过了！")
        elif not self.errors:
            print("\n✅ 配置基本正确，但有一些优化建议")
        else:
            print("\n❌ 配置存在问题，需要修复")
        
        print("\n" + "="*60)
        
        # 生成改进建议
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """生成改进建议"""
        print("💡 改进建议:")
        
        recommendations = [
            "1. 确保所有微服务都有完整的测试覆盖",
            "2. 定期更新依赖以修复安全漏洞",
            "3. 使用 pre-commit hooks 确保代码质量",
            "4. 监控 CI/CD 流程的性能和可靠性",
            "5. 定期审查和优化 Docker 镜像大小",
            "6. 实施蓝绿部署或金丝雀部署策略",
            "7. 设置性能基准测试和监控",
            "8. 配置自动化的安全扫描"
        ]
        
        for rec in recommendations:
            print(f"   {rec}")
    
    def validate_github_secrets(self):
        """验证 GitHub Secrets 配置"""
        print("🔐 验证 GitHub Secrets 配置...")
        
        required_secrets = [
            "SNYK_TOKEN",
            "SEMGREP_APP_TOKEN", 
            "KUBE_CONFIG"
        ]
        
        print("请确保在 GitHub 仓库设置中配置了以下 Secrets:")
        for secret in required_secrets:
            print(f"   - {secret}")

def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    validator = CICDValidator(project_root)
    
    # 运行验证
    success = validator.validate_all()
    
    # 额外检查
    validator.check_git_hooks()
    validator.validate_github_secrets()
    
    # 返回适当的退出代码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()