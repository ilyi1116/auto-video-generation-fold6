#!/usr/bin/env python3
"""
服務管理器 - 統一的服務啟動、停止、監控管理
支援依賴管理、優雅啟動/停止、健康檢查整合
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """服務狀態枚舉"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ServiceConfig:
    """服務配置"""

    name: str
    command: str
    working_dir: str = "."
    env_vars: Dict[str, str] = None
    dependencies: List[str] = None
    health_check_url: Optional[str] = None
    startup_timeout: int = 60
    shutdown_timeout: int = 30
    auto_restart: bool = False
    restart_delay: int = 5
    max_restarts: int = 3


@dataclass
class ServiceStatus:
    """服務狀態"""

    name: str
    state: ServiceState
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_error: Optional[str] = None
    health_status: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return {
            **asdict(self),
            "state": self.state.value,
            "start_time": (
                self.start_time.isoformat() if self.start_time else None
            ),
            "metadata": self.metadata or {},
        }


class ServiceManager:
    """服務管理器"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or "config/services.json"
        self.services: Dict[str, ServiceConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status: Dict[str, ServiceStatus] = {}
        self.running = True

        # PID 檔案目錄
        self.pid_dir = Path("logs/pids")
        self.pid_dir.mkdir(parents=True, exist_ok=True)

        # 載入配置
        self._load_config()

        # 設置信號處理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"收到信號 {signum}，正在優雅關閉...")
        asyncio.create_task(self.stop_all_services())
        self.running = False

    def _load_config(self):
        """載入服務配置"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for service_data in data.get("services", []):
                    service = ServiceConfig(**service_data)
                    self.services[service.name] = service
                    self.status[service.name] = ServiceStatus(
                        name=service.name, state=ServiceState.STOPPED
                    )
            else:
                self._create_default_config()

        except Exception as e:
            logger.error(f"載入服務配置失敗: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """創建預設服務配置"""
        default_services = [
            ServiceConfig(
                name="redis",
                command="redis-server config/redis.con",
                working_dir=".",
                health_check_url="redis://localhost:6379",
                startup_timeout=30,
                auto_restart=True,
            ),
            ServiceConfig(
                name="backend",
                command="python -m uvicorn main:app --host 0.0.0.0 --port 8000",
                working_dir="services/api-gateway",
                dependencies=["redis"],
                health_check_url="http://localhost:8000/health",
                startup_timeout=60,
                auto_restart=True,
                env_vars={"PYTHONPATH": "."},
            ),
            ServiceConfig(
                name="ai-service",
                command="python -m uvicorn main:app --host 0.0.0.0 --port 8001",
                working_dir="services/ai-service",
                dependencies=["redis"],
                health_check_url="http://localhost:8001/health",
                startup_timeout=90,
                auto_restart=True,
                env_vars={"PYTHONPATH": "."},
            ),
            ServiceConfig(
                name="video-service",
                command="python -m uvicorn main:app --host 0.0.0.0 --port 8002",
                working_dir="services/video-service",
                dependencies=["redis"],
                health_check_url="http://localhost:8002/health",
                startup_timeout=60,
                auto_restart=True,
                env_vars={"PYTHONPATH": "."},
            ),
            ServiceConfig(
                name="frontend",
                command="npm run preview -- --host 0.0.0.0 --port 3000",
                working_dir="frontend",
                dependencies=["backend"],
                health_check_url="http://localhost:3000",
                startup_timeout=45,
                auto_restart=True,
            ),
            ServiceConfig(
                name="scheduler",
                command="python scripts/scheduler.py",
                working_dir=".",
                dependencies=["backend", "ai-service"],
                startup_timeout=30,
                auto_restart=True,
                env_vars={"PYTHONPATH": "."},
            ),
        ]

        for service in default_services:
            self.services[service.name] = service
            self.status[service.name] = ServiceStatus(
                name=service.name, state=ServiceState.STOPPED
            )

        # 保存預設配置
        self._save_config()

    def _save_config(self):
        """保存服務配置"""
        try:
            config_data = {
                "services": [
                    asdict(service) for service in self.services.values()
                ]
            }

            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存服務配置失敗: {e}")

    def _get_pid_file(self, service_name: str) -> Path:
        """獲取 PID 檔案路徑"""
        return self.pid_dir / f"{service_name}.pid"

    def _save_pid(self, service_name: str, pid: int):
        """保存 PID 到檔案"""
        try:
            pid_file = self._get_pid_file(service_name)
            with open(pid_file, "w") as f:
                f.write(str(pid))
        except Exception as e:
            logger.error(f"保存 PID 檔案失敗: {e}")

    def _load_pid(self, service_name: str) -> Optional[int]:
        """從檔案載入 PID"""
        try:
            pid_file = self._get_pid_file(service_name)
            if pid_file.exists():
                with open(pid_file, "r") as f:
                    return int(f.read().strip())
        except Exception as e:
            logger.debug(f"載入 PID 檔案失敗: {e}")
        return None

    def _remove_pid_file(self, service_name: str):
        """移除 PID 檔案"""
        try:
            pid_file = self._get_pid_file(service_name)
            if pid_file.exists():
                pid_file.unlink()
        except Exception as e:
            logger.debug(f"移除 PID 檔案失敗: {e}")

    async def _check_dependencies(self, service_name: str) -> bool:
        """檢查服務依賴是否滿足"""
        service = self.services[service_name]
        if not service.dependencies:
            return True

        for dep in service.dependencies:
            if dep not in self.status:
                logger.error(f"服務 {service_name} 的依賴 {dep} 不存在")
                return False

            if self.status[dep].state != ServiceState.RUNNING:
                logger.warning(f"服務 {service_name} 的依賴 {dep} 未運行")
                return False

        return True

    async def _wait_for_health_check(self, service_name: str) -> bool:
        """等待服務健康檢查通過"""
        service = self.services[service_name]
        if not service.health_check_url:
            return True

        logger.info(f"等待服務 {service_name} 健康檢查...")

        import aiohttp

        start_time = time.time()
        while time.time() - start_time < service.startup_timeout:
            try:
                if service.health_check_url.startswith("http"):
                    # HTTP 健康檢查
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(
                        timeout=timeout
                    ) as session:
                        async with session.get(
                            service.health_check_url
                        ) as response:
                            if response.status == 200:
                                logger.info(
                                    f"服務 {service_name} 健康檢查通過"
                                )
                                return True

                elif service.health_check_url.startswith("redis://"):
                    # Redis 健康檢查
                    try:
                        import redis

                        r = redis.Redis(
                            host="localhost", port=6379, decode_responses=True
                        )
                        r.ping()
                        logger.info(f"服務 {service_name} 健康檢查通過")
                        return True
                    except Exception:
                        pass

            except Exception as e:
                logger.debug(f"健康檢查失敗: {e}")

            await asyncio.sleep(2)

        logger.warning(f"服務 {service_name} 健康檢查超時")
        return False

    async def start_service(self, service_name: str) -> bool:
        """啟動單個服務"""
        if service_name not in self.services:
            logger.error(f"服務 {service_name} 不存在")
            return False

        service = self.services[service_name]
        status = self.status[service_name]

        # 檢查是否已經在運行
        if status.state == ServiceState.RUNNING:
            logger.info(f"服務 {service_name} 已經在運行")
            return True

        # 檢查依賴
        if not await self._check_dependencies(service_name):
            logger.error(f"服務 {service_name} 依賴檢查失敗")
            status.state = ServiceState.FAILED
            status.last_error = "依賴檢查失敗"
            return False

        logger.info(f"啟動服務: {service_name}")
        status.state = ServiceState.STARTING

        try:
            # 準備環境變數
            env = os.environ.copy()
            if service.env_vars:
                env.update(service.env_vars)

            # 啟動進程
            process = subprocess.Popen(
                service.command,
                shell=True,
                cwd=service.working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            self.processes[service_name] = process
            status.pid = process.pid
            status.start_time = datetime.now()
            status.restart_count = 0

            # 保存 PID
            self._save_pid(service_name, process.pid)

            # 等待健康檢查
            if await self._wait_for_health_check(service_name):
                status.state = ServiceState.RUNNING
                status.health_status = "healthy"
                logger.info(
                    f"服務 {service_name} 啟動成功 (PID: {process.pid})"
                )
                return True
            else:
                # 健康檢查失敗，停止進程
                await self.stop_service(service_name)
                status.state = ServiceState.FAILED
                status.last_error = "健康檢查失敗"
                logger.error(f"服務 {service_name} 啟動失敗: 健康檢查超時")
                return False

        except Exception as e:
            status.state = ServiceState.FAILED
            status.last_error = str(e)
            logger.error(f"啟動服務 {service_name} 時發生錯誤: {e}")
            return False

    async def stop_service(self, service_name: str) -> bool:
        """停止單個服務"""
        if service_name not in self.services:
            logger.error(f"服務 {service_name} 不存在")
            return False

        service = self.services[service_name]
        status = self.status[service_name]

        if status.state == ServiceState.STOPPED:
            logger.info(f"服務 {service_name} 已經停止")
            return True

        logger.info(f"停止服務: {service_name}")
        status.state = ServiceState.STOPPING

        try:
            # 首先嘗試從 PID 檔案獲取 PID
            pid = status.pid or self._load_pid(service_name)

            if pid and psutil.pid_exists(pid):
                # 優雅停止
                try:
                    process = psutil.Process(pid)
                    process.terminate()

                    # 等待進程優雅退出
                    try:
                        process.wait(timeout=service.shutdown_timeout)
                    except psutil.TimeoutExpired:
                        logger.warning(
                            f"服務 {service_name} 優雅停止超時，強制終止"
                        )
                        process.kill()
                        process.wait(timeout=10)

                    logger.info(f"服務 {service_name} 已停止")

                except psutil.NoSuchProcess:
                    logger.info(f"服務 {service_name} 進程已不存在")

            # 清理
            if service_name in self.processes:
                del self.processes[service_name]

            self._remove_pid_file(service_name)

            status.state = ServiceState.STOPPED
            status.pid = None
            status.health_status = None

            return True

        except Exception as e:
            status.last_error = str(e)
            logger.error(f"停止服務 {service_name} 時發生錯誤: {e}")
            return False

    async def restart_service(self, service_name: str) -> bool:
        """重啟服務"""
        logger.info(f"重啟服務: {service_name}")

        await self.stop_service(service_name)
        await asyncio.sleep(2)  # 等待2秒

        return await self.start_service(service_name)

    def _get_startup_order(self) -> List[str]:
        """獲取服務啟動順序 (基於依賴關係)"""
        # 簡單的拓撲排序
        ordered = []
        remaining = set(self.services.keys())

        while remaining:
            # 找到沒有未滿足依賴的服務
            ready = []
            for service_name in remaining:
                service = self.services[service_name]
                if not service.dependencies or all(
                    dep in ordered for dep in service.dependencies
                ):
                    ready.append(service_name)

            if not ready:
                # 循環依賴，按名稱排序
                ready = sorted(remaining)
                logger.warning("檢測到循環依賴，使用字母順序啟動")

            for service_name in ready:
                ordered.append(service_name)
                remaining.remove(service_name)

        return ordered

    async def start_all_services(self) -> bool:
        """啟動所有服務"""
        logger.info("啟動所有服務...")

        startup_order = self._get_startup_order()
        success_count = 0

        for service_name in startup_order:
            if await self.start_service(service_name):
                success_count += 1
            else:
                logger.error(f"服務 {service_name} 啟動失敗，繼續啟動其他服務")

        total_services = len(self.services)
        logger.info(f"服務啟動完成: {success_count}/{total_services} 成功")

        return success_count == total_services

    async def stop_all_services(self) -> bool:
        """停止所有服務"""
        logger.info("停止所有服務...")

        # 反向依賴順序停止
        startup_order = self._get_startup_order()
        shutdown_order = list(reversed(startup_order))

        success_count = 0

        for service_name in shutdown_order:
            if await self.stop_service(service_name):
                success_count += 1

        total_services = len(self.services)
        logger.info(f"服務停止完成: {success_count}/{total_services} 成功")

        return success_count == total_services

    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """獲取服務狀態"""
        return self.status.get(service_name)

    def get_all_status(self) -> Dict[str, ServiceStatus]:
        """獲取所有服務狀態"""
        return self.status.copy()

    def get_system_summary(self) -> Dict[str, Any]:
        """獲取系統摘要"""
        states = [status.state for status in self.status.values()]

        return {
            "total_services": len(self.services),
            "running": sum(
                1 for state in states if state == ServiceState.RUNNING
            ),
            "stopped": sum(
                1 for state in states if state == ServiceState.STOPPED
            ),
            "failed": sum(
                1 for state in states if state == ServiceState.FAILED
            ),
            "starting": sum(
                1 for state in states if state == ServiceState.STARTING
            ),
            "stopping": sum(
                1 for state in states if state == ServiceState.STOPPING
            ),
            "services": {
                name: status.to_dict() for name, status in self.status.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def monitor_services(self):
        """監控服務狀態"""
        logger.info("啟動服務監控...")

        while self.running:
            try:
                for service_name, status in self.status.items():
                    if status.state == ServiceState.RUNNING and status.pid:
                        # 檢查進程是否還存在
                        if not psutil.pid_exists(status.pid):
                            logger.warning(f"服務 {service_name} 進程已終止")
                            status.state = ServiceState.FAILED
                            status.last_error = "進程意外終止"

                            # 自動重啟 (如果啟用)
                            service = self.services[service_name]
                            if (
                                service.auto_restart
                                and status.restart_count < service.max_restarts
                            ):
                                logger.info(
                                    f"自動重啟服務 {service_name} (第 {status.restart_count + 1} 次)"
                                )
                                status.restart_count += 1

                                await asyncio.sleep(service.restart_delay)
                                await self.start_service(service_name)

                await asyncio.sleep(10)  # 每10秒檢查一次

            except Exception as e:
                logger.error(f"服務監控錯誤: {e}")
                await asyncio.sleep(30)


async def main():
    """主函數"""
    if len(sys.argv) < 2:
        print(
            "使用方法: python service_manager.py [start|stop|restart|status|monitor] [service_name]"
        )
        return

    manager = ServiceManager()
    command = sys.argv[1]
    service_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        if command == "start":
            if service_name:
                success = await manager.start_service(service_name)
                print(
                    f"服務 {service_name} 啟動 {'成功' if success else '失敗'}"
                )
            else:
                success = await manager.start_all_services()
                print(f"所有服務啟動 {'成功' if success else '失敗'}")

        elif command == "stop":
            if service_name:
                success = await manager.stop_service(service_name)
                print(
                    f"服務 {service_name} 停止 {'成功' if success else '失敗'}"
                )
            else:
                success = await manager.stop_all_services()
                print(f"所有服務停止 {'成功' if success else '失敗'}")

        elif command == "restart":
            if service_name:
                success = await manager.restart_service(service_name)
                print(
                    f"服務 {service_name} 重啟 {'成功' if success else '失敗'}"
                )
            else:
                await manager.stop_all_services()
                await asyncio.sleep(3)
                success = await manager.start_all_services()
                print(f"所有服務重啟 {'成功' if success else '失敗'}")

        elif command == "status":
            if service_name:
                status = manager.get_service_status(service_name)
                if status:
                    print(
                        json.dumps(
                            status.to_dict(), indent=2, ensure_ascii=False
                        )
                    )
                else:
                    print(f"服務 {service_name} 不存在")
            else:
                summary = manager.get_system_summary()
                print(json.dumps(summary, indent=2, ensure_ascii=False))

        elif command == "monitor":
            await manager.monitor_services()

        else:
            print(f"未知命令: {command}")

    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在停止...")
        await manager.stop_all_services()


if __name__ == "__main__":
    asyncio.run(main())
