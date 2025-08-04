#!/usr/bin/env python3
"""
微服务健康检查工具 - 适配 Termux Android 环境

功能:
1. 多协议健康检查 (HTTP, PostgreSQL, Redis, MinIO)
2. 并行检查提升效率
3. 详细的健康状态报告
4. 自动重试机制
5. 性能指标收集
6. 故障诊断建议

作者: Claude Code
日期: 2025-08-04
"""

import asyncio
import json
import logging
import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import httpx
from pydantic import BaseModel, Field

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthCheckResult(BaseModel):
    """健康检查结果模型"""
    service_name: str
    service_type: str
    endpoint: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: float = 0.0
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    details: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    retries: int = 0


class ServiceHealthChecker:
    """服务健康检查器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.is_termux = self._detect_termux()
        
        # 定义服务配置
        self.services = {
            # 基础设施服务
            "postgres": {
                "type": "postgres",
                "host": "localhost",
                "port": 5432,
                "database": "auto_video_generation",
                "user": "postgres"
            },
            "redis": {
                "type": "redis",
                "host": "localhost",
                "port": 6379
            },
            "minio": {
                "type": "http",
                "url": "http://localhost:9000/minio/health/live",
                "expected_status": 200
            },
            
            # 应用服务
            "api-gateway": {
                "type": "http",
                "url": "http://localhost:8000/health",
                "expected_status": 200
            },
            "auth-service": {
                "type": "http",
                "url": "http://localhost:8001/health",
                "expected_status": 200
            },
            "video-service": {
                "type": "http",
                "url": "http://localhost:8004/health",
                "expected_status": 200
            },
            "ai-service": {
                "type": "http",
                "url": "http://localhost:8005/health",
                "expected_status": 200
            },
            "social-service": {
                "type": "http",
                "url": "http://localhost:8006/health",
                "expected_status": 200
            },
            "trend-service": {
                "type": "http",
                "url": "http://localhost:8007/health",
                "expected_status": 200
            },
            "scheduler-service": {
                "type": "http",
                "url": "http://localhost:8008/health",
                "expected_status": 200
            },
            "storage-service": {
                "type": "http",
                "url": "http://localhost:8009/health",
                "expected_status": 200
            }
        }
        
        logger.info(f"健康检查器初始化完成 - Termux: {self.is_termux}, 超时: {timeout}s, 重试: {max_retries}次")
    
    def _detect_termux(self) -> bool:
        """检测是否在 Termux 环境中运行"""
        return (
            os.environ.get('PREFIX', '').startswith('/data/data/com.termux') or
            'termux' in os.environ.get('HOME', '').lower() or
            Path('/data/data/com.termux').exists()
        )
    
    async def _check_port_open(self, host: str, port: int, timeout: int = 5) -> bool:
        """检查端口是否开放"""
        try:
            # 使用 asyncio 进行非阻塞的端口检查
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
    
    async def _check_http_service(self, config: Dict) -> HealthCheckResult:
        """检查 HTTP 服务健康状态"""
        service_name = config.get('name', 'unknown')
        url = config['url']
        expected_status = config.get('expected_status', 200)
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                is_healthy = response.status_code == expected_status
                status = "healthy" if is_healthy else "unhealthy"
                
                # 尝试解析响应内容
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text[:200]}
                
                return HealthCheckResult(
                    service_name=service_name,
                    service_type="http",
                    endpoint=url,
                    status=status,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    details={
                        "response_data": response_data,
                        "headers": dict(response.headers),
                        "expected_status": expected_status
                    }
                )
                
        except httpx.TimeoutException:
            return HealthCheckResult(
                service_name=service_name,
                service_type="http",
                endpoint=url,
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=f"请求超时 ({self.timeout}s)",
                details={"timeout": self.timeout}
            )
        except Exception as e:
            return HealthCheckResult(
                service_name=service_name,
                service_type="http",
                endpoint=url,
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
                details={"exception_type": type(e).__name__}
            )
    
    async def _check_postgres_service(self, config: Dict) -> HealthCheckResult:
        """检查 PostgreSQL 服务健康状态"""
        service_name = config.get('name', 'postgres')
        host = config.get('host', 'localhost')
        port = config.get('port', 5432)
        
        start_time = time.time()
        
        # 首先检查端口是否开放
        port_open = await self._check_port_open(host, port, timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if not port_open:
            return HealthCheckResult(
                service_name=service_name,
                service_type="postgres",
                endpoint=f"postgresql://{host}:{port}",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="PostgreSQL 端口不可达",
                details={"port_check": False}
            )
        
        # 如果有 pg_isready 命令，使用它进行更详细的检查
        try:
            process = await asyncio.create_subprocess_exec(
                'pg_isready', '-h', host, '-p', str(port),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )
            
            is_healthy = process.returncode == 0
            status = "healthy" if is_healthy else "unhealthy"
            
            return HealthCheckResult(
                service_name=service_name,
                service_type="postgres",
                endpoint=f"postgresql://{host}:{port}",
                status=status,
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "pg_isready_output": stdout.decode().strip(),
                    "pg_isready_error": stderr.decode().strip(),
                    "return_code": process.returncode
                }
            )
            
        except (FileNotFoundError, asyncio.TimeoutError) as e:
            # pg_isready 不可用或超时，仅基于端口检查
            return HealthCheckResult(
                service_name=service_name,
                service_type="postgres",
                endpoint=f"postgresql://{host}:{port}",
                status="healthy" if port_open else "unhealthy",
                response_time_ms=response_time,
                error_message=str(e) if not port_open else None,
                details={
                    "check_method": "port_only",
                    "port_open": port_open,
                    "pg_isready_available": False
                }
            )
    
    async def _check_redis_service(self, config: Dict) -> HealthCheckResult:
        """检查 Redis 服务健康状态"""
        service_name = config.get('name', 'redis')
        host = config.get('host', 'localhost')
        port = config.get('port', 6379)
        
        start_time = time.time()
        
        # 首先检查端口是否开放
        port_open = await self._check_port_open(host, port, timeout=5)
        
        if not port_open:
            return HealthCheckResult(
                service_name=service_name,
                service_type="redis",
                endpoint=f"redis://{host}:{port}",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message="Redis 端口不可达",
                details={"port_check": False}
            )
        
        # 如果有 redis-cli 命令，使用它进行 PING 测试
        try:
            process = await asyncio.create_subprocess_exec(
                'redis-cli', '-h', host, '-p', str(port), 'ping',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )
            
            output = stdout.decode().strip()
            is_healthy = process.returncode == 0 and output == "PONG"
            status = "healthy" if is_healthy else "unhealthy"
            
            return HealthCheckResult(
                service_name=service_name,
                service_type="redis",
                endpoint=f"redis://{host}:{port}",
                status=status,
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "ping_response": output,
                    "redis_cli_error": stderr.decode().strip(),
                    "return_code": process.returncode
                }
            )
            
        except (FileNotFoundError, asyncio.TimeoutError) as e:
            # redis-cli 不可用或超时，仅基于端口检查
            return HealthCheckResult(
                service_name=service_name,
                service_type="redis",
                endpoint=f"redis://{host}:{port}",
                status="healthy" if port_open else "unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e) if not port_open else None,
                details={
                    "check_method": "port_only",
                    "port_open": port_open,
                    "redis_cli_available": False
                }
            )
    
    async def _check_service_with_retry(self, service_name: str, config: Dict) -> HealthCheckResult:
        """带重试机制的服务检查"""
        config['name'] = service_name
        
        for attempt in range(self.max_retries + 1):
            try:
                if config['type'] == 'http':
                    result = await self._check_http_service(config)
                elif config['type'] == 'postgres':
                    result = await self._check_postgres_service(config)
                elif config['type'] == 'redis':
                    result = await self._check_redis_service(config)
                else:
                    raise ValueError(f"不支持的服务类型: {config['type']}")
                
                result.retries = attempt
                
                # 如果检查成功，直接返回
                if result.status == "healthy":
                    return result
                
                # 如果还有重试机会，等待后重试
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                
                return result
                
            except Exception as e:
                if attempt == self.max_retries:
                    return HealthCheckResult(
                        service_name=service_name,
                        service_type=config['type'],
                        endpoint=config.get('url', f"{config.get('host', 'unknown')}:{config.get('port', 'unknown')}"),
                        status="unhealthy",
                        error_message=f"检查失败 (重试 {attempt} 次): {str(e)}",
                        retries=attempt,
                        details={"exception_type": type(e).__name__, "final_attempt": True}
                    )
                
                await asyncio.sleep(2 ** attempt)
        
        # 不应该到达这里
        return HealthCheckResult(
            service_name=service_name,
            service_type=config['type'],
            endpoint="unknown",
            status="unknown",
            error_message="未知错误"
        )
    
    async def check_all_services(self, services: Optional[List[str]] = None) -> List[HealthCheckResult]:
        """检查所有服务或指定的服务列表"""
        if services is None:
            services = list(self.services.keys())
        
        logger.info(f"开始检查 {len(services)} 个服务的健康状态...")
        
        # 并行检查所有服务
        tasks = []
        for service_name in services:
            if service_name in self.services:
                task = self._check_service_with_retry(service_name, self.services[service_name])
                tasks.append(task)
            else:
                logger.warning(f"未知服务: {service_name}")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = services[i]
                processed_results.append(HealthCheckResult(
                    service_name=service_name,
                    service_type="unknown",
                    endpoint="unknown",
                    status="unhealthy",
                    error_message=f"检查异常: {str(result)}",
                    details={"exception_type": type(result).__name__}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def generate_health_report(self, results: List[HealthCheckResult]) -> Dict:
        """生成健康检查报告"""
        healthy_services = [r for r in results if r.status == "healthy"]
        unhealthy_services = [r for r in results if r.status == "unhealthy"]
        unknown_services = [r for r in results if r.status == "unknown"]
        
        total_services = len(results)
        health_percentage = (len(healthy_services) / total_services * 100) if total_services > 0 else 0
        
        # 按服务类型分组统计
        service_types = {}
        for result in results:
            service_type = result.service_type
            if service_type not in service_types:
                service_types[service_type] = {"total": 0, "healthy": 0, "unhealthy": 0, "unknown": 0}
            
            service_types[service_type]["total"] += 1
            service_types[service_type][result.status] += 1
        
        # 性能统计
        response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "is_termux": self.is_termux,
                "check_timeout": self.timeout,
                "max_retries": self.max_retries
            },
            "summary": {
                "total_services": total_services,
                "healthy_services": len(healthy_services),
                "unhealthy_services": len(unhealthy_services),
                "unknown_services": len(unknown_services),
                "health_percentage": round(health_percentage, 1),
                "average_response_time_ms": round(avg_response_time, 2)
            },
            "service_types": service_types,
            "detailed_results": [result.model_dump() for result in results],
            "recommendations": self._generate_recommendations(results)
        }
        
        return report
    
    def _generate_recommendations(self, results: List[HealthCheckResult]) -> List[str]:
        """基于检查结果生成建议"""
        recommendations = []
        
        unhealthy_services = [r for r in results if r.status == "unhealthy"]
        
        if not unhealthy_services:
            recommendations.append("🎉 所有服务运行正常！")
            return recommendations
        
        # 按服务类型分析问题
        postgres_issues = [r for r in unhealthy_services if r.service_type == "postgres"]
        redis_issues = [r for r in unhealthy_services if r.service_type == "redis"]
        http_issues = [r for r in unhealthy_services if r.service_type == "http"]
        
        if postgres_issues:
            recommendations.append(
                f"🔧 PostgreSQL 服务异常 ({len(postgres_issues)} 个): "
                "检查数据库是否启动，端口 5432 是否可访问"
            )
        
        if redis_issues:
            recommendations.append(
                f"🔧 Redis 服务异常 ({len(redis_issues)} 个): "
                "检查 Redis 是否启动，端口 6379 是否可访问"
            )
        
        if http_issues:
            timeout_issues = [r for r in http_issues if "超时" in (r.error_message or "")]
            if timeout_issues:
                recommendations.append(
                    f"⏱️ HTTP 服务超时 ({len(timeout_issues)} 个): "
                    "可能需要增加超时时间或检查服务启动状态"
                )
            
            connection_issues = [r for r in http_issues if "连接" in (r.error_message or "")]
            if connection_issues:
                recommendations.append(
                    f"🔌 HTTP 服务连接失败 ({len(connection_issues)} 个): "
                    "检查服务是否启动，防火墙是否阻止连接"
                )
        
        # Termux 特定建议
        if self.is_termux:
            recommendations.append(
                "📱 Termux 环境建议: 某些服务可能需要额外的权限或配置，"
                "建议检查 Termux 网络权限和端口访问权限"
            )
        
        return recommendations
    
    def save_report(self, report: Dict, output_path: str = "health-check-report.json"):
        """保存健康检查报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 健康检查报告已保存: {Path(output_path).absolute()}")
        
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
            "微服务健康检查报告",
            "=" * 60,
            f"生成时间: {report['timestamp']}",
            f"环境: {'Termux Android' if report['environment']['is_termux'] else '标准 Linux'}",
            "",
            "总体状况:",
            f"  总服务数: {report['summary']['total_services']}",
            f"  健康服务: {report['summary']['healthy_services']}",
            f"  异常服务: {report['summary']['unhealthy_services']}",
            f"  未知状态: {report['summary']['unknown_services']}",
            f"  健康率: {report['summary']['health_percentage']}%",
            f"  平均响应时间: {report['summary']['average_response_time_ms']} ms",
            "",
            "详细结果:"
        ]
        
        for result in report['detailed_results']:
            status_icon = {
                "healthy": "✅",
                "unhealthy": "❌",
                "unknown": "❓"
            }.get(result['status'], "⚪")
            
            lines.append(
                f"  {status_icon} {result['service_name']} ({result['service_type']}) - "
                f"{result['response_time_ms']:.1f}ms"
            )
            
            if result['error_message']:
                lines.append(f"     错误: {result['error_message']}")
        
        lines.extend([
            "",
            "建议:"
        ])
        
        for i, recommendation in enumerate(report['recommendations'], 1):
            lines.append(f"  {i}. {recommendation}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="微服务健康检查工具")
    parser.add_argument("--services", "-s", nargs="*", help="指定要检查的服务名称")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="超时时间（秒）")
    parser.add_argument("--retries", "-r", type=int, default=3, help="最大重试次数")
    parser.add_argument("--output", "-o", default="health-check-report", help="报告文件名（不含扩展名）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建健康检查器
    checker = ServiceHealthChecker(timeout=args.timeout, max_retries=args.retries)
    
    # 执行健康检查
    results = await checker.check_all_services(args.services)
    
    # 生成报告
    report = checker.generate_health_report(results)
    
    # 保存报告
    checker.save_report(report, f"{args.output}.json")
    
    # 输出总结到控制台
    summary = report['summary']
    print(f"\n📊 健康检查完成:")
    print(f"   健康服务: {summary['healthy_services']}/{summary['total_services']} ({summary['health_percentage']}%)")
    print(f"   平均响应时间: {summary['average_response_time_ms']} ms")
    
    if summary['unhealthy_services'] > 0:
        print(f"   ⚠️  {summary['unhealthy_services']} 个服务异常")
        return 1
    else:
        print("   ✅ 所有服务运行正常")
        return 0


if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)
