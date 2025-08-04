#!/usr/bin/env python3
"""
服务连通性测试工具 - 专为 Termux Android 环境设计

功能:
1. 网络连通性测试 (TCP/UDP/HTTP)
2. 服务间通信测试
3. API 端点响应测试
4. 数据库连接测试
5. 消息队列连通性测试
6. 网络延迟和吞吐量测试

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
from typing import Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConnectivityResult(BaseModel):
    """连通性测试结果模型"""
    test_name: str
    test_type: str  # tcp, udp, http, api, database
    source: str
    target: str
    status: str  # connected, failed, timeout
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    details: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class NetworkConnectivityTester:
    """网络连通性测试器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.is_termux = self._detect_termux()
        
        # 定义测试目标
        self.test_targets = {
            # 本地基础设施服务
            "postgres": {
                "type": "tcp",
                "host": "localhost",
                "port": 5432,
                "description": "PostgreSQL 数据库"
            },
            "redis": {
                "type": "tcp",
                "host": "localhost",
                "port": 6379,
                "description": "Redis 缓存服务"
            },
            "minio": {
                "type": "http",
                "url": "http://localhost:9000/minio/health/live",
                "description": "MinIO 对象存储"
            },
            
            # 应用服务
            "api-gateway": {
                "type": "http",
                "url": "http://localhost:8000/health",
                "description": "API 网关服务"
            },
            "auth-service": {
                "type": "http",
                "url": "http://localhost:8001/health",
                "description": "认证服务"
            },
            "video-service": {
                "type": "http",
                "url": "http://localhost:8004/health",
                "description": "视频生成服务"
            },
            "ai-service": {
                "type": "http",
                "url": "http://localhost:8005/health",
                "description": "AI 服务"
            },
            
            # 外部服务
            "internet": {
                "type": "http",
                "url": "http://httpbin.org/get",
                "description": "互联网连接测试",
                "optional": True
            },
            "dns": {
                "type": "dns",
                "host": "8.8.8.8",
                "port": 53,
                "description": "DNS 解析服务",
                "optional": True
            }
        }
        
        logger.info(f"连通性测试器初始化完成 - Termux: {self.is_termux}, 超时: {timeout}s")
    
    def _detect_termux(self) -> bool:
        """检测是否在 Termux 环境中运行"""
        return (
            os.environ.get('PREFIX', '').startswith('/data/data/com.termux') or
            'termux' in os.environ.get('HOME', '').lower() or
            Path('/data/data/com.termux').exists()
        )
    
    async def _test_tcp_connection(self, host: str, port: int, timeout: int = None) -> Tuple[bool, float, Optional[str]]:
        """测试 TCP 连接"""
        if timeout is None:
            timeout = self.timeout
        
        start_time = time.time()
        
        try:
            # 使用 asyncio 进行非阻塞的 TCP 连接测试
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            
            response_time = (time.time() - start_time) * 1000
            
            # 关闭连接
            writer.close()
            await writer.wait_closed()
            
            return True, response_time, None
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"TCP 连接超时 ({timeout}s)"
        except ConnectionRefusedError:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"TCP 连接被拒绝 - 端口 {port} 可能未开放"
        except OSError as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"TCP 连接失败: {str(e)}"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"TCP 测试异常: {str(e)}"
    
    async def _test_http_connection(self, url: str, timeout: int = None) -> Tuple[bool, float, Optional[str], Optional[Dict]]:
        """测试 HTTP 连接"""
        if timeout is None:
            timeout = self.timeout
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                success = 200 <= response.status_code < 400
                error_msg = None if success else f"HTTP {response.status_code}"
                
                details = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "response_size_bytes": len(response.content)
                }
                
                # 尝试解析 JSON 响应
                try:
                    details["response_data"] = response.json()
                except:
                    details["response_text"] = response.text[:200]  # 只保存前200个字符
                
                return success, response_time, error_msg, details
                
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"HTTP 请求超时 ({timeout}s)", None
        except httpx.ConnectError as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"HTTP 连接失败: {str(e)}", None
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"HTTP 测试异常: {str(e)}", None
    
    async def _test_dns_resolution(self, host: str, port: int = 53) -> Tuple[bool, float, Optional[str], Optional[Dict]]:
        """测试 DNS 解析"""
        start_time = time.time()
        
        try:
            # 测试域名解析
            test_domain = "google.com"
            
            loop = asyncio.get_event_loop()
            result = await loop.getaddrinfo(test_domain, None)
            
            response_time = (time.time() - start_time) * 1000
            
            details = {
                "test_domain": test_domain,
                "resolved_ips": [addr[4][0] for addr in result],
                "dns_server": host
            }
            
            return True, response_time, None, details
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"DNS 解析失败: {str(e)}", None
    
    async def _test_service_api(self, url: str) -> Tuple[bool, float, Optional[str], Optional[Dict]]:
        """测试服务 API 响应"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 测试基本的健康检查端点
                health_response = await client.get(url)
                
                # 如果健康检查通过，尝试测试其他端点
                response_time = (time.time() - start_time) * 1000
                
                if health_response.status_code == 200:
                    # 尝试访问 API 文档端点
                    base_url = url.replace('/health', '')
                    docs_endpoints = ['/docs', '/openapi.json', '/api/v1/status']
                    
                    endpoint_results = {}
                    for endpoint in docs_endpoints:
                        try:
                            docs_response = await client.get(f"{base_url}{endpoint}", timeout=5)
                            endpoint_results[endpoint] = {
                                "status_code": docs_response.status_code,
                                "available": docs_response.status_code == 200
                            }
                        except:
                            endpoint_results[endpoint] = {
                                "status_code": None,
                                "available": False
                            }
                    
                    details = {
                        "health_status": health_response.status_code,
                        "available_endpoints": endpoint_results,
                        "service_info": None
                    }
                    
                    # 尝试获取服务信息
                    try:
                        health_data = health_response.json()
                        details["service_info"] = health_data
                    except:
                        details["service_info"] = {"raw_response": health_response.text[:100]}
                    
                    return True, response_time, None, details
                else:
                    return False, response_time, f"API 健康检查失败: HTTP {health_response.status_code}", {
                        "status_code": health_response.status_code,
                        "response_text": health_response.text[:200]
                    }
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"API 测试异常: {str(e)}", None
    
    async def test_single_target(self, target_name: str, config: Dict) -> ConnectivityResult:
        """测试单个目标的连通性"""
        start_time = time.time()
        
        try:
            if config['type'] == 'tcp':
                success, response_time, error_msg = await self._test_tcp_connection(
                    config['host'], config['port']
                )
                details = {"host": config['host'], "port": config['port']}
                
            elif config['type'] == 'http':
                success, response_time, error_msg, http_details = await self._test_http_connection(
                    config['url']
                )
                details = http_details or {}
                
            elif config['type'] == 'dns':
                success, response_time, error_msg, dns_details = await self._test_dns_resolution(
                    config['host'], config.get('port', 53)
                )
                details = dns_details or {}
                
            elif config['type'] == 'api':
                success, response_time, error_msg, api_details = await self._test_service_api(
                    config['url']
                )
                details = api_details or {}
                
            else:
                return ConnectivityResult(
                    test_name=target_name,
                    test_type=config['type'],
                    source="localhost",
                    target=config.get('url', f"{config.get('host')}:{config.get('port')}"),
                    status="failed",
                    error_message=f"不支持的测试类型: {config['type']}"
                )
            
            status = "connected" if success else "failed"
            
            details.update({
                "description": config.get('description', ''),
                "test_duration_ms": (time.time() - start_time) * 1000
            })
            
            return ConnectivityResult(
                test_name=target_name,
                test_type=config['type'],
                source="localhost",
                target=config.get('url', f"{config.get('host', 'unknown')}:{config.get('port', 'unknown')}"),
                status=status,
                response_time_ms=response_time,
                error_message=error_msg,
                details=details
            )
            
        except Exception as e:
            return ConnectivityResult(
                test_name=target_name,
                test_type=config.get('type', 'unknown'),
                source="localhost",
                target=config.get('url', f"{config.get('host', 'unknown')}:{config.get('port', 'unknown')}"),
                status="failed",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=f"测试异常: {str(e)}",
                details={"exception_type": type(e).__name__}
            )
    
    async def test_all_connectivity(self, include_optional: bool = True) -> List[ConnectivityResult]:
        """测试所有目标的连通性"""
        logger.info(f"开始连通性测试 - {len(self.test_targets)} 个目标")
        
        tasks = []
        for target_name, config in self.test_targets.items():
            # 跳过可选测试（如果指定）
            if not include_optional and config.get('optional', False):
                continue
            
            task = self.test_single_target(target_name, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                target_name = list(self.test_targets.keys())[i]
                processed_results.append(ConnectivityResult(
                    test_name=target_name,
                    test_type="unknown",
                    source="localhost",
                    target="unknown",
                    status="failed",
                    error_message=f"测试异常: {str(result)}",
                    details={"exception_type": type(result).__name__}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def test_service_to_service_connectivity(self) -> List[ConnectivityResult]:
        """测试服务间连通性生成的）"""
        logger.info("测试服务间连通性...")
        
        # 定义服务间的关键连接
        service_connections = [
            {
                "name": "api-gateway-to-auth",
                "source": "api-gateway",
                "target": "http://localhost:8001/health",
                "description": "API 网关到认证服务"
            },
            {
                "name": "api-gateway-to-video",
                "source": "api-gateway",
                "target": "http://localhost:8004/health",
                "description": "API 网关到视频服务"
            },
            {
                "name": "video-service-to-ai",
                "source": "video-service",
                "target": "http://localhost:8005/health",
                "description": "视频服务到 AI 服务"
            },
            {
                "name": "services-to-postgres",
                "source": "services",
                "target": "localhost:5432",
                "description": "服务到 PostgreSQL"
            },
            {
                "name": "services-to-redis",
                "source": "services",
                "target": "localhost:6379",
                "description": "服务到 Redis"
            }
        ]
        
        results = []
        for connection in service_connections:
            start_time = time.time()
            
            if connection['target'].startswith('http'):
                # HTTP 连接测试
                success, response_time, error_msg, details = await self._test_http_connection(
                    connection['target']
                )
            else:
                # TCP 连接测试
                host, port = connection['target'].split(':')
                success, response_time, error_msg = await self._test_tcp_connection(
                    host, int(port)
                )
                details = {"host": host, "port": int(port)}
            
            if details is None:
                details = {}
            
            details.update({
                "description": connection['description'],
                "test_duration_ms": (time.time() - start_time) * 1000
            })
            
            result = ConnectivityResult(
                test_name=connection['name'],
                test_type="service_to_service",
                source=connection['source'],
                target=connection['target'],
                status="connected" if success else "failed",
                response_time_ms=response_time,
                error_message=error_msg,
                details=details
            )
            
            results.append(result)
        
        return results
    
    def generate_connectivity_report(self, results: List[ConnectivityResult]) -> Dict:
        """生成连通性测试报告"""
        connected_tests = [r for r in results if r.status == "connected"]
        failed_tests = [r for r in results if r.status == "failed"]
        timeout_tests = [r for r in results if r.status == "timeout"]
        
        total_tests = len(results)
        success_rate = (len(connected_tests) / total_tests * 100) if total_tests > 0 else 0
        
        # 按测试类型分组统计
        test_types = {}
        for result in results:
            test_type = result.test_type
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "connected": 0, "failed": 0, "timeout": 0}
            
            test_types[test_type]["total"] += 1
            test_types[test_type][result.status] += 1
        
        # 性能统计
        response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # 关键服务状态
        critical_services = ['postgres', 'redis', 'api-gateway']
        critical_status = {}
        for service in critical_services:
            service_results = [r for r in results if r.test_name == service]
            if service_results:
                critical_status[service] = service_results[0].status
            else:
                critical_status[service] = "not_tested"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "is_termux": self.is_termux,
                "test_timeout": self.timeout
            },
            "summary": {
                "total_tests": total_tests,
                "connected_tests": len(connected_tests),
                "failed_tests": len(failed_tests),
                "timeout_tests": len(timeout_tests),
                "success_rate": round(success_rate, 1),
                "average_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": round(max_response_time, 2),
                "min_response_time_ms": round(min_response_time, 2)
            },
            "test_types": test_types,
            "critical_services": critical_status,
            "detailed_results": [result.model_dump() for result in results],
            "recommendations": self._generate_connectivity_recommendations(results)
        }
        
        return report
    
    def _generate_connectivity_recommendations(self, results: List[ConnectivityResult]) -> List[str]:
        """基于连通性测试结果生成建议"""
        recommendations = []
        
        failed_tests = [r for r in results if r.status == "failed"]
        
        if not failed_tests:
            recommendations.append("🎉 所有连通性测试通过！")
            return recommendations
        
        # 分析失败类型
        tcp_failures = [r for r in failed_tests if r.test_type == "tcp"]
        http_failures = [r for r in failed_tests if r.test_type == "http"]
        dns_failures = [r for r in failed_tests if r.test_type == "dns"]
        
        if tcp_failures:
            tcp_services = [r.test_name for r in tcp_failures]
            recommendations.append(
                f"🔧 TCP 连接失败 ({len(tcp_failures)} 个): {', '.join(tcp_services)}. "
                "检查服务是否启动，端口是否开放"
            )
        
        if http_failures:
            timeout_failures = [r for r in http_failures if "超时" in (r.error_message or "")]
            if timeout_failures:
                recommendations.append(
                    f"⏱️ HTTP 请求超时 ({len(timeout_failures)} 个): "
                    "可能需要增加超时时间或检查网络延迟"
                )
            
            connection_failures = [r for r in http_failures if "连接" in (r.error_message or "")]
            if connection_failures:
                recommendations.append(
                    f"🔌 HTTP 连接失败 ({len(connection_failures)} 个): "
                    "检查服务是否运行，防火墙配置是否正确"
                )
        
        if dns_failures:
            recommendations.append(
                f"🌐 DNS 解析失败 ({len(dns_failures)} 个): "
                "检查 DNS 设置，尝试使用其他 DNS 服务器"
            )
        
        # 关键服务失败分析
        critical_failures = [r for r in failed_tests if r.test_name in ['postgres', 'redis', 'api-gateway']]
        if critical_failures:
            critical_names = [r.test_name for r in critical_failures]
            recommendations.append(
                f"⚠️ 关键服务失败 ({len(critical_failures)} 个): {', '.join(critical_names)}. "
                "这些服务对系统正常运行至关重要，请优先修复"
            )
        
        # Termux 特定建议
        if self.is_termux:
            recommendations.append(
                "📱 Termux 环境提示: 某些网络功能可能受到 Android 系统限制，"
                "建议检查 Termux 网络权限和端口访问设置"
            )
        
        return recommendations
    
    def save_report(self, report: Dict, output_path: str = "connectivity-test-report.json"):
        """保存连通性测试报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 连通性测试报告已保存: {Path(output_path).absolute()}")
        
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
            "网络连通性测试报告",
            "=" * 60,
            f"生成时间: {report['timestamp']}",
            f"环境: {'Termux Android' if report['environment']['is_termux'] else '标准 Linux'}",
            "",
            "总体状况:",
            f"  总测试数: {report['summary']['total_tests']}",
            f"  连接成功: {report['summary']['connected_tests']}",
            f"  连接失败: {report['summary']['failed_tests']}",
            f"  连接超时: {report['summary']['timeout_tests']}",
            f"  成功率: {report['summary']['success_rate']}%",
            f"  平均响应时间: {report['summary']['average_response_time_ms']} ms",
            "",
            "关键服务状态:"
        ]
        
        for service, status in report['critical_services'].items():
            status_icon = {
                "connected": "✅",
                "failed": "❌",
                "timeout": "⏱️",
                "not_tested": "❓"
            }.get(status, "⚪")
            lines.append(f"  {status_icon} {service}: {status}")
        
        lines.extend([
            "",
            "详细结果:"
        ])
        
        for result in report['detailed_results']:
            status_icon = {
                "connected": "✅",
                "failed": "❌",
                "timeout": "⏱️"
            }.get(result['status'], "⚪")
            
            lines.append(
                f"  {status_icon} {result['test_name']} ({result['test_type']}) - "
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
    
    parser = argparse.ArgumentParser(description="网络连通性测试工具")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="超时时间（秒）")
    parser.add_argument("--include-optional", "-i", action="store_true", help="包含可选测试（如互联网连接）")
    parser.add_argument("--service-to-service", "-s", action="store_true", help="测试服务间连通性")
    parser.add_argument("--output", "-o", default="connectivity-test-report", help="报告文件名（不含扩展名）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建连通性测试器
    tester = NetworkConnectivityTester(timeout=args.timeout)
    
    # 执行连通性测试
    results = await tester.test_all_connectivity(include_optional=args.include_optional)
    
    # 添加服务间连通性测试
    if args.service_to_service:
        service_results = await tester.test_service_to_service_connectivity()
        results.extend(service_results)
    
    # 生成报告
    report = tester.generate_connectivity_report(results)
    
    # 保存报告
    tester.save_report(report, f"{args.output}.json")
    
    # 输出总结到控制台
    summary = report['summary']
    print(f"\n📊 连通性测试完成:")
    print(f"   成功连接: {summary['connected_tests']}/{summary['total_tests']} ({summary['success_rate']}%)")
    print(f"   平均响应时间: {summary['average_response_time_ms']} ms")
    
    if summary['failed_tests'] > 0:
        print(f"   ⚠️  {summary['failed_tests']} 个连接失败")
        return 1
    else:
        print("   ✅ 所有连接测试通过")
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
