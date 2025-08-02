#!/usr/bin/env python3
"""
綜合備份與災難恢復系統
自動化數據備份、監控備份狀態並提供災難恢復機制
"""

import asyncio
import logging
import os
import tarfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import schedule
import yaml
from cryptography.fernet import Fernet


@dataclass
class BackupJob:
    """備份任務資料結構"""

    name: str
    type: str  # database, files, container, configuration
    source: str
    destination: str
    schedule: str  # cron expression
    encryption: bool
    compression: bool
    retention_days: int
    priority: str  # high, medium, low
    dependencies: List[str]


@dataclass
class BackupResult:
    """備份結果資料結構"""

    job_name: str
    start_time: datetime
    end_time: datetime
    status: str  # success, failed, partial
    size_bytes: int
    duration_seconds: float
    error_message: Optional[str] = None
    backup_path: Optional[str] = None
    checksum: Optional[str] = None


class BackupSystem:
    """備份系統主類"""

    def __init__(self, config_path: str = "./scripts/backup/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = self._setup_logging()

        # 加密金鑰
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)

        # S3 客戶端 (如果配置)
        self.s3_client = self._setup_s3_client()

        # 備份歷史
        self.backup_history = []

    def _load_config(self) -> Dict[str, Any]:
        """載入配置檔案"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "backup": {
                "base_path": "/var/backups/auto-video",
                "encryption": True,
                "compression": True,
                "checksum_verification": True,
                "parallel_jobs": 3,
                "retention_policy": {"daily": 7, "weekly": 4, "monthly": 12},
            },
            "storage": {
                "local": {
                    "enabled": True,
                    "path": "/var/backups/auto-video/local",
                },
                "s3": {
                    "enabled": False,
                    "bucket": "auto-video-backups",
                    "region": "us-west-2",
                    "access_key": "${AWS_ACCESS_KEY_ID}",
                    "secret_key": "${AWS_SECRET_ACCESS_KEY}",
                },
                "remote_sync": {
                    "enabled": False,
                    "host": "backup-server.company.com",
                    "user": "backup",
                    "path": "/backups/auto-video",
                },
            },
            "jobs": [],
        }

    def _setup_logging(self) -> logging.Logger:
        """設定日誌記錄"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("./logs/backup_system.log"),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)

    def _get_or_create_encryption_key(self) -> bytes:
        """獲取或創建加密金鑰"""
        key_file = Path("./secrets/backup_encryption.key")

        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 僅所有者可讀寫
            return key

    def _setup_s3_client(self):
        """設定 S3 客戶端"""
        s3_config = self.config.get("storage", {}).get("s3", {})

        if s3_config.get("enabled", False):
            return boto3.client(
                "s3",
                region_name=s3_config.get("region"),
                aws_access_key_id=os.getenv(
                    s3_config.get("access_key", "")
                    .replace("${", "")
                    .replace("}", "")
                ),
                aws_secret_access_key=os.getenv(
                    s3_config.get("secret_key", "")
                    .replace("${", "")
                    .replace("}", "")
                ),
            )
        return None

    async def run_backup_scheduler(self):
        """運行備份排程器"""
        self.logger.info("Starting backup scheduler")

        # 註冊所有備份任務
        for job_config in self.config.get("jobs", []):
            job = BackupJob(**job_config)
            self._schedule_backup_job(job)

        # 運行排程器
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # 每分鐘檢查一次

    def _schedule_backup_job(self, job: BackupJob):
        """排程備份任務"""
        if job.schedule == "daily":
            schedule.every().day.at("02:00").do(self._run_backup_job, job)
        elif job.schedule == "weekly":
            schedule.every().sunday.at("01:00").do(self._run_backup_job, job)
        elif job.schedule == "monthly":
            schedule.every().month.do(self._run_backup_job, job)
        elif job.schedule.startswith("*/"):
            # 間隔執行，例如 "*/6" 表示每6小時
            hours = int(job.schedule.split("/")[1])
            schedule.every(hours).hours.do(self._run_backup_job, job)

    async def _run_backup_job(self, job: BackupJob) -> BackupResult:
        """執行備份任務"""
        start_time = datetime.now()
        self.logger.info(f"Starting backup job: {job.name}")

        try:
            # 檢查依賴任務
            if not await self._check_dependencies(job.dependencies):
                raise Exception("Dependency check failed")

            # 執行備份
            if job.type == "database":
                result = await self._backup_database(job, start_time)
            elif job.type == "files":
                result = await self._backup_files(job, start_time)
            elif job.type == "container":
                result = await self._backup_container(job, start_time)
            elif job.type == "configuration":
                result = await self._backup_configuration(job, start_time)
            else:
                raise Exception(f"Unknown backup type: {job.type}")

            # 驗證備份
            if self.config["backup"]["checksum_verification"]:
                await self._verify_backup(result)

            # 清理舊備份
            await self._cleanup_old_backups(job)

            # 同步到遠端儲存
            await self._sync_to_remote_storage(result)

            self.logger.info(f"Backup job completed: {job.name}")
            return result

        except Exception as e:
            end_time = datetime.now()
            error_result = BackupResult(
                job_name=job.name,
                start_time=start_time,
                end_time=end_time,
                status="failed",
                size_bytes=0,
                duration_seconds=(end_time - start_time).total_seconds(),
                error_message=str(e),
            )

            self.logger.error(f"Backup job failed: {job.name} - {e}")
            await self._send_backup_alert(error_result)
            return error_result

    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """檢查依賴任務"""
        for dep in dependencies:
            # 檢查依賴服務是否可用
            if not await self._check_service_availability(dep):
                return False
        return True

    async def _check_service_availability(self, service_name: str) -> bool:
        """檢查服務可用性"""
        try:
            # 這裡可以整合健康檢查系統
            # 暫時返回 True
            return True
        except Exception:
            return False

    async def _backup_database(
        self, job: BackupJob, start_time: datetime
    ) -> BackupResult:
        """備份資料庫"""
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{job.name}_{timestamp}.sql"

        if job.compression:
            backup_filename += ".gz"

        backup_path = Path(job.destination) / backup_filename
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # 解析資料庫連接字串
        # 假設格式為 postgresql://user:pass@host:port/dbname
        db_url = job.source

        try:
            # 執行 pg_dump
            dump_cmd = [
                "pg_dump",
                db_url,
                "--verbose",
                "--no-password",
                "--format=custom",
                "--file",
                str(backup_path),
            ]

            if job.compression:
                dump_cmd.extend(["--compress=9"])

            process = await asyncio.create_subprocess_exec(
                *dump_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")

            # 加密備份檔案
            if job.encryption:
                await self._encrypt_file(backup_path)

            # 計算檔案大小和校驗和
            file_size = backup_path.stat().st_size
            checksum = await self._calculate_checksum(backup_path)

            end_time = datetime.now()

            result = BackupResult(
                job_name=job.name,
                start_time=start_time,
                end_time=end_time,
                status="success",
                size_bytes=file_size,
                duration_seconds=(end_time - start_time).total_seconds(),
                backup_path=str(backup_path),
                checksum=checksum,
            )

            self.backup_history.append(result)
            return result

        except Exception as e:
            # 清理失敗的備份檔案
            if backup_path.exists():
                backup_path.unlink()
            raise e

    async def _backup_files(
        self, job: BackupJob, start_time: datetime
    ) -> BackupResult:
        """備份檔案系統"""
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{job.name}_{timestamp}.tar"

        if job.compression:
            backup_filename += ".gz"

        backup_path = Path(job.destination) / backup_filename
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 創建 tar 歸檔
            mode = "w:gz" if job.compression else "w"

            with tarfile.open(backup_path, mode) as tar:
                tar.add(job.source, arcname=Path(job.source).name)

            # 加密備份檔案
            if job.encryption:
                await self._encrypt_file(backup_path)

            file_size = backup_path.stat().st_size
            checksum = await self._calculate_checksum(backup_path)

            end_time = datetime.now()

            result = BackupResult(
                job_name=job.name,
                start_time=start_time,
                end_time=end_time,
                status="success",
                size_bytes=file_size,
                duration_seconds=(end_time - start_time).total_seconds(),
                backup_path=str(backup_path),
                checksum=checksum,
            )

            self.backup_history.append(result)
            return result

        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()
            raise e

    async def _backup_container(
        self, job: BackupJob, start_time: datetime
    ) -> BackupResult:
        """備份 Docker 容器"""
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{job.name}_{timestamp}.tar"

        if job.compression:
            backup_filename += ".gz"

        backup_path = Path(job.destination) / backup_filename
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 導出容器
            export_cmd = ["docker", "export", job.source]  # 容器名稱或 ID

            # 壓縮處理
            if job.compression:
                process = await asyncio.create_subprocess_exec(
                    *export_cmd, stdout=asyncio.subprocess.PIPE
                )

                gzip_process = await asyncio.create_subprocess_exec(
                    "gzip",
                    "-c",
                    stdin=process.stdout,
                    stdout=open(backup_path, "wb"),
                )

                await process.wait()
                await gzip_process.wait()
            else:
                with open(backup_path, "wb") as f:
                    process = await asyncio.create_subprocess_exec(
                        *export_cmd, stdout=f
                    )
                    await process.wait()

            if job.encryption:
                await self._encrypt_file(backup_path)

            file_size = backup_path.stat().st_size
            checksum = await self._calculate_checksum(backup_path)

            end_time = datetime.now()

            result = BackupResult(
                job_name=job.name,
                start_time=start_time,
                end_time=end_time,
                status="success",
                size_bytes=file_size,
                duration_seconds=(end_time - start_time).total_seconds(),
                backup_path=str(backup_path),
                checksum=checksum,
            )

            self.backup_history.append(result)
            return result

        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()
            raise e

    async def _backup_configuration(
        self, job: BackupJob, start_time: datetime
    ) -> BackupResult:
        """備份配置檔案"""
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{job.name}_{timestamp}.tar.gz"

        backup_path = Path(job.destination) / backup_filename
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 收集配置檔案
            config_files = [
                "./docker-compose.yml",
                "./docker-compose.prod.yml",
                "./.env.production",
                "./nginx/nginx.conf",
                "./monitoring/prometheus/prometheus.yml",
                "./monitoring/grafana/provisioning/",
                "./k8s/",
                "./scripts/",
                "./security/",
            ]

            with tarfile.open(backup_path, "w:gz") as tar:
                for config_path in config_files:
                    if Path(config_path).exists():
                        tar.add(config_path, arcname=Path(config_path).name)

            if job.encryption:
                await self._encrypt_file(backup_path)

            file_size = backup_path.stat().st_size
            checksum = await self._calculate_checksum(backup_path)

            end_time = datetime.now()

            result = BackupResult(
                job_name=job.name,
                start_time=start_time,
                end_time=end_time,
                status="success",
                size_bytes=file_size,
                duration_seconds=(end_time - start_time).total_seconds(),
                backup_path=str(backup_path),
                checksum=checksum,
            )

            self.backup_history.append(result)
            return result

        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()
            raise e

    async def _encrypt_file(self, file_path: Path):
        """加密檔案"""
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            encrypted_data = self.cipher.encrypt(data)

            encrypted_path = file_path.with_suffix(file_path.suffix + ".enc")
            with open(encrypted_path, "wb") as f:
                f.write(encrypted_data)

            # 刪除原始檔案
            file_path.unlink()
            encrypted_path.rename(file_path)

        except Exception as e:
            self.logger.error(f"Failed to encrypt file {file_path}: {e}")
            raise e

    async def _calculate_checksum(self, file_path: Path) -> str:
        """計算檔案校驗和"""
        import hashlib

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    async def _verify_backup(self, result: BackupResult):
        """驗證備份完整性"""
        if not result.backup_path or not Path(result.backup_path).exists():
            raise Exception("Backup file not found")

        # 重新計算校驗和
        current_checksum = await self._calculate_checksum(
            Path(result.backup_path)
        )

        if current_checksum != result.checksum:
            raise Exception("Backup verification failed: checksum mismatch")

        self.logger.info(f"Backup verification successful: {result.job_name}")

    async def _cleanup_old_backups(self, job: BackupJob):
        """清理舊備份"""
        backup_dir = Path(job.destination)
        retention_days = job.retention_days

        if not backup_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        for backup_file in backup_dir.glob(f"{job.name}_*"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                self.logger.info(f"Deleted old backup: {backup_file}")

    async def _sync_to_remote_storage(self, result: BackupResult):
        """同步到遠端儲存"""
        if not result.backup_path:
            return

        backup_file = Path(result.backup_path)

        # S3 同步
        if self.s3_client and self.config["storage"]["s3"]["enabled"]:
            try:
                bucket = self.config["storage"]["s3"]["bucket"]
                key = f"backups/{result.job_name}/{backup_file.name}"

                self.s3_client.upload_file(str(backup_file), bucket, key)
                self.logger.info(f"Backup uploaded to S3: {key}")

            except Exception as e:
                self.logger.error(f"Failed to upload to S3: {e}")

        # 遠端同步
        remote_config = self.config["storage"]["remote_sync"]
        if remote_config.get("enabled", False):
            try:
                rsync_cmd = [
                    "rsync",
                    "-avz",
                    "--progress",
                    str(backup_file),
                    f"{remote_config['user']}@{remote_config['host']}:{remote_config['path']}",
                ]

                process = await asyncio.create_subprocess_exec(*rsync_cmd)
                await process.wait()

                if process.returncode == 0:
                    self.logger.info(
                        f"Backup synced to remote: {backup_file.name}"
                    )
                else:
                    raise Exception(
                        f"rsync failed with code {process.returncode}"
                    )

            except Exception as e:
                self.logger.error(f"Failed to sync to remote: {e}")

    async def _send_backup_alert(self, result: BackupResult):
        """發送備份告警"""
        if result.status == "failed":
            alert_data = {
                "alert_type": "backup_failure",
                "job_name": result.job_name,
                "error": result.error_message,
                "timestamp": result.start_time.isoformat(),
            }

            # 發送到 Alertmanager
            try:
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "http://alertmanager:9093/api/v1/alerts",
                        json=[alert_data],
                    ) as response:
                        if response.status == 200:
                            self.logger.info("Backup alert sent successfully")
                        else:
                            self.logger.error(
                                f"Failed to send backup alert: {response.status}"
                            )

            except Exception as e:
                self.logger.error(f"Failed to send backup alert: {e}")

    async def disaster_recovery(self, recovery_plan: str):
        """災難恢復程序"""
        self.logger.info(f"Starting disaster recovery: {recovery_plan}")

        # 載入恢復計劃
        plan_path = Path(
            f"./scripts/backup/recovery_plans/{recovery_plan}.yaml"
        )

        if not plan_path.exists():
            raise Exception(f"Recovery plan not found: {recovery_plan}")

        with open(plan_path, "r") as f:
            plan = yaml.safe_load(f)

        try:
            # 執行恢復步驟
            for step in plan.get("steps", []):
                await self._execute_recovery_step(step)

            self.logger.info("Disaster recovery completed successfully")

        except Exception as e:
            self.logger.error(f"Disaster recovery failed: {e}")
            raise e

    async def _execute_recovery_step(self, step: Dict[str, Any]):
        """執行恢復步驟"""
        step_type = step.get("type")

        if step_type == "restore_database":
            await self._restore_database(step)
        elif step_type == "restore_files":
            await self._restore_files(step)
        elif step_type == "start_services":
            await self._start_services(step)
        elif step_type == "verify_system":
            await self._verify_system(step)
        else:
            raise Exception(f"Unknown recovery step type: {step_type}")

    async def _restore_database(self, step: Dict[str, Any]):
        """恢復資料庫"""
        backup_file = step.get("backup_file")
        target_db = step.get("target_database")

        # 解密備份檔案
        if backup_file.endswith(".enc"):
            await self._decrypt_file(Path(backup_file))

        # 恢復資料庫
        restore_cmd = [
            "pg_restore",
            "--verbose",
            "--clean",
            "--no-acl",
            "--no-owner",
            "--dbname",
            target_db,
            backup_file,
        ]

        process = await asyncio.create_subprocess_exec(*restore_cmd)
        await process.wait()

        if process.returncode != 0:
            raise Exception("Database restore failed")

    async def _decrypt_file(self, file_path: Path):
        """解密檔案"""
        with open(file_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = self.cipher.decrypt(encrypted_data)

        decrypted_path = file_path.with_suffix("")
        with open(decrypted_path, "wb") as f:
            f.write(decrypted_data)

        # 刪除加密檔案
        file_path.unlink()

    async def _restore_files(self, step: Dict[str, Any]):
        """恢復檔案"""
        # 實作檔案恢復邏輯

    async def _start_services(self, step: Dict[str, Any]):
        """啟動服務"""
        # 實作服務啟動邏輯

    async def _verify_system(self, step: Dict[str, Any]):
        """驗證系統"""
        # 實作系統驗證邏輯


async def main():
    """主函數"""
    backup_system = BackupSystem()
    await backup_system.run_backup_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
