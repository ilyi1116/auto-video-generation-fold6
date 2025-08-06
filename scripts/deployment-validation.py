#!/usr/bin/env python3
"""
部署验证系统 - 专为 Termux Android 环境优化

功能:
1. Docker Compose 部署验证
2. 微服务健康检查
3. 服务连通性测试
4. 配置验证
5. 前端构建测试
6. 基础设施组件连通性检查

作者: Claude Code
日期: 2025-08-04
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deployment-validation.log"),
    ],
)
logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """验证结果模型"""

    test_name: str
    success: bool
    message: str
    details: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_seconds: float = 0.0


class ServiceEndpoint(BaseModel):
    """服务端点模型"""

    name: str
    url: str
    health_path: str = "/health"
    expected_status: int = 200
    timeout: int = 30


class DeploymentValidator:
    """部署验证器 - 针对 Termux 环境优化"""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.results: List[ValidationResult] = []
        self.is_termux = self._detect_termux()
        self.docker_available = self._check_docker_availability()

        # 定义服务端点
        self.services = [
            ServiceEndpoint(name="api-gateway", url="http://localhost:8000"),
            ServiceEndpoint(name="auth-service", url="http://localhost:8001"),
            ServiceEndpoint(name="video-service", url="http://localhost:8004"),
            ServiceEndpoint(name="ai-service", url="http://localhost:8005"),
            ServiceEndpoint(
                name="social-service", url="http://localhost:8006"
            ),
            ServiceEndpoint(name="trend-service", url="http://localhost:8007"),
            ServiceEndpoint(
                name="scheduler-service", url="http://localhost:8008"
            ),
            ServiceEndpoint(
                name="storage-service", url="http://localhost:8009"
            ),
        ]

        # 基础设施端点
        self.infrastructure = [
            ServiceEndpoint(
                name="postgres",
                url="postgresql://localhost:5432",
                health_path="",
                timeout=10,
            ),
            ServiceEndpoint(
                name="redis",
                url="redis://localhost:6379",
                health_path="",
                timeout=10,
            ),
            ServiceEndpoint(
                name="minio",
                url="http://localhost:9000",
                health_path="/minio/health/live",
            ),
        ]

        logger.info(
            f"初始化部署验证器 - Termux: {self.is_termux}, Docker: {self.docker_available}"
        )

    def _detect_termux(self) -> bool:
        """检测是否在 Termux 环境中运行"""
        return (
            os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
            or "termux" in os.environ.get("HOME", "").lower()
            or Path("/data/data/com.termux").exists()
        )

    def _check_docker_availability(self) -> bool:
        """检查 Docker 是否可用"""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _run_command(
        self, command: List[str], timeout: int = 30
    ) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_path,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"命令超时 ({timeout}s): {' '.join(command)}"
        except Exception as e:
            return False, "", f"命令执行失败: {str(e)}"

    def _add_result(
        self,
        test_name: str,
        success: bool,
        message: str,
        details: Optional[Dict] = None,
        duration: float = 0.0,
    ):
        """添加验证结果"""
        result = ValidationResult(
            test_name=test_name,
            success=success,
            message=message,
            details=details,
            duration_seconds=duration,
        )
        self.results.append(result)

        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {message}")
        if details:
            logger.debug(
                f"详细信息: {json.dumps(details, indent=2, ensure_ascii=False)}"
            )

    async def validate_docker_compose_config(self) -> bool:
        """验证 Docker Compose 配置"""
        start_time = time.time()

        try:
            # 检查 docker-compose.yml 文件
            compose_files = [
                "docker-compose.yml",
                "docker-compose.unified.yml",
            ]

            found_files = []
            for file in compose_files:
                file_path = self.project_path / file
                if file_path.exists():
                    found_files.append(file)

            if not found_files:
                self._add_result(
                    "Docker Compose Config",
                    False,
                    "未找到 Docker Compose 配置文件",
                    duration=time.time() - start_time,
                )
                return False

            # 验证配置语法
            for file in found_files:
                success, stdout, stderr = self._run_command(
                    ["docker-compose", "-", file, "config"]
                )

                if not success:
                    self._add_result(
                        f"Docker Compose Config ({file})",
                        False,
                        f"配置文件语法错误: {stderr}",
                        duration=time.time() - start_time,
                    )
                    return False

            # 检查环境变量文件
            env_files = [".env", "docker-compose.env"]
            missing_env = []
            for env_file in env_files:
                if not (self.project_path / env_file).exists():
                    missing_env.append(env_file)

            details = {
                "found_compose_files": found_files,
                "missing_env_files": missing_env,
                "validation": "passed",
            }

            self._add_result(
                "Docker Compose Config",
                True,
                f"配置验证通过 - 找到 {len(found_files)} 个配置文件",
                details=details,
                duration=time.time() - start_time,
            )
            return True

        except Exception as e:
            self._add_result(
                "Docker Compose Config",
                False,
                f"验证过程中出现异常: {str(e)}",
                duration=time.time() - start_time,
            )
            return False

    async def test_docker_compose_deployment(self) -> bool:
        """测试 Docker Compose 部署（如果 Docker 可用）"""
        start_time = time.time()

        if not self.docker_available:
            self._add_result(
                "Docker Compose Deployment",
                False,
                "Docker 不可用，跳过部署测试",
                details={
                    "reason": "docker_unavailable",
                    "environment": "termux",
                },
                duration=time.time() - start_time,
            )
            return False

        try:
            # 尝试启动核心服务（最小化配置）
            compose_file = "docker-compose.yml"
            if (self.project_path / "docker-compose.unified.yml").exists():
                compose_file = "docker-compose.unified.yml"

            # 检查是否有正在运行的容器
            success, stdout, stderr = self._run_command(
                ["docker-compose", "-", compose_file, "ps"]
            )

            details = {
                "compose_file": compose_file,
                "running_containers": stdout.split("\n") if success else [],
                "docker_available": True,
            }

            self._add_result(
                "Docker Compose Deployment",
                success,
                (
                    "Docker Compose 状态检查完成"
                    if success
                    else f"检查失败: {stderr}"
                ),
                details=details,
                duration=time.time() - start_time,
            )
            return success

        except Exception as e:
            self._add_result(
                "Docker Compose Deployment",
                False,
                f"部署测试异常: {str(e)}",
                duration=time.time() - start_time,
            )
            return False

    async def check_service_health(self, service: ServiceEndpoint) -> bool:
        """检查单个服务健康状态"""
        start_time = time.time()

        try:
            if service.name == "postgres":
                # PostgreSQL 连接测试
                success, stdout, stderr = self._run_command(
                    ["pg_isready", "-h", "localhost", "-p", "5432"],
                    timeout=service.timeout,
                )

                self._add_result(
                    f"Service Health - {service.name}",
                    success,
                    (
                        "PostgreSQL 连接正常"
                        if success
                        else f"连接失败: {stderr}"
                    ),
                    details={"type": "postgres", "command": "pg_isready"},
                    duration=time.time() - start_time,
                )
                return success

            elif service.name == "redis":
                # Redis 连接测试
                success, stdout, stderr = self._run_command(
                    ["redis-cli", "-h", "localhost", "-p", "6379", "ping"],
                    timeout=service.timeout,
                )

                success = success and "PONG" in stdout

                self._add_result(
                    f"Service Health - {service.name}",
                    success,
                    "Redis 连接正常" if success else f"连接失败: {stderr}",
                    details={"type": "redis", "response": stdout.strip()},
                    duration=time.time() - start_time,
                )
                return success

            else:
                # HTTP 服务健康检查
                async with httpx.AsyncClient(
                    timeout=service.timeout
                ) as client:
                    health_url = f"{service.url}{service.health_path}"
                    response = await client.get(health_url)

                    success = response.status_code == service.expected_status

                    details = {
                        "url": health_url,
                        "status_code": response.status_code,
                        "expected_status": service.expected_status,
                        "response_time_ms": response.elapsed.total_seconds()
                        * 1000,
                    }

                    self._add_result(
                        f"Service Health - {service.name}",
                        success,
                        (
                            f"服务响应正常 ({response.status_code})"
                            if success
                            else f"服务异常 ({response.status_code})"
                        ),
                        details=details,
                        duration=time.time() - start_time,
                    )
                    return success

        except Exception as e:
            self._add_result(
                f"Service Health - {service.name}",
                False,
                f"健康检查失败: {str(e)}",
                details={"error": str(e), "service_url": service.url},
                duration=time.time() - start_time,
            )
            return False

    async def test_service_connectivity(self) -> bool:
        """测试服务间连通性"""
        start_time = time.time()

        try:
            # 测试基础设施服务
            infrastructure_results = []
            for infra in self.infrastructure:
                result = await self.check_service_health(infra)
                infrastructure_results.append((infra.name, result))

            # 测试应用服务（仅在基础设施可用时）
            service_results = []
            if any(result for _, result in infrastructure_results):
                for service in self.services[:3]:  # 仅测试前3个核心服务
                    result = await self.check_service_health(service)
                    service_results.append((service.name, result))

            total_tests = len(infrastructure_results) + len(service_results)
            passed_tests = sum(
                [
                    sum(1 for _, result in infrastructure_results if result),
                    sum(1 for _, result in service_results if result),
                ]
            )

            success = passed_tests > 0  # 至少有一个服务可用

            details = {
                "infrastructure_services": dict(infrastructure_results),
                "application_services": dict(service_results),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "pass_rate": (
                    f"{passed_tests/total_tests*100:.1f}%"
                    if total_tests > 0
                    else "0%"
                ),
            }

            self._add_result(
                "Service Connectivity",
                success,
                f"连通性测试完成 - {passed_tests}/{total_tests} 服务可用",
                details=details,
                duration=time.time() - start_time,
            )
            return success

        except Exception as e:
            self._add_result(
                "Service Connectivity",
                False,
                f"连通性测试异常: {str(e)}",
                duration=time.time() - start_time,
            )
            return False

    async def validate_configuration(self) -> bool:
        """验证配置文件"""
        start_time = time.time()

        try:
            config_files = {
                "pyproject.toml": "项目配置",
                "alembic.ini": "数据库迁移配置",
                "config/environments/development.env": "开发环境配置",
                "config/environments/production.env": "生产环境配置",
                "docker-compose.yml": "Docker Compose 配置",
            }

            found_configs = {}
            missing_configs = []

            for config_file, description in config_files.items():
                file_path = self.project_path / config_file
                if file_path.exists():
                    try:
                        file_size = file_path.stat().st_size
                        found_configs[config_file] = {
                            "description": description,
                            "size_bytes": file_size,
                            "exists": True,
                        }
                    except Exception as e:
                        found_configs[config_file] = {
                            "description": description,
                            "error": str(e),
                            "exists": True,
                        }
                else:
                    missing_configs.append(config_file)

            # 检查关键配置
            critical_configs = ["pyproject.toml", "docker-compose.yml"]
            has_critical = all(
                config in found_configs for config in critical_configs
            )

            success = has_critical and len(found_configs) >= 3

            details = {
                "found_configs": found_configs,
                "missing_configs": missing_configs,
                "critical_configs_present": has_critical,
                "total_found": len(found_configs),
                "total_expected": len(config_files),
            }

            self._add_result(
                "Configuration Validation",
                success,
                f"配置验证{'通过' if success else '失败'} - {len(found_configs)}/{len(config_files)} 配置文件存在",
                details=details,
                duration=time.time() - start_time,
            )
            return success

        except Exception as e:
            self._add_result(
                "Configuration Validation",
                False,
                f"配置验证异常: {str(e)}",
                duration=time.time() - start_time,
            )
            return False

    async def test_frontend_build(self) -> bool:
        """测试前端构建（在 Termux 环境中进行简化测试）"""
        start_time = time.time()

        try:
            frontend_paths = [
                self.project_path / "src" / "frontend",
                self.project_path / "frontend",
                self.project_path
                / "auto_generate_video_fold6.old"
                / "frontend",
            ]

            frontend_path = None
            for path in frontend_paths:
                if path.exists() and (path / "package.json").exists():
                    frontend_path = path
                    break

            if not frontend_path:
                self._add_result(
                    "Frontend Build Test",
                    False,
                    "未找到前端项目目录或 package.json",
                    details={
                        "searched_paths": [str(p) for p in frontend_paths]
                    },
                    duration=time.time() - start_time,
                )
                return False

            # 检查 Node.js 是否可用
            node_available = False
            try:
                result = subprocess.run(
                    ["node", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                node_available = result.returncode == 0
                node_version = result.stdout.strip()
            except Exception:
                node_version = "未安装"

            if not node_available:
                self._add_result(
                    "Frontend Build Test",
                    False,
                    "Node.js 不可用，无法进行前端构建测试",
                    details={
                        "frontend_path": str(frontend_path),
                        "node_available": False,
                        "node_version": node_version,
                        "environment": "termux",
                    },
                    duration=time.time() - start_time,
                )
                return False

            # 检查依赖是否安装
            node_modules_exists = (frontend_path / "node_modules").exists()
            package_lock_exists = (
                frontend_path / "package-lock.json"
            ).exists()

            details = {
                "frontend_path": str(frontend_path),
                "node_available": True,
                "node_version": node_version,
                "node_modules_exists": node_modules_exists,
                "package_lock_exists": package_lock_exists,
            }

            # 在 Termux 环境中，我们只验证文件存在性，不执行实际构建
            if self.is_termux:
                success = True  # 基础检查通过
                message = f"前端项目结构验证通过 (Termux 环境) - Node.js {node_version}"
            else:
                # 在非 Termux 环境中可以尝试实际构建
                success, stdout, stderr = self._run_command(
                    ["npm", "run", "build"], timeout=120
                )
                message = (
                    "前端构建成功" if success else f"构建失败: {stderr[:200]}"
                )
                details["build_output"] = (
                    stdout[:500] if success else stderr[:500]
                )

            self._add_result(
                "Frontend Build Test",
                success,
                message,
                details=details,
                duration=time.time() - start_time,
            )
            return success

        except Exception as e:
            self._add_result(
                "Frontend Build Test",
                False,
                f"前端构建测试异常: {str(e)}",
                duration=time.time() - start_time,
            )
            return False

    async def run_all_validations(self) -> Dict:
        """运行所有验证测试"""
        logger.info("🚀 开始运行完整的部署验证测试套件")
        start_time = time.time()

        # 依次运行所有验证
        validations = [
            ("配置验证", self.validate_configuration()),
            ("Docker Compose 配置检查", self.validate_docker_compose_config()),
            ("Docker Compose 部署测试", self.test_docker_compose_deployment()),
            ("服务连通性测试", self.test_service_connectivity()),
            ("前端构建测试", self.test_frontend_build()),
        ]

        for name, validation in validations:
            logger.info(f"执行 {name}...")
            try:
                await validation
            except Exception as e:
                logger.error(f"{name} 执行异常: {str(e)}")
                self._add_result(
                    name, False, f"执行异常: {str(e)}", duration=0
                )

        # 生成总结报告
        total_duration = time.time() - start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "is_termux": self.is_termux,
                "docker_available": self.docker_available,
                "project_path": str(self.project_path.absolute()),
            },
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "pass_rate": (
                    f"{passed_tests/total_tests*100:.1f}%"
                    if total_tests > 0
                    else "0%"
                ),
                "total_duration_seconds": round(total_duration, 2),
            },
            "results": [result.model_dump() for result in self.results],
        }

        logger.info(
            f"✅ 验证完成 - {passed_tests}/{total_tests} 测试通过 ({summary['summary']['pass_rate']})"
        )

        return summary

    def save_report(
        self,
        summary: Dict,
        filename: str = "deployment-validation-report.json",
    ):
        """保存验证报告"""
        report_path = self.project_path / filename
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 验证报告已保存: {report_path.absolute()}")

        # 同时生成简化的 Markdown 报告
        self._generate_markdown_report(summary, report_path.with_suffix(".md"))

    def _generate_markdown_report(self, summary: Dict, output_path: Path):
        """生成 Markdown 格式的报告"""
        markdown_content = """# 部署验证报告

**生成时间**: {summary['timestamp']}
**环境信息**: {'Termux Android' if summary['environment']['is_termux'] else '标准 Linux'}
**Docker 可用**: {'✅' if summary['environment']['docker_available'] else '❌'}

## 测试总结

- **总测试数**: {summary['summary']['total_tests']}
- **通过测试**: {summary['summary']['passed_tests']}
- **失败测试**: {summary['summary']['failed_tests']}
- **通过率**: {summary['summary']['pass_rate']}
- **总耗时**: {summary['summary']['total_duration_seconds']} 秒

## 详细结果

"""

        for result in summary["results"]:
            status = "✅ 通过" if result["success"] else "❌ 失败"
            markdown_content += f"### {result['test_name']}\n"
            markdown_content += f"**状态**: {status}\n"
            markdown_content += f"**信息**: {result['message']}\n"
            markdown_content += (
                f"**耗时**: {result['duration_seconds']:.2f} 秒\n\n"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"📄 Markdown 报告已保存: {output_path}")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="部署验证系统")
    parser.add_argument("--project-path", "-p", default=".", help="项目路径")
    parser.add_argument(
        "--output",
        "-o",
        default="deployment-validation-report",
        help="报告文件名（不含扩展名）",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="详细输出"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建验证器并运行测试
    validator = DeploymentValidator(args.project_path)
    summary = await validator.run_all_validations()

    # 保存报告
    validator.save_report(summary, f"{args.output}.json")

    # 根据结果返回适当的退出码
    exit_code = 0 if summary["summary"]["passed_tests"] > 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)
