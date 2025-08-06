#!/usr/bin/env python3
"""
服務健康檢查腳本
檢查所有微服務的健康狀態和可用性
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp

# 設置日誌
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class ServiceHealthChecker:
    """服務健康檢查器"""

    def __init__(self):
        self.services = {
            "api-gateway": {
                "url": "http://localhost:8000",
                "health_path": "/health",
                "critical": True,
            },
            "auth-service": {
                "url": "http://localhost:8001",
                "health_path": "/health",
                "critical": True,
            },
            "data-service": {
                "url": "http://localhost:8002",
                "health_path": "/health",
                "critical": True,
            },
            "inference-service": {
                "url": "http://localhost:8003",
                "health_path": "/health",
                "critical": True,
            },
            "video-service": {
                "url": "http://localhost:8004",
                "health_path": "/health",
                "critical": False,
            },
            "ai-service": {
                "url": "http://localhost:8005",
                "health_path": "/health",
                "critical": False,
            },
            "social-service": {
                "url": "http://localhost:8006",
                "health_path": "/health",
                "critical": False,
            },
            "trend-service": {
                "url": "http://localhost:8007",
                "health_path": "/health",
                "critical": False,
            },
            "scheduler-service": {
                "url": "http://localhost:8008",
                "health_path": "/health",
                "critical": False,
            },
            "storage-service": {
                "url": "http://localhost:8009",
                "health_path": "/health",
                "critical": True,
            },
        }

        self.infrastructure = {
            "postgres": {
                "url": "http://localhost:5432",
                "check_type": "tcp",
                "critical": True,
            },
            "redis": {
                "url": "http://localhost:6379",
                "check_type": "tcp",
                "critical": True,
            },
            "prometheus": {
                "url": "http://localhost:9090",
                "health_path": "/-/healthy",
                "critical": False,
            },
            "grafana": {
                "url": "http://localhost:3000",
                "health_path": "/api/health",
                "critical": False,
            },
        }

        self.results = {}

    async def check_http_health(
        self, session: aiohttp.ClientSession, name: str, config: Dict
    ) -> Dict:
        """檢查 HTTP 服務健康狀態"""
        url = config["url"] + config.get("health_path", "/health")
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with session.get(url, timeout=timeout) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    try:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time": round(response_time * 1000, 2),
                            "data": data,
                            "http_status": response.status,
                        }
                    except Exception:
                        return {
                            "status": "healthy",
                            "response_time": round(response_time * 1000, 2),
                            "data": {"message": "OK"},
                            "http_status": response.status,
                        }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time": round(response_time * 1000, 2),
                        "error": f"HTTP {response.status}",
                        "http_status": response.status,
                    }

        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "response_time": round((time.time() - start_time) * 1000, 2),
                "error": "Request timeout",
            }
        except Exception as e:
            return {
                "status": "error",
                "response_time": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    async def check_tcp_port(self, host: str, port: int) -> Dict:
        """檢查 TCP 端口連接"""
        start_time = time.time()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5.0
            )
            writer.close()
            await writer.wait_closed()

            response_time = time.time() - start_time
            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),
                "message": f"Port {port} is open",
            }

        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "response_time": round((time.time() - start_time) * 1000, 2),
                "error": "Connection timeout",
            }
        except Exception as e:
            return {
                "status": "error",
                "response_time": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    async def check_all_services(self) -> None:
        """檢查所有服務"""
        logger.info("🏥 Starting health checks...")
        logger.info("=" * 60)

        async with aiohttp.ClientSession() as session:
            # 檢查微服務
            logger.info("🔍 Checking Microservices:")
            logger.info("-" * 30)

            for name, config in self.services.items():
                result = await self.check_http_health(session, name, config)
                self.results[name] = {**result, "critical": config["critical"]}

                status_icon = self._get_status_icon(result["status"])
                critical_marker = " 🔴" if config["critical"] else ""

                logger.info(
                    f"{status_icon} {name:<20} {result['response_time']:>6}ms{critical_marker}"
                )

                if result["status"] not in ["healthy"] and "error" in result:
                    logger.info(f"   └─ Error: {result['error']}")

            # 檢查基礎設施
            logger.info("\n🔍 Checking Infrastructure:")
            logger.info("-" * 30)

            for name, config in self.infrastructure.items():
                if config.get("check_type") == "tcp":
                    # 解析 URL 獲取主機和端口
                    import urllib.parse

                    parsed = urllib.parse.urlparse(config["url"])
                    result = await self.check_tcp_port(
                        parsed.hostname or "localhost", parsed.port
                    )
                else:
                    result = await self.check_http_health(
                        session, name, config
                    )

                self.results[name] = {**result, "critical": config["critical"]}

                status_icon = self._get_status_icon(result["status"])
                critical_marker = " 🔴" if config["critical"] else ""

                logger.info(
                    f"{status_icon} {name:<20} {result['response_time']:>6}ms{critical_marker}"
                )

                if result["status"] not in ["healthy"] and "error" in result:
                    logger.info(f"   └─ Error: {result['error']}")

    def _get_status_icon(self, status: str) -> str:
        """獲取狀態圖標"""
        icons = {
            "healthy": "✅",
            "unhealthy": "❌",
            "timeout": "⏰",
            "error": "🚫",
        }
        return icons.get(status, "❓")

    def generate_summary(self) -> Tuple[int, int, int]:
        """生成摘要統計"""
        healthy = sum(
            1 for r in self.results.values() if r["status"] == "healthy"
        )
        critical_failures = sum(
            1
            for r in self.results.values()
            if r["status"] != "healthy" and r.get("critical", False)
        )
        total_failures = sum(
            1 for r in self.results.values() if r["status"] != "healthy"
        )

        logger.info("\n" + "=" * 60)
        logger.info("📊 HEALTH CHECK SUMMARY")
        logger.info("=" * 60)

        total_services = len(self.results)
        logger.info(f"Total Services: {total_services}")
        logger.info(f"✅ Healthy: {healthy}")
        logger.info(f"❌ Failed: {total_failures}")
        logger.info(f"🔴 Critical Failures: {critical_failures}")

        # 顯示系統狀態
        if critical_failures > 0:
            logger.info(
                f"\n🚨 SYSTEM STATUS: CRITICAL - {critical_failures} critical services down"
            )
            system_status = 2
        elif total_failures > 0:
            logger.info(
                f"\n⚠️  SYSTEM STATUS: DEGRADED - {total_failures} services down"
            )
            system_status = 1
        else:
            logger.info(
                "\n✅ SYSTEM STATUS: HEALTHY - All services operational"
            )
            system_status = 0

        # 顯示建議
        if critical_failures > 0:
            logger.info("\n💡 RECOMMENDATIONS:")
            logger.info(
                "  • Investigate critical service failures immediately"
            )
            logger.info("  • Check Docker containers: docker-compose ps")
            logger.info(
                "  • Review service logs: docker-compose logs <service>"
            )
        elif total_failures > 0:
            logger.info("\n💡 RECOMMENDATIONS:")
            logger.info("  • Monitor non-critical service failures")
            logger.info("  • Consider restarting failed services")

        logger.info("=" * 60)

        return system_status, healthy, total_failures

    def save_report(self) -> None:
        """保存健康檢查報告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": {
                "total_services": len(self.results),
                "healthy": sum(
                    1
                    for r in self.results.values()
                    if r["status"] == "healthy"
                ),
                "failed": sum(
                    1
                    for r in self.results.values()
                    if r["status"] != "healthy"
                ),
                "critical_failures": sum(
                    1
                    for r in self.results.values()
                    if r["status"] != "healthy" and r.get("critical", False)
                ),
            },
        }

        with open("health-check-report.json", "w") as f:
            json.dump(report, f, indent=2)

        logger.info(
            "📄 Health check report saved to: health-check-report.json"
        )


async def main():
    """主要健康檢查流程"""
    checker = ServiceHealthChecker()

    try:
        await checker.check_all_services()
        system_status, healthy, failed = checker.generate_summary()

        # 保存報告
        checker.save_report()

        return system_status

    except KeyboardInterrupt:
        logger.info("\nHealth check interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during health check: {str(e)}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Failed to run health check: {str(e)}")
        sys.exit(1)
