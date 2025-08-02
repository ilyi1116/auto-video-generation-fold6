#!/usr/bin/env python3
"""
增強健康監控系統 - 統一的服務健康檢查與監控
支援多種檢查方式和自動修復機制
"""

import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import aiohttp
import psutil

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康狀態枚舉"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ServiceCheck:
    """服務檢查配置"""

    name: str
    type: str  # http, tcp, process, custom
    target: str  # URL, port, process_name, command
    timeout: int = 10
    interval: int = 30
    retries: int = 3
    expected_response: Optional[str] = None
    auto_restart: bool = False
    restart_command: Optional[str] = None


@dataclass
class HealthResult:
    """健康檢查結果"""

    service: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return {
            **asdict(self),
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


class HealthMonitor:
    """健康監控器"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or "monitoring/health_config.json"
        self.services: List[ServiceCheck] = []
        self.results: Dict[str, HealthResult] = {}
        self.running = True

        # 載入配置
        self._load_config()

        # 初始化監控目錄
        self.monitor_dir = Path("monitoring/health")
        self.monitor_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """載入健康檢查配置"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.services = [
                    ServiceCheck(**service_data)
                    for service_data in data.get("services", [])
                ]
            else:
                # 使用預設配置
                self._create_default_config()

        except Exception as e:
            logger.error(f"載入健康檢查配置失敗: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """創建預設健康檢查配置"""
        default_services = [
            ServiceCheck(
                name="frontend",
                type="http",
                target="http://localhost:3000",
                timeout=10,
                interval=30,
                auto_restart=True,
                restart_command="bash scripts/start_frontend.sh",
            ),
            ServiceCheck(
                name="backend",
                type="http",
                target="http://localhost:8000/health",
                timeout=10,
                interval=30,
                auto_restart=True,
                restart_command="bash scripts/start_backend.sh",
            ),
            ServiceCheck(
                name="redis",
                type="tcp",
                target="localhost:6379",
                timeout=5,
                interval=60,
            ),
            ServiceCheck(
                name="disk_space",
                type="custom",
                target="check_disk_space",
                interval=300,  # 5分鐘
            ),
            ServiceCheck(
                name="memory_usage",
                type="custom",
                target="check_memory_usage",
                interval=60,
            ),
        ]

        self.services = default_services

        # 保存預設配置
        try:
            config_data = {
                "services": [asdict(service) for service in self.services]
            }

            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存預設配置失敗: {e}")

    async def _check_http_service(self, service: ServiceCheck) -> HealthResult:
        """檢查 HTTP 服務"""
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=service.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(service.target) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        # 檢查響應內容 (如果指定)
                        if service.expected_response:
                            text = await response.text()
                            if service.expected_response in text:
                                status = HealthStatus.HEALTHY
                                message = "HTTP 200 OK, 響應內容匹配"
                            else:
                                status = HealthStatus.WARNING
                                message = "HTTP 200 OK, 但響應內容不匹配"
                        else:
                            status = HealthStatus.HEALTHY
                            message = "HTTP 200 OK"
                    else:
                        status = HealthStatus.WARNING
                        message = f"HTTP {response.status}"

                    return HealthResult(
                        service=service.name,
                        status=status,
                        response_time=response_time,
                        message=message,
                        timestamp=datetime.now(),
                        metadata={"status_code": response.status},
                    )

        except asyncio.TimeoutError:
            return HealthResult(
                service=service.name,
                status=HealthStatus.CRITICAL,
                response_time=service.timeout,
                message="請求超時",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthResult(
                service=service.name,
                status=HealthStatus.DOWN,
                response_time=time.time() - start_time,
                message=f"連接失敗: {str(e)}",
                timestamp=datetime.now(),
            )

    async def _check_tcp_service(self, service: ServiceCheck) -> HealthResult:
        """檢查 TCP 服務"""
        start_time = time.time()

        try:
            # 解析主機和端口
            if ":" in service.target:
                host, port = service.target.split(":")
                port = int(port)
            else:
                host = service.target
                port = 80

            # 嘗試建立 TCP 連接
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(
                future, timeout=service.timeout
            )

            writer.close()
            await writer.wait_closed()

            response_time = time.time() - start_time

            return HealthResult(
                service=service.name,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="TCP 連接成功",
                timestamp=datetime.now(),
                metadata={"host": host, "port": port},
            )

        except asyncio.TimeoutError:
            return HealthResult(
                service=service.name,
                status=HealthStatus.CRITICAL,
                response_time=service.timeout,
                message="TCP 連接超時",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthResult(
                service=service.name,
                status=HealthStatus.DOWN,
                response_time=time.time() - start_time,
                message=f"TCP 連接失敗: {str(e)}",
                timestamp=datetime.now(),
            )

    async def _check_custom_service(
        self, service: ServiceCheck
    ) -> HealthResult:
        """檢查自定義服務"""
        start_time = time.time()

        try:
            if service.target == "check_disk_space":
                return await self._check_disk_space(service, start_time)
            elif service.target == "check_memory_usage":
                return await self._check_memory_usage(service, start_time)
            else:
                # 執行自定義命令
                process = await asyncio.create_subprocess_shell(
                    service.target,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=service.timeout
                )

                response_time = time.time() - start_time

                if process.returncode == 0:
                    status = HealthStatus.HEALTHY
                    message = stdout.decode().strip() or "命令執行成功"
                else:
                    status = HealthStatus.CRITICAL
                    message = (
                        stderr.decode().strip()
                        or f"命令執行失敗 (退出代碼: {process.returncode})"
                    )

                return HealthResult(
                    service=service.name,
                    status=status,
                    response_time=response_time,
                    message=message,
                    timestamp=datetime.now(),
                    metadata={"exit_code": process.returncode},
                )

        except asyncio.TimeoutError:
            return HealthResult(
                service=service.name,
                status=HealthStatus.CRITICAL,
                response_time=service.timeout,
                message="自定義檢查超時",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthResult(
                service=service.name,
                status=HealthStatus.DOWN,
                response_time=time.time() - start_time,
                message=f"自定義檢查失敗: {str(e)}",
                timestamp=datetime.now(),
            )

    async def _check_disk_space(
        self, service: ServiceCheck, start_time: float
    ) -> HealthResult:
        """檢查磁盤空間"""
        try:
            disk_usage = psutil.disk_usage("/")
            used_percent = (disk_usage.used / disk_usage.total) * 100
            free_gb = disk_usage.free / (1024**3)

            response_time = time.time() - start_time

            if used_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"磁盤空間嚴重不足: {used_percent:.1f}% 已使用"
            elif used_percent > 80:
                status = HealthStatus.WARNING
                message = f"磁盤空間不足: {used_percent:.1f}% 已使用"
            else:
                status = HealthStatus.HEALTHY
                message = f"磁盤空間正常: {used_percent:.1f}% 已使用"

            return HealthResult(
                service=service.name,
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.now(),
                metadata={
                    "used_percent": used_percent,
                    "free_gb": free_gb,
                    "total_gb": disk_usage.total / (1024**3),
                },
            )

        except Exception as e:
            return HealthResult(
                service=service.name,
                status=HealthStatus.UNKNOWN,
                response_time=time.time() - start_time,
                message=f"無法檢查磁盤空間: {str(e)}",
                timestamp=datetime.now(),
            )

    async def _check_memory_usage(
        self, service: ServiceCheck, start_time: float
    ) -> HealthResult:
        """檢查記憶體使用"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            available_gb = memory.available / (1024**3)

            response_time = time.time() - start_time

            if used_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"記憶體使用過高: {used_percent:.1f}%"
            elif used_percent > 80:
                status = HealthStatus.WARNING
                message = f"記憶體使用偏高: {used_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"記憶體使用正常: {used_percent:.1f}%"

            return HealthResult(
                service=service.name,
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.now(),
                metadata={
                    "used_percent": used_percent,
                    "available_gb": available_gb,
                    "total_gb": memory.total / (1024**3),
                },
            )

        except Exception as e:
            return HealthResult(
                service=service.name,
                status=HealthStatus.UNKNOWN,
                response_time=time.time() - start_time,
                message=f"無法檢查記憶體使用: {str(e)}",
                timestamp=datetime.now(),
            )

    async def check_service(self, service: ServiceCheck) -> HealthResult:
        """檢查單個服務"""
        logger.debug(f"檢查服務: {service.name}")

        # 根據服務類型執行相應檢查
        if service.type == "http":
            result = await self._check_http_service(service)
        elif service.type == "tcp":
            result = await self._check_tcp_service(service)
        elif service.type == "custom":
            result = await self._check_custom_service(service)
        else:
            result = HealthResult(
                service=service.name,
                status=HealthStatus.UNKNOWN,
                response_time=0,
                message=f"不支援的檢查類型: {service.type}",
                timestamp=datetime.now(),
            )

        # 重試機制
        if (
            result.status in [HealthStatus.CRITICAL, HealthStatus.DOWN]
            and service.retries > 0
        ):
            for retry in range(service.retries):
                logger.info(f"重試檢查 {service.name} (第 {retry + 1} 次)")
                await asyncio.sleep(2)  # 等待2秒再重試

                if service.type == "http":
                    retry_result = await self._check_http_service(service)
                elif service.type == "tcp":
                    retry_result = await self._check_tcp_service(service)
                elif service.type == "custom":
                    retry_result = await self._check_custom_service(service)

                if retry_result.status not in [
                    HealthStatus.CRITICAL,
                    HealthStatus.DOWN,
                ]:
                    result = retry_result
                    result.message += f" (重試 {retry + 1} 次後成功)"
                    break

        # 自動重啟機制
        if (
            result.status in [HealthStatus.CRITICAL, HealthStatus.DOWN]
            and service.auto_restart
            and service.restart_command
        ):
            logger.warning(f"嘗試自動重啟服務: {service.name}")
            await self._restart_service(service)

        return result

    async def _restart_service(self, service: ServiceCheck):
        """重啟服務"""
        try:
            logger.info(f"執行重啟命令: {service.restart_command}")

            process = await asyncio.create_subprocess_shell(
                service.restart_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"服務 {service.name} 重啟成功")
            else:
                logger.error(
                    f"服務 {service.name} 重啟失敗: {stderr.decode()}"
                )

        except Exception as e:
            logger.error(f"重啟服務 {service.name} 時發生錯誤: {e}")

    async def check_all_services(self) -> Dict[str, HealthResult]:
        """檢查所有服務"""
        tasks = []
        for service in self.services:
            task = asyncio.create_task(self.check_service(service))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"檢查服務 {self.services[i].name} 時發生錯誤: {result}"
                )
                result = HealthResult(
                    service=self.services[i].name,
                    status=HealthStatus.UNKNOWN,
                    response_time=0,
                    message=f"檢查失敗: {str(result)}",
                    timestamp=datetime.now(),
                )

            self.results[result.service] = result

        return self.results

    async def save_results(self):
        """保存檢查結果"""
        try:
            # 保存最新結果
            latest_file = self.monitor_dir / "latest_results.json"
            results_data = {
                "timestamp": datetime.now().isoformat(),
                "results": {
                    name: result.to_dict()
                    for name, result in self.results.items()
                },
            }

            async with aiofiles.open(latest_file, "w", encoding="utf-8") as f:
                await f.write(
                    json.dumps(results_data, indent=2, ensure_ascii=False)
                )

            # 保存歷史記錄
            history_file = (
                self.monitor_dir
                / f"health_history_{datetime.now().strftime('%Y%m%d')}.jsonl"
            )

            async with aiofiles.open(history_file, "a", encoding="utf-8") as f:
                await f.write(
                    json.dumps(results_data, ensure_ascii=False) + "\n"
                )

            logger.debug("健康檢查結果已保存")

        except Exception as e:
            logger.error(f"保存健康檢查結果失敗: {e}")

    def get_overall_status(self) -> HealthStatus:
        """獲取系統整體健康狀態"""
        if not self.results:
            return HealthStatus.UNKNOWN

        statuses = [result.status for result in self.results.values()]

        if HealthStatus.DOWN in statuses:
            return HealthStatus.DOWN
        elif HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def get_summary(self) -> Dict[str, Any]:
        """獲取健康檢查摘要"""
        overall_status = self.get_overall_status()

        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = sum(
                1
                for result in self.results.values()
                if result.status == status
            )

        return {
            "overall_status": overall_status.value,
            "total_services": len(self.services),
            "status_counts": status_counts,
            "last_check": datetime.now().isoformat(),
            "services": {
                name: result.to_dict() for name, result in self.results.items()
            },
        }

    async def run_continuous_monitoring(self):
        """持續監控模式"""
        logger.info("啟動健康監控系統...")

        while self.running:
            try:
                # 執行健康檢查
                await self.check_all_services()

                # 保存結果
                await self.save_results()

                # 記錄狀態
                overall_status = self.get_overall_status()
                logger.info(f"系統整體狀態: {overall_status.value}")

                # 如果有嚴重問題，記錄詳細信息
                for name, result in self.results.items():
                    if result.status in [
                        HealthStatus.CRITICAL,
                        HealthStatus.DOWN,
                    ]:
                        logger.warning(
                            f"服務 {name} 狀態異常: {result.message}"
                        )

                # 等待下次檢查 (使用最小間隔)
                min_interval = min(
                    service.interval for service in self.services
                )
                await asyncio.sleep(min_interval)

            except Exception as e:
                logger.error(f"健康監控執行錯誤: {e}")
                await asyncio.sleep(30)  # 錯誤時等待30秒

    def stop(self):
        """停止監控"""
        logger.info("停止健康監控系統...")
        self.running = False


async def main():
    """主函數 - 健康檢查服務"""
    monitor = HealthMonitor()

    import signal

    def signal_handler(signum, frame):
        logger.info(f"收到信號 {signum}，正在停止...")
        monitor.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "once":
            # 單次檢查模式
            logger.info("執行單次健康檢查...")
            await monitor.check_all_services()
            await monitor.save_results()

            summary = monitor.get_summary()
            print(json.dumps(summary, indent=2, ensure_ascii=False))

        else:
            # 持續監控模式
            await monitor.run_continuous_monitoring()

    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在停止...")
    finally:
        monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
