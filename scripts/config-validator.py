#!/usr/bin/env python3
"""
配置验证工具 - 适配 Termux Android 环境

功能:
1. 项目配置文件验证 (pyproject.toml, alembic.ini)
2. 环境变量文件验证 (.env 文件)
3. Docker 配置验证 (docker-compose.yml)
4. 服务配置验证 (Dockerfile, requirements.txt)
5. 数据库配置验证 (Alembic migrations)
6. 安全配置检查 (敏感信息栖测)

作者: Claude Code
日期: 2025-08-04
"""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import toml
import yaml
from pydantic import BaseModel, Field

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationIssue(BaseModel):
    """配置验证问题模型"""
    severity: str  # critical, warning, info
    category: str  # syntax, security, compatibility, missing
    file_path: str
    line_number: Optional[int] = None
    message: str
    suggestion: Optional[str] = None
    details: Dict = Field(default_factory=dict)


class ConfigValidationResult(BaseModel):
    """配置验证结果模型"""
    file_path: str
    file_type: str
    status: str  # valid, invalid, missing
    issues: List[ValidationIssue] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfigurationValidator:
    """配置验证器"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.is_termux = self._detect_termux()
        self.results: List[ConfigValidationResult] = []
        
        # 定义需要验证的配置文件
        self.config_files = {
            "pyproject.toml": {
                "type": "toml",
                "description": "项目配置文件",
                "required": True,
                "validator": self._validate_pyproject_toml
            },
            "alembic.ini": {
                "type": "ini",
                "description": "Alembic 数据库迁移配置",
                "required": True,
                "validator": self._validate_alembic_ini
            },
            "docker-compose.yml": {
                "type": "yaml",
                "description": "Docker Compose 配置",
                "required": True,
                "validator": self._validate_docker_compose
            },
            "docker-compose.unified.yml": {
                "type": "yaml",
                "description": "统一 Docker Compose 配置",
                "required": False,
                "validator": self._validate_docker_compose
            },
            ".env": {
                "type": "env",
                "description": "环境变量文件",
                "required": False,
                "validator": self._validate_env_file
            },
            "config/environments/development.env": {
                "type": "env",
                "description": "开发环境配置",
                "required": True,
                "validator": self._validate_env_file
            },
            "config/environments/production.env": {
                "type": "env",
                "description": "生产环境配置",
                "required": False,
                "validator": self._validate_env_file
            }
        }
        
        # 定义敏感信息模式
        self.sensitive_patterns = [
            (r'password\s*=\s*["\']?[^\s"\'\\n]+', "密码可能明文存储"),
            (r'secret\s*=\s*["\']?[^\s"\'\\n]+', "秘钥可能明文存储"),
            (r'api[_-]?key\s*=\s*["\']?[^\s"\'\\n]+', "API 密钥可能明文存储"),
            (r'token\s*=\s*["\']?[^\s"\'\\n]+', "令牌可能明文存储"),
            (r'private[_-]?key', "私钥信息"),
            (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "PEM 格式私钥")
        ]
        
        logger.info(f"配置验证器初始化完成 - Termux: {self.is_termux}, 项目路径: {self.project_path}")
    
    def _detect_termux(self) -> bool:
        """检测是否在 Termux 环境中运行"""
        return (
            os.environ.get('PREFIX', '').startswith('/data/data/com.termux') or
            'termux' in os.environ.get('HOME', '').lower() or
            Path('/data/data/com.termux').exists()
        )
    
    def _add_issue(self, result: ConfigValidationResult, severity: str, category: str, 
                   message: str, line_number: Optional[int] = None, 
                   suggestion: Optional[str] = None, details: Optional[Dict] = None):
        """添加验证问题"""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            file_path=result.file_path,
            line_number=line_number,
            message=message,
            suggestion=suggestion,
            details=details or {}
        )
        result.issues.append(issue)
    
    def _read_file_safely(self, file_path: Path) -> Tuple[bool, Optional[str], Optional[str]]:
        """安全读取文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content, None
        except FileNotFoundError:
            return False, None, "文件不存在"
        except PermissionError:
            return False, None, "没有文件读取权限"
        except UnicodeDecodeError:
            return False, None, "文件编码错误，非 UTF-8 格式"
        except Exception as e:
            return False, None, f"读取文件异常: {str(e)}"
    
    def _check_sensitive_content(self, result: ConfigValidationResult, content: str):
        """检查敏感信息"""
        lines = content.split('\\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in self.sensitive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self._add_issue(
                        result, "warning", "security",
                        f"{description}: {line.strip()[:50]}...",
                        line_number=line_num,
                        suggestion="考虑使用环境变量或加密存储敏感信息",
                        details={"pattern": pattern, "matched_line": line.strip()}
                    )
    
    def _validate_pyproject_toml(self, file_path: Path, content: str) -> ConfigValidationResult:
        """验证 pyproject.toml 文件"""
        result = ConfigValidationResult(
            file_path=str(file_path),
            file_type="toml",
            status="valid"
        )
        
        try:
            # 解析 TOML 文件
            config = toml.loads(content)
            result.metadata["parsed_config"] = True
            
            # 检查必要的节
            required_sections = ['build-system', 'project']
            for section in required_sections:
                if section not in config:
                    self._add_issue(
                        result, "warning", "missing",
                        f"缺少必要的节: [{section}]",
                        suggestion=f"添加 [{section}] 节到 pyproject.toml"
                    )
            
            # 检查项目信息
            if 'project' in config:
                project = config['project']
                
                # 检查必要字段
                required_fields = ['name', 'version', 'description']
                for field in required_fields:
                    if field not in project:
                        self._add_issue(
                            result, "warning", "missing",
                            f"项目信息中缺少 {field} 字段"
                        )
                
                # 检查依赖
                if 'dependencies' in project:
                    deps = project['dependencies']
                    result.metadata["dependency_count"] = len(deps)
                    
                    # 检查是否有常见的安全问题依赖
                    problematic_deps = []
                    for dep in deps:
                        if isinstance(dep, str):
                            dep_name = dep.split('==')[0].split('>=')[0].split('<=')[0].strip()
                            # 这里可以添加已知的问题依赖检查
                            if 'insecure' in dep_name.lower():
                                problematic_deps.append(dep_name)
                    
                    if problematic_deps:
                        self._add_issue(
                            result, "warning", "security",
                            f"可能不安全的依赖: {', '.join(problematic_deps)}"
                        )
            
            # 检查构建系统
            if 'build-system' in config:
                build_system = config['build-system']
                if 'requires' not in build_system:
                    self._add_issue(
                        result, "warning", "missing",
                        "构建系统中缺少 requires 字段"
                    )
            
        except toml.TomlDecodeError as e:
            result.status = "invalid"
            self._add_issue(
                result, "critical", "syntax",
                f"TOML 语法错误: {str(e)}",
                suggestion="检查 TOML 语法是否正确"
            )
        except Exception as e:
            result.status = "invalid"
            self._add_issue(
                result, "critical", "syntax",
                f"解析文件失败: {str(e)}"
            )
        
        # 检查敏感信息
        self._check_sensitive_content(result, content)
        
        return result
    
    def _validate_alembic_ini(self, file_path: Path, content: str) -> ConfigValidationResult:
        """验证 alembic.ini 文件"""
        result = ConfigValidationResult(
            file_path=str(file_path),
            file_type="ini",
            status="valid"
        )
        
        try:
            import configparser
            
            config = configparser.ConfigParser()
            config.read_string(content)
            
            result.metadata["parsed_config"] = True
            result.metadata["sections"] = list(config.sections())
            
            # 检查必要的节
            required_sections = ['alembic']
            for section in required_sections:
                if section not in config:
                    self._add_issue(
                        result, "critical", "missing",
                        f"缺少必要的节: [{section}]"
                    )
            
            # 检查 alembic 节的必要配置
            if 'alembic' in config:
                alembic_section = config['alembic']
                
                required_keys = ['script_location', 'sqlalchemy.url']
                for key in required_keys:
                    if key not in alembic_section:
                        self._add_issue(
                            result, "critical", "missing",
                            f"alembic 节中缺少必要的配置: {key}"
                        )
                
                # 检查数据库 URL 格式
                if 'sqlalchemy.url' in alembic_section:
                    db_url = alembic_section['sqlalchemy.url']
                    if not db_url.startswith(('postgresql', 'sqlite', 'mysql')):
                        self._add_issue(
                            result, "warning", "compatibility",
                            f"不常见的数据库 URL 格式: {db_url[:50]}..."
                        )
                    
                    # 检查是否使用了明文密码
                    if '@' in db_url and ':' in db_url:
                        self._add_issue(
                            result, "warning", "security",
                            "数据库 URL 中可能包含明文密码",
                            suggestion="考虑使用环境变量或配置文件来存储数据库凭据"
                        )
            
        except configparser.Error as e:
            result.status = "invalid"
            self._add_issue(
                result, "critical", "syntax",
                f"INI 文件格式错误: {str(e)}"
            )
        except Exception as e:
            result.status = "invalid"
            self._add_issue(
                result, "critical", "syntax",
                f"解析文件失败: {str(e)}"
            )
        
        # 检查敏感信息
        self._check_sensitive_content(result, content)
        
        return result
    
    def _validate_docker_compose(self, file_path: Path, content: str) -> ConfigValidationResult:
        """验证 Docker Compose 文件"""
        result = ConfigValidationResult(
            file_path=str(file_path),
            file_type="yaml",
            status="valid"
        )
        
        try:
            # 解析 YAML 文件
            config = yaml.safe_load(content)
            result.metadata["parsed_config"] = True
            
            # 检查版本
            if 'version' not in config:
                self._add_issue(
                    result, "warning", "missing",
                    "缺少 Docker Compose 版本声明"
                )
            else:
                version = config['version']
                result.metadata["compose_version"] = version
                
                # 检查是否使用了过时的版本
                if version.startswith('2.'):
                    self._add_issue(
                        result, "warning", "compatibility",
                        f"Docker Compose 版本 {version} 已过时，建议升级到 3.x"
                    )
            
            # 检查服务定义
            if 'services' not in config:
                self._add_issue(
                    result, "critical", "missing",
                    "缺少 services 节，这是 Docker Compose 的核心部分"
                )
            else:
                services = config['services']
                result.metadata["service_count"] = len(services)
                result.metadata["service_names"] = list(services.keys())
                
                # 检查每个服务
                for service_name, service_config in services.items():
                    if not isinstance(service_config, dict):
                        self._add_issue(
                            result, "critical", "syntax",
                            f"服务 {service_name} 的配置必须是一个对象"
                        )
                        continue
                    
                    # 检查是否有镜像或构建配置
                    if 'image' not in service_config and 'build' not in service_config:
                        self._add_issue(
                            result, "critical", "missing",
                            f"服务 {service_name} 缺少 image 或 build 配置"
                        )
                    
                    # 检查端口映射是否合理
                    if 'ports' in service_config:
                        ports = service_config['ports']
                        for port in ports:
                            if isinstance(port, str) and ':' in port:
                                host_port, container_port = port.split(':', 1)
                                try:
                                    host_port_num = int(host_port)
                                    if host_port_num < 1024 and not self.is_termux:
                                        self._add_issue(
                                            result, "warning", "compatibility",
                                            f"服务 {service_name} 使用了特权端口 {host_port_num}，可能需要 root 权限"
                                        )
                                except ValueError:
                                    pass
                    
                    # 检查环境变量安全性
                    if 'environment' in service_config:
                        env_vars = service_config['environment']
                        if isinstance(env_vars, list):
                            for env_var in env_vars:
                                if isinstance(env_var, str) and '=' in env_var:
                                    key, value = env_var.split('=', 1)
                                    if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                                        if not value.startswith('${'):
                                            self._add_issue(
                                                result, "warning", "security",
                                                f"服务 {service_name} 中的敏感环境变量 {key} 可能使用了明文值",
                                                suggestion="使用 ${VARIABLE_NAME} 格式引用环境变量"
                                            )
            
            # 检查网络配置
            if 'networks' in config:
                networks = config['networks']
                result.metadata["network_count"] = len(networks)
                result.metadata["network_names"] = list(networks.keys())
            
            # 检查数据卷配置
            if 'volumes' in config:
                volumes = config['volumes']
                result.metadata["volume_count"] = len(volumes)
                result.metadata["volume_names"] = list(volumes.keys())
            
        except yaml.YAMLError as e:
            result.status = "invalid"
            self._add_issue(
                result, "critical", "syntax",
                f"YAML 语法错误: {str(e)}",
                suggestion="检查 YAML 格式是否正确，注意缩进和特殊字符"
            )
        except Exception as e:
            result.status = "invalid"
            self._add_issue(
                result, "critical", "syntax",
                f"解析文件失败: {str(e)}"
            )
        
        # 检查敏感信息
        self._check_sensitive_content(result, content)
        
        return result
    
    def _validate_env_file(self, file_path: Path, content: str) -> ConfigValidationResult:
        """验证环境变量文件"""
        result = ConfigValidationResult(
            file_path=str(file_path),
            file_type="env",
            status="valid"
        )
        
        lines = content.strip().split('\\n')
        result.metadata["line_count"] = len(lines)
        
        env_vars = {}
        duplicates = set()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 检查环境变量格式
            if '=' not in line:
                self._add_issue(
                    result, "warning", "syntax",
                    f"无效的环境变量格式: {line}",
                    line_number=line_num,
                    suggestion="环境变量应该使用 KEY=VALUE 格式"
                )
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # 检查重复的环境变量
            if key in env_vars:
                duplicates.add(key)
                self._add_issue(
                    result, "warning", "syntax",
                    f"重复的环境变量: {key}",
                    line_number=line_num,
                    suggestion="移除重复的变量定义"
                )
            
            env_vars[key] = value
            
            # 检查环境变量名称规范
            if not re.match(r'^[A-Z][A-Z0-9_]*$', key):
                self._add_issue(
                    result, "info", "syntax",
                    f"环境变量名 {key} 不符合常见约定（全大写加下划线）",
                    line_number=line_num,
                    suggestion="建议使用全大写字母和下划线的环境变量名"
                )
            
            # 检查空值
            if not value:
                self._add_issue(
                    result, "warning", "missing",
                    f"环境变量 {key} 的值为空",
                    line_number=line_num
                )
            
            # 检查敏感信息
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                if len(value) < 8:
                    self._add_issue(
                        result, "warning", "security",
                        f"敏感环境变量 {key} 的值可能太短（少于8位）",
                        line_number=line_num,
                        suggestion="使用更长的、更复杂的密码或密钥"
                    )
                
                if value in ['password', 'secret', '123456', 'admin', 'root']:
                    self._add_issue(
                        result, "critical", "security",
                        f"敏感环境变量 {key} 使用了弱密码: {value}",
                        line_number=line_num,
                        suggestion="使用强密码或随机生成的密钥"
                    )
        
        result.metadata["env_var_count"] = len(env_vars)
        result.metadata["duplicate_count"] = len(duplicates)
        
        # 检查常见的必要环境变量
        if 'development' in str(file_path):
            expected_vars = ['DATABASE_URL', 'REDIS_URL', 'API_HOST', 'API_PORT']
            for var in expected_vars:
                if var not in env_vars:
                    self._add_issue(
                        result, "info", "missing",
                        f"开发环境中可能缺少常用环境变量: {var}"
                    )
        
        # 检查敏感信息
        self._check_sensitive_content(result, content)
        
        return result
    
    def validate_all_configs(self) -> List[ConfigValidationResult]:
        """验证所有配置文件"""
        logger.info(f"开始验证 {len(self.config_files)} 个配置文件...")
        
        results = []
        
        for file_name, file_config in self.config_files.items():
            file_path = self.project_path / file_name
            
            # 读取文件
            success, content, error = self._read_file_safely(file_path)
            
            if not success:
                # 文件不存在或读取失败
                result = ConfigValidationResult(
                    file_path=str(file_path),
                    file_type=file_config['type'],
                    status="missing" if "not exist" in error else "invalid"
                )
                
                severity = "critical" if file_config['required'] else "warning"
                self._add_issue(
                    result, severity, "missing",
                    f"{file_config['description']}文件问题: {error}",
                    suggestion=f"创建 {file_name} 文件" if "not exist" in error else "检查文件权限和格式"
                )
                
                results.append(result)
                continue
            
            # 验证文件内容
            try:
                validator = file_config['validator']
                result = validator(file_path, content)
                results.append(result)
                
                # 统计问题严重程度
                critical_issues = len([i for i in result.issues if i.severity == "critical"])
                warning_issues = len([i for i in result.issues if i.severity == "warning"])
                info_issues = len([i for i in result.issues if i.severity == "info"])
                
                status_icon = "✅" if result.status == "valid" else "❌"
                logger.info(
                    f"{status_icon} {file_name}: {result.status.upper()} - "
                    f"{critical_issues} 严重, {warning_issues} 警告, {info_issues} 提示"
                )
                
            except Exception as e:
                result = ConfigValidationResult(
                    file_path=str(file_path),
                    file_type=file_config['type'],
                    status="invalid"
                )
                
                self._add_issue(
                    result, "critical", "syntax",
                    f"验证器异常: {str(e)}"
                )
                
                results.append(result)
                logger.error(f"❌ {file_name}: 验证器异常 - {str(e)}")
        
        self.results = results
        return results
    
    def validate_service_configs(self) -> List[ConfigValidationResult]:
        """验证服务配置文件"""
        service_results = []
        
        # 查找所有服务目录
        services_dir = self.project_path / "services"
        if not services_dir.exists():
            return service_results
        
        for service_path in services_dir.iterdir():
            if not service_path.is_dir():
                continue
            
            service_name = service_path.name
            
            # 检查 Dockerfile
            dockerfile_path = service_path / "Dockerfile"
            if dockerfile_path.exists():
                success, content, error = self._read_file_safely(dockerfile_path)
                if success:
                    result = self._validate_dockerfile(dockerfile_path, content)
                    service_results.append(result)
            
            # 检查 requirements.txt
            requirements_path = service_path / "requirements.txt"
            if requirements_path.exists():
                success, content, error = self._read_file_safely(requirements_path)
                if success:
                    result = self._validate_requirements_txt(requirements_path, content)
                    service_results.append(result)
        
        return service_results
    
    def _validate_dockerfile(self, file_path: Path, content: str) -> ConfigValidationResult:
        """验证 Dockerfile"""
        result = ConfigValidationResult(
            file_path=str(file_path),
            file_type="dockerfile",
            status="valid"
        )
        
        lines = content.strip().split('\\n')
        
        has_from = False
        has_workdir = False
        runs_as_root = True
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            # 检查 FROM 指令
            if line.upper().startswith('FROM'):
                has_from = True
                # 检查是否使用了 latest 标签
                if ':latest' in line or (':' not in line and 'FROM' in line.upper()):
                    self._add_issue(
                        result, "warning", "compatibility",
                        "使用了 latest 标签或未指定标签，可能导致构建不一致",
                        line_number=line_num,
                        suggestion="使用具体的版本标签，如 python:3.11-slim"
                    )
            
            # 检查 WORKDIR 指令
            elif line.upper().startswith('WORKDIR'):
                has_workdir = True
            
            # 检查 USER 指令
            elif line.upper().startswith('USER'):
                user = line.split()[1] if len(line.split()) > 1 else ''
                if user != 'root':
                    runs_as_root = False
            
            # 检查危险的 RUN 指令
            elif line.upper().startswith('RUN'):
                if 'rm -rf /' in line or 'rm -rf /*' in line:
                    self._add_issue(
                        result, "critical", "security",
                        "危险的 rm 命令，可能删除重要文件",
                        line_number=line_num
                    )
                
                if 'curl' in line and 'bash' in line:
                    self._add_issue(
                        result, "warning", "security",
                        "直接从网络执行 shell 脚本可能存在安全风险",
                        line_number=line_num,
                        suggestion="先下载脚本并验证其安全性"
                    )
        
        # 检查必要的指令
        if not has_from:
            self._add_issue(
                result, "critical", "missing",
                "Dockerfile 中缺少 FROM 指令"
            )
        
        if not has_workdir:
            self._add_issue(
                result, "warning", "missing",
                "建议使用 WORKDIR 指令设置工作目录"
            )
        
        if runs_as_root:
            self._add_issue(
                result, "warning", "security",
                "容器以 root 用户运行，存在安全风险",
                suggestion="使用 USER 指令切换到非特权用户"
            )
        
        return result
    
    def _validate_requirements_txt(self, file_path: Path, content: str) -> ConfigValidationResult:
        """验证 requirements.txt 文件"""
        result = ConfigValidationResult(
            file_path=str(file_path),
            file_type="requirements",
            status="valid"
        )
        
        lines = content.strip().split('\\n')
        dependencies = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            
            dependencies.append(line)
            
            # 检查版本固定
            if '==' not in line and '>=' not in line and '<=' not in line:
                self._add_issue(
                    result, "warning", "compatibility",
                    f"依赖 {line} 未指定版本，可能导致构建不一致",
                    line_number=line_num,
                    suggestion="使用 == 或 >= 指定版本范围"
                )
            
            # 检查常见的不安全依赖
            package_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
            if package_name.lower() in ['pillow', 'requests', 'urllib3']:
                # 这里可以添加更详细的版本检查
                pass
        
        result.metadata["dependency_count"] = len(dependencies)
        
        return result
    
    def generate_validation_report(self, results: List[ConfigValidationResult]) -> Dict:
        """生成验证报告"""
        # 统计问题
        total_files = len(results)
        valid_files = len([r for r in results if r.status == "valid"])
        invalid_files = len([r for r in results if r.status == "invalid"])
        missing_files = len([r for r in results if r.status == "missing"])
        
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        critical_issues = [i for i in all_issues if i.severity == "critical"]
        warning_issues = [i for i in all_issues if i.severity == "warning"]
        info_issues = [i for i in all_issues if i.severity == "info"]
        
        # 按类别统计问题
        category_stats = {}
        for issue in all_issues:
            category = issue.category
            if category not in category_stats:
                category_stats[category] = {"critical": 0, "warning": 0, "info": 0}
            category_stats[category][issue.severity] += 1
        
        # 按文件类型统计
        file_type_stats = {}
        for result in results:
            file_type = result.file_type
            if file_type not in file_type_stats:
                file_type_stats[file_type] = {"total": 0, "valid": 0, "invalid": 0, "missing": 0}
            file_type_stats[file_type]["total"] += 1
            file_type_stats[file_type][result.status] += 1
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "is_termux": self.is_termux,
                "project_path": str(self.project_path.absolute())
            },
            "summary": {
                "total_files": total_files,
                "valid_files": valid_files,
                "invalid_files": invalid_files,
                "missing_files": missing_files,
                "total_issues": len(all_issues),
                "critical_issues": len(critical_issues),
                "warning_issues": len(warning_issues),
                "info_issues": len(info_issues),
                "validation_success_rate": round((valid_files / total_files * 100) if total_files > 0 else 0, 1)
            },
            "category_statistics": category_stats,
            "file_type_statistics": file_type_stats,
            "detailed_results": [result.model_dump() for result in results],
            "recommendations": self._generate_validation_recommendations(results)
        }
        
        return report
    
    def _generate_validation_recommendations(self, results: List[ConfigValidationResult]) -> List[str]:
        """基于验证结果生成建议"""
        recommendations = []
        
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        critical_issues = [i for i in all_issues if i.severity == "critical"]
        security_issues = [i for i in all_issues if i.category == "security"]
        missing_files = [r for r in results if r.status == "missing"]
        
        if not all_issues:
            recommendations.append("🎉 所有配置文件都通过了验证！")
            return recommendations
        
        # 优先级建议
        if critical_issues:
            recommendations.append(
                f"⚠️ 优先修复 {len(critical_issues)} 个严重问题，这些问题可能导致系统无法正常运行"
            )
        
        if security_issues:
            recommendations.append(
                f"🔒 关注 {len(security_issues)} 个安全问题，建议使用环境变量或加密存储敏感信息"
            )
        
        if missing_files:
            missing_names = [Path(r.file_path).name for r in missing_files]
            recommendations.append(
                f"📁 创建缺失的配置文件: {', '.join(missing_names)}"
            )
        
        # 按类别统计建议
        syntax_issues = [i for i in all_issues if i.category == "syntax"]
        if syntax_issues:
            recommendations.append(
                f"🔧 修复 {len(syntax_issues)} 个语法错误，检查文件格式和缩进"
            )
        
        compatibility_issues = [i for i in all_issues if i.category == "compatibility"]
        if compatibility_issues:
            recommendations.append(
                f"🔄 解决 {len(compatibility_issues)} 个兼容性问题，升级过时的版本和配置"
            )
        
        # Termux 特定建议
        if self.is_termux:
            recommendations.append(
                "📱 Termux 环境提示: 某些配置可能需要针对 Android 环境进行调整，"
                "如端口范围、文件权限等"
            )
        
        return recommendations
    
    def save_report(self, report: Dict, output_path: str = "config-validation-report.json"):
        """保存验证报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 配置验证报告已保存: {Path(output_path).absolute()}")
        
        # 同时生成简化的文本报告
        text_report = self._generate_text_report(report)
        text_path = Path(output_path).with_suffix('.txt')
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        logger.info(f"📄 文本报告已保存: {text_path.absolute()}")
    
    def _generate_text_report(self, report: Dict) -> str:
        """生成简化的文本报告"""
        lines = [
            "=" * 60,
            "配置文件验证报告",
            "=" * 60,
            f"生成时间: {report['timestamp']}",
            f"环境: {'Termux Android' if report['environment']['is_termux'] else '标准 Linux'}",
            f"项目路径: {report['environment']['project_path']}",
            "",
            "总体状况:",
            f"  总文件数: {report['summary']['total_files']}",
            f"  有效文件: {report['summary']['valid_files']}",
            f"  无效文件: {report['summary']['invalid_files']}",
            f"  缺失文件: {report['summary']['missing_files']}",
            f"  验证成功率: {report['summary']['validation_success_rate']}%",
            f"  总问题数: {report['summary']['total_issues']}",
            f"    - 严重: {report['summary']['critical_issues']}",
            f"    - 警告: {report['summary']['warning_issues']}",
            f"    - 提示: {report['summary']['info_issues']}",
            "",
            "按类别统计:"
        ]
        
        for category, stats in report['category_statistics'].items():
            total = stats['critical'] + stats['warning'] + stats['info']
            lines.append(f"  {category}: {total} (严重: {stats['critical']}, 警告: {stats['warning']}, 提示: {stats['info']})")
        
        lines.extend([
            "",
            "详细结果:"
        ])
        
        for result in report['detailed_results']:
            status_icon = {
                "valid": "✅",
                "invalid": "❌",
                "missing": "❓"
            }.get(result['status'], "⚪")
            
            issue_count = len(result['issues'])
            lines.append(
                f"  {status_icon} {Path(result['file_path']).name} ({result['file_type']}) - "
                f"{result['status'].upper()} - {issue_count} 问题"
            )
            
            # 显示前3个重要问题
            important_issues = [i for i in result['issues'] if i['severity'] in ['critical', 'warning']][:3]
            for issue in important_issues:
                lines.append(f"     {issue['severity'].upper()}: {issue['message']}")
        
        lines.extend([
            "",
            "建议:"
        ])
        
        for i, recommendation in enumerate(report['recommendations'], 1):
            lines.append(f"  {i}. {recommendation}")
        
        lines.append("=" * 60)
        
        return "\\n".join(lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="配置文件验证工具")
    parser.add_argument("--project-path", "-p", default=".", help="项目路径")
    parser.add_argument("--include-services", "-s", action="store_true", help="包含服务配置验证")
    parser.add_argument("--output", "-o", default="config-validation-report", help="报告文件名（不含扩展名）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建配置验证器
    validator = ConfigurationValidator(args.project_path)
    
    # 执行配置验证
    results = validator.validate_all_configs()
    
    # 添加服务配置验证
    if args.include_services:
        service_results = validator.validate_service_configs()
        results.extend(service_results)
    
    # 生成报告
    report = validator.generate_validation_report(results)
    
    # 保存报告
    validator.save_report(report, f"{args.output}.json")
    
    # 输出总结到控制台
    summary = report['summary']
    print(f"\\n📊 配置验证完成:")
    print(f"   有效配置: {summary['valid_files']}/{summary['total_files']} ({summary['validation_success_rate']}%)")
    print(f"   总问题数: {summary['total_issues']} (严重: {summary['critical_issues']}, 警告: {summary['warning_issues']})")
    
    if summary['critical_issues'] > 0:
        print(f"   ⚠️  {summary['critical_issues']} 个严重问题需要修复")
        return 1
    elif summary['warning_issues'] > 0:
        print(f"   ⚠️  {summary['warning_issues']} 个警告建议修复")
        return 0
    else:
        print("   ✅ 所有配置文件都通过了验证")
        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)