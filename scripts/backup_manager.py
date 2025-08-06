#!/usr/bin/env python3
"""
企業級備份管理系統
達到 AWS Backup / Google Cloud Backup 級別的數據保護
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3
import redis

logger = logging.getLogger(__name__)


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackupJob:
    """備份任務"""

    job_id: str
    backup_type: BackupType
    source: str
    destination: str
    status: BackupStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    size_bytes: int
    checksum: str
    metadata: Dict[str, Any]


class PostgreSQLBackup:
    """PostgreSQL 資料庫備份"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config.get("postgresql", {})

    async def create_backup(self, backup_path: str) -> Dict[str, Any]:
        """創建 PostgreSQL 備份"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/postgresql_backup_{timestamp}.sql.gz"

        # 構建 pg_dump 命令
        pg_dump_cmd = [
            "pg_dump",
            f"--host={self.db_config.get('host', 'localhost')}",
            f"--port={self.db_config.get('port', 5432)}",
            f"--username={self.db_config.get('username', 'postgres')}",
            f"--dbname={self.db_config.get('database', 'auto_video')}",
            "--verbose",
            "--clean",
            "--no-owner",
            "--no-privileges",
        ]

        try:
            # 執行備份
            logger.info(f"開始 PostgreSQL 備份到 {backup_file}")

            with gzip.open(backup_file, "wt") as f:
                process = subprocess.Popen(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env={
                        **os.environ,
                        "PGPASSWORD": self.db_config.get("password", ""),
                    },
                )

                _, stderr = process.communicate()

                if process.returncode != 0:
                    raise Exception(f"pg_dump 失敗: {stderr.decode()}")

            # 計算檔案大小和校驗和
            file_size = os.path.getsize(backup_file)
            checksum = await self._calculate_checksum(backup_file)

            logger.info(f"PostgreSQL 備份完成: {backup_file} ({file_size} bytes)")

            return {
                "success": True,
                "backup_file": backup_file,
                "size_bytes": file_size,
                "checksum": checksum,
                "timestamp": timestamp,
            }

        except Exception as e:
            logger.error(f"PostgreSQL 備份失敗: {e}")
            return {"success": False, "error": str(e)}

    async def restore_backup(self, backup_file: str) -> Dict[str, Any]:
        """恢復 PostgreSQL 備份"""

        try:
            logger.info(f"開始恢復 PostgreSQL 備份: {backup_file}")

            # 構建 psql 命令
            psql_cmd = [
                "psql",
                f"--host={self.db_config.get('host', 'localhost')}",
                f"--port={self.db_config.get('port', 5432)}",
                f"--username={self.db_config.get('username', 'postgres')}",
                f"--dbname={self.db_config.get('database', 'auto_video')}",
                "--quiet",
            ]

            with gzip.open(backup_file, "rt") as f:
                process = subprocess.Popen(
                    psql_cmd,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={
                        **os.environ,
                        "PGPASSWORD": self.db_config.get("password", ""),
                    },
                )

                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    raise Exception(f"psql 恢復失敗: {stderr.decode()}")

            logger.info(f"PostgreSQL 恢復完成: {backup_file}")
            return {"success": True, "message": "恢復成功"}

        except Exception as e:
            logger.error(f"PostgreSQL 恢復失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_checksum(self, file_path: str) -> str:
        """計算檔案校驗和"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class RedisBackup:
    """Redis 資料備份"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_config = config.get("redis", {})
        self.redis_client = redis.Redis(
            host=self.redis_config.get("host", "localhost"),
            port=self.redis_config.get("port", 6379),
            password=self.redis_config.get("password"),
        )

    async def create_backup(self, backup_path: str) -> Dict[str, Any]:
        """創建 Redis 備份"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/redis_backup_{timestamp}.rdb"

        try:
            # 觸發 Redis BGSAVE
            logger.info("開始 Redis 備份")
            self.redis_client.bgsave()

            # 等待備份完成
            while self.redis_client.lastsave() == self.redis_client.lastsave():
                await asyncio.sleep(1)

            # 複製 RDB 檔案
            redis_dump_path = self.redis_config.get("dump_dir", "/var/lib/redis/dump.rdb")
            if os.path.exists(redis_dump_path):
                subprocess.run(["cp", redis_dump_path, backup_file], check=True)

                file_size = os.path.getsize(backup_file)
                checksum = await self._calculate_checksum(backup_file)

                logger.info(f"Redis 備份完成: {backup_file} ({file_size} bytes)")

                return {
                    "success": True,
                    "backup_file": backup_file,
                    "size_bytes": file_size,
                    "checksum": checksum,
                    "timestamp": timestamp,
                }
            else:
                raise Exception(f"找不到 Redis dump 檔案: {redis_dump_path}")

        except Exception as e:
            logger.error(f"Redis 備份失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_checksum(self, file_path: str) -> str:
        """計算檔案校驗和"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class FileSystemBackup:
    """檔案系統備份"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def create_backup(
        self,
        source_paths: List[str],
        backup_path: str,
        exclude_patterns: List[str] = None,
    ) -> Dict[str, Any]:
        """創建檔案系統備份"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/filesystem_backup_{timestamp}.tar.gz"

        try:
            logger.info(f"開始檔案系統備份: {source_paths}")

            # 建立 tar 備份
            with tarfile.open(backup_file, "w:gz") as tar:
                for source_path in source_paths:
                    if os.path.exists(source_path):
                        tar.add(
                            source_path,
                            arcname=os.path.basename(source_path),
                            exclude=self._create_exclude_filter(exclude_patterns or []),
                        )

            file_size = os.path.getsize(backup_file)
            checksum = await self._calculate_checksum(backup_file)

            logger.info(f"檔案系統備份完成: {backup_file} ({file_size} bytes)")

            return {
                "success": True,
                "backup_file": backup_file,
                "size_bytes": file_size,
                "checksum": checksum,
                "timestamp": timestamp,
            }

        except Exception as e:
            logger.error(f"檔案系統備份失敗: {e}")
            return {"success": False, "error": str(e)}

    def _create_exclude_filter(self, exclude_patterns: List[str]):
        """創建排除過濾器"""

        def exclude_filter(tarinfo):
            for pattern in exclude_patterns:
                if pattern in tarinfo.name:
                    return None
            return tarinfo

        return exclude_filter

    async def _calculate_checksum(self, file_path: str) -> str:
        """計算檔案校驗和"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class S3BackupStorage:
    """AWS S3 備份存儲"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.s3_config = config.get("s3", {})
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.s3_config.get("access_key_id"),
            aws_secret_access_key=self.s3_config.get("secret_access_key"),
            region_name=self.s3_config.get("region", "us-west-2"),
        )
        self.bucket_name = self.s3_config.get("bucket_name")

    async def upload_backup(self, local_file: str, s3_key: str) -> Dict[str, Any]:
        """上傳備份到 S3"""
        try:
            logger.info(f"上傳備份到 S3: {local_file} -> s3://{self.bucket_name}/{s3_key}")

            # 上傳檔案
            self.s3_client.upload_file(local_file, self.bucket_name, s3_key)

            # 設定生命週期標籤
            self.s3_client.put_object_tagging(
                Bucket=self.bucket_name,
                Key=s3_key,
                Tagging={
                    "TagSet": [
                        {"Key": "BackupType", "Value": "AutoVideoSystem"},
                        {
                            "Key": "CreatedDate",
                            "Value": datetime.utcnow().isoformat(),
                        },
                    ]
                },
            )

            logger.info(f"S3 上傳完成: s3://{self.bucket_name}/{s3_key}")
            return {"success": True, "s3_key": s3_key}

        except Exception as e:
            logger.error(f"S3 上傳失敗: {e}")
            return {"success": False, "error": str(e)}

    async def download_backup(self, s3_key: str, local_file: str) -> Dict[str, Any]:
        """從 S3 下載備份"""
        try:
            logger.info(f"從 S3 下載備份: s3://{self.bucket_name}/{s3_key} -> {local_file}")

            self.s3_client.download_file(self.bucket_name, s3_key, local_file)

            logger.info(f"S3 下載完成: {local_file}")
            return {"success": True, "local_file": local_file}

        except Exception as e:
            logger.error(f"S3 下載失敗: {e}")
            return {"success": False, "error": str(e)}


class BackupManager:
    """企業級備份管理器"""

    def __init__(self, config_file: str = "config/backup-config.json"):
        self.config = self._load_config(config_file)
        self.postgresql_backup = PostgreSQLBackup(self.config)
        self.redis_backup = RedisBackup(self.config)
        self.filesystem_backup = FileSystemBackup(self.config)
        self.s3_storage = S3BackupStorage(self.config)
        self.backup_jobs: Dict[str, BackupJob] = {}

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """載入備份配置"""
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置檔案不存在: {config_file}，使用預設配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "username": "postgres",
                "password": os.getenv("POSTGRES_PASSWORD", ""),
                "database": "auto_video",
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": os.getenv("REDIS_PASSWORD", ""),
                "dump_dir": "/var/lib/redis/dump.rdb",
            },
            "s3": {
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                "bucket_name": os.getenv("S3_BACKUP_BUCKET", "auto-video-backups"),
                "region": "us-west-2",
            },
            "backup": {
                "local_path": "/var/backups/auto-video",
                "retention_days": 30,
                "schedule": {
                    "full_backup": "0 2 * * 0",  # 每週日凌晨2點
                    "incremental_backup": "0 2 * * 1-6",  # 週一到週六凌晨2點
                },
            },
        }

    async def create_full_backup(self) -> Dict[str, Any]:
        """創建完整備份"""

        job_id = f"full_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.config["backup"]["local_path"]

        # 確保備份目錄存在
        os.makedirs(backup_path, exist_ok=True)

        logger.info(f"開始完整備份: {job_id}")

        backup_results = {
            "job_id": job_id,
            "backup_type": "full",
            "started_at": datetime.utcnow().isoformat(),
            "components": {},
        }

        try:
            # 1. PostgreSQL 備份
            logger.info("執行 PostgreSQL 備份...")
            pg_result = await self.postgresql_backup.create_backup(backup_path)
            backup_results["components"]["postgresql"] = pg_result

            # 2. Redis 備份
            logger.info("執行 Redis 備份...")
            redis_result = await self.redis_backup.create_backup(backup_path)
            backup_results["components"]["redis"] = redis_result

            # 3. 檔案系統備份
            logger.info("執行檔案系統備份...")
            filesystem_paths = [
                "./config",
                "./services",
                "./monitoring",
                "./scripts",
            ]
            exclude_patterns = ["__pycache__", ".git", "node_modules", "*.log"]
            fs_result = await self.filesystem_backup.create_backup(
                filesystem_paths, backup_path, exclude_patterns
            )
            backup_results["components"]["filesystem"] = fs_result

            # 4. 上傳到 S3（如果配置了）
            if self.s3_storage.bucket_name:
                logger.info("上傳備份到 S3...")
                s3_results = []

                for component, result in backup_results["components"].items():
                    if result.get("success") and "backup_file" in result:
                        backup_file = result["backup_file"]
                        s3_key = f"backups/{job_id}/{os.path.basename(backup_file)}"

                        s3_result = await self.s3_storage.upload_backup(backup_file, s3_key)
                        s3_results.append({"component": component, "s3_result": s3_result})

                backup_results["s3_uploads"] = s3_results

            backup_results["completed_at"] = datetime.utcnow().isoformat()
            backup_results["status"] = "completed"

            logger.info(f"完整備份完成: {job_id}")

        except Exception as e:
            backup_results["status"] = "failed"
            backup_results["error"] = str(e)
            backup_results["completed_at"] = datetime.utcnow().isoformat()
            logger.error(f"完整備份失敗: {e}")

        return backup_results

    async def cleanup_old_backups(self):
        """清理過期備份"""

        retention_days = self.config["backup"]["retention_days"]
        backup_path = self.config["backup"]["local_path"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        logger.info(f"清理 {retention_days} 天前的備份")

        try:
            for filename in os.listdir(backup_path):
                file_path = os.path.join(backup_path, filename)
                if os.path.isfile(file_path):
                    # 檢查檔案修改時間
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"刪除過期備份: {filename}")

        except Exception as e:
            logger.error(f"清理備份失敗: {e}")

    async def verify_backup_integrity(self, backup_file: str, expected_checksum: str) -> bool:
        """驗證備份完整性"""

        try:
            hash_sha256 = hashlib.sha256()
            with open(backup_file, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)

            actual_checksum = hash_sha256.hexdigest()

            if actual_checksum == expected_checksum:
                logger.info(f"備份完整性驗證成功: {backup_file}")
                return True
            else:
                logger.error(f"備份完整性驗證失敗: {backup_file}")
                return False

        except Exception as e:
            logger.error(f"備份完整性驗證錯誤: {e}")
            return False


# 使用示例
async def main():
    """備份管理器使用示例"""

    backup_manager = BackupManager()

    # 執行完整備份
    result = await backup_manager.create_full_backup()

    if result["status"] == "completed":
        print("✅ 完整備份完成")
        print(f"備份 ID: {result['job_id']}")

        # 顯示各組件備份結果
        for component, details in result["components"].items():
            if details.get("success"):
                print(f"  ✅ {component}: {details.get('size_bytes', 0)} bytes")
            else:
                print(f"  ❌ {component}: {details.get('error', 'Unknown error')}")
    else:
        print(f"❌ 備份失敗: {result.get('error', 'Unknown error')}")

    # 清理過期備份
    await backup_manager.cleanup_old_backups()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
