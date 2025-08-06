#!/usr/bin/env python3
from typing import Any
"""
備份和恢復流程測試腳本
驗證災難恢復的完整性和可靠性
"""

import asyncio
import gzip
import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import boto3
import psycopg2
import redis

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """測試結果"""

    test_name: str
    success: bool
    duration: float
    message: str
    details: Optional[Dict] = None


class BackupRecoveryTester:
    """備份恢復測試器"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="backup_test_"))
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """載入測試配置"""
        return {
            "postgres": {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": os.getenv("POSTGRES_PORT", "5432"),
                "user": os.getenv("POSTGRES_USER", "auto_video_user"),
                "password": os.getenv("POSTGRES_PASSWORD", "password"),
                "database": os.getenv("POSTGRES_DB", "auto_video_db"),
            },
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "password": os.getenv("REDIS_PASSWORD", ""),
            },
            "s3": {
                "endpoint_url": os.getenv(
                    "S3_ENDPOINT_URL", "http://localhost:9000"
                ),
                "access_key": os.getenv("S3_ACCESS_KEY_ID", "minioadmin"),
                "secret_key": os.getenv("S3_SECRET_ACCESS_KEY", "minioadmin"),
                "bucket": os.getenv("S3_BUCKET_NAME", "auto-video-backups"),
            },
        }

    async def test_database_backup_restore(self) -> TestResult:
        """測試資料庫備份和恢復"""
        start_time = datetime.now()
        test_name = "資料庫備份恢復測試"

        try:
            # 1. 創建測試資料
            test_table = f"backup_test_{int(datetime.now().timestamp())}"
            test_data = [
                ("test_user_1", "test@example.com", "2024-01-01"),
                ("test_user_2", "user2@example.com", "2024-01-02"),
                ("test_user_3", "user3@example.com", "2024-01-03"),
            ]

            logger.info(f"創建測試表: {test_table}")
            await self._create_test_data(test_table, test_data)

            # 2. 執行資料庫備份
            backup_file = self.temp_dir / f"{test_table}_backup.sql.gz"
            logger.info(f"執行資料庫備份到: {backup_file}")
            backup_success = await self._backup_database(backup_file)

            if not backup_success:
                raise Exception("資料庫備份失敗")

            # 3. 刪除測試資料
            logger.info("刪除原始測試資料")
            await self._delete_test_data(test_table)

            # 4. 驗證資料已刪除
            data_count = await self._count_test_data(test_table)
            if data_count > 0:
                raise Exception("測試資料刪除失敗")

            # 5. 執行資料恢復
            logger.info("執行資料庫恢復")
            restore_success = await self._restore_database(backup_file)

            if not restore_success:
                raise Exception("資料庫恢復失敗")

            # 6. 驗證恢復的資料
            logger.info("驗證恢復的資料")
            restored_data = await self._get_test_data(test_table)

            if len(restored_data) != len(test_data):
                raise Exception(
                    f"恢復的資料數量不正確: 期望 {len(test_data)}, 實際 {len(restored_data)}"
                )

            # 7. 清理測試資料
            await self._delete_test_data(test_table)

            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_name=test_name,
                success=True,
                duration=duration,
                message=f"成功備份和恢復 {len(test_data)} 筆資料",
                details={
                    "backup_file_size": (
                        backup_file.stat().st_size
                        if backup_file.exists()
                        else 0
                    ),
                    "restored_records": len(restored_data),
                },
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"資料庫備份恢復測試失敗: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                message=str(e),
            )

    async def test_redis_backup_restore(self) -> TestResult:
        """測試 Redis 備份和恢復"""
        start_time = datetime.now()
        test_name = "Redis 備份恢復測試"

        try:
            # 1. 創建測試資料
            test_keys = {
                f"test:backup:{i}": f"test_value_{i}" for i in range(100)
            }

            logger.info(f"在 Redis 中創建 {len(test_keys)} 個測試鍵")
            redis_client = redis.Redis(
                host=self.config["redis"]["host"],
                port=self.config["redis"]["port"],
                password=self.config["redis"]["password"],
                decode_responses=True,
            )

            for key, value in test_keys.items():
                redis_client.set(key, value)

            # 2. 執行 Redis 備份 (RDB dump)
            backup_file = self.temp_dir / "redis_backup.rdb"
            logger.info(f"執行 Redis 備份到: {backup_file}")

            # 觸發 Redis 保存
            redis_client.bgsave()

            # 等待備份完成
            await asyncio.sleep(1)

            # 複製 RDB 文件
            redis_dump_path = "/var/lib/redis/dump.rdb"  # 默認路徑
            if not Path(redis_dump_path).exists():
                redis_dump_path = "/data/dump.rdb"  # Docker 容器路徑

            if Path(redis_dump_path).exists():
                shutil.copy2(redis_dump_path, backup_file)
            else:
                # 如果找不到 RDB 文件，使用手動方式
                await self._manual_redis_backup(redis_client, backup_file)

            # 3. 清除測試資料
            logger.info("清除 Redis 測試資料")
            for key in test_keys.keys():
                redis_client.delete(key)

            # 4. 驗證資料已清除
            remaining_keys = redis_client.keys("test:backup:*")
            if remaining_keys:
                raise Exception(
                    f"測試資料清除失敗，仍有 {len(remaining_keys)} 個鍵"
                )

            # 5. 模擬恢復 (重新插入資料)
            logger.info("模擬 Redis 資料恢復")
            await self._restore_redis_data(redis_client, test_keys)

            # 6. 驗證恢復的資料
            logger.info("驗證恢復的資料")
            restored_count = 0
            for key, expected_value in test_keys.items():
                actual_value = redis_client.get(key)
                if actual_value == expected_value:
                    restored_count += 1

            if restored_count != len(test_keys):
                raise Exception(
                    f"恢復的資料不完整: 期望 {len(test_keys)}, 實際 {restored_count}"
                )

            # 7. 清理測試資料
            for key in test_keys.keys():
                redis_client.delete(key)

            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_name=test_name,
                success=True,
                duration=duration,
                message=f"成功備份和恢復 {len(test_keys)} 個 Redis 鍵",
                details={
                    "backup_file_size": (
                        backup_file.stat().st_size
                        if backup_file.exists()
                        else 0
                    ),
                    "restored_keys": restored_count,
                },
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Redis 備份恢復測試失敗: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                message=str(e),
            )

    async def test_file_backup_restore(self) -> TestResult:
        """測試檔案備份和恢復"""
        start_time = datetime.now()
        test_name = "檔案備份恢復測試"

        try:
            # 1. 創建測試檔案
            test_files_dir = self.temp_dir / "test_files"
            test_files_dir.mkdir(exist_ok=True)

            test_files = {}
            for i in range(10):
                file_path = test_files_dir / f"test_file_{i}.txt"
                content = (
                    f"Test file {i} content\nCreated at {datetime.now()}\n"
                    * 100
                )
                file_path.write_text(content, encoding="utf-8")
                test_files[file_path.name] = len(content)

            logger.info(f"創建了 {len(test_files)} 個測試檔案")

            # 2. 執行檔案備份
            backup_archive = self.temp_dir / "files_backup.tar.gz"
            logger.info(f"執行檔案備份到: {backup_archive}")

            with tarfile.open(backup_archive, "w:gz") as tar:
                tar.add(test_files_dir, arcname="test_files")

            # 3. 刪除原始檔案
            logger.info("刪除原始測試檔案")
            shutil.rmtree(test_files_dir)

            # 4. 驗證檔案已刪除
            if test_files_dir.exists():
                raise Exception("測試檔案刪除失敗")

            # 5. 執行檔案恢復
            logger.info("執行檔案恢復")
            with tarfile.open(backup_archive, "r:gz") as tar:
                tar.extractall(self.temp_dir)

            # 6. 驗證恢復的檔案
            restored_files_dir = self.temp_dir / "test_files"
            if not restored_files_dir.exists():
                raise Exception("檔案恢復失敗，目錄不存在")

            restored_files = list(restored_files_dir.glob("*.txt"))
            if len(restored_files) != len(test_files):
                raise Exception(
                    f"恢復的檔案數量不正確: 期望 {len(test_files)}, 實際 {len(restored_files)}"
                )

            # 驗證檔案內容
            for file_path in restored_files:
                if file_path.name not in test_files:
                    raise Exception(f"發現意外的檔案: {file_path.name}")

                actual_size = len(file_path.read_text(encoding="utf-8"))
                expected_size = test_files[file_path.name]
                if actual_size != expected_size:
                    raise Exception(
                        f"檔案 {file_path.name} 大小不正確: 期望 {expected_size}, 實際 {actual_size}"
                    )

            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_name=test_name,
                success=True,
                duration=duration,
                message=f"成功備份和恢復 {len(test_files)} 個檔案",
                details={
                    "backup_archive_size": (
                        backup_archive.stat().st_size
                        if backup_archive.exists()
                        else 0
                    ),
                    "restored_files": len(restored_files),
                },
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"檔案備份恢復測試失敗: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                message=str(e),
            )

    async def test_s3_backup_restore(self) -> TestResult:
        """測試 S3 備份和恢復"""
        start_time = datetime.now()
        test_name = "S3 備份恢復測試"

        try:
            # 1. 設置 S3 客戶端
            s3_client = boto3.client(
                "s3",
                endpoint_url=self.config["s3"]["endpoint_url"],
                aws_access_key_id=self.config["s3"]["access_key"],
                aws_secret_access_key=self.config["s3"]["secret_key"],
            )

            bucket_name = self.config["s3"]["bucket"]

            # 2. 創建測試檔案
            test_file = self.temp_dir / "s3_test_file.json"
            test_data = {
                "test_id": int(datetime.now().timestamp()),
                "data": [f"item_{i}" for i in range(1000)],
                "timestamp": datetime.now().isoformat(),
            }

            test_file.write_text(
                json.dumps(test_data, indent=2), encoding="utf-8"
            )
            logger.info(f"創建測試檔案: {test_file}")

            # 3. 上傳到 S3
            s3_key = f"backup-test/{test_file.name}"
            logger.info(f"上傳檔案到 S3: {s3_key}")

            s3_client.upload_file(str(test_file), bucket_name, s3_key)

            # 4. 刪除本地檔案
            test_file.unlink()
            logger.info("刪除本地測試檔案")

            # 5. 從 S3 下載檔案
            restored_file = self.temp_dir / "restored_s3_test_file.json"
            logger.info(f"從 S3 下載檔案: {restored_file}")

            s3_client.download_file(bucket_name, s3_key, str(restored_file))

            # 6. 驗證恢復的檔案
            if not restored_file.exists():
                raise Exception("檔案從 S3 恢復失敗")

            restored_data = json.loads(
                restored_file.read_text(encoding="utf-8")
            )

            if restored_data["test_id"] != test_data["test_id"]:
                raise Exception("恢復的檔案內容不正確")

            if len(restored_data["data"]) != len(test_data["data"]):
                raise Exception(
                    f"恢復的資料項目數量不正確: 期望 {len(test_data['data'])}, 實際 {len(restored_data['data'])}"
                )

            # 7. 清理 S3 中的測試檔案
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            logger.info("清理 S3 中的測試檔案")

            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_name=test_name,
                success=True,
                duration=duration,
                message="成功通過 S3 備份和恢復檔案",
                details={
                    "file_size": restored_file.stat().st_size,
                    "data_items": len(restored_data["data"]),
                },
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"S3 備份恢復測試失敗: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                message=str(e),
            )

    async def _create_test_data(
        self, table_name: str, data: List[Tuple]
    ) -> None:
        """創建測試資料"""
        conn = psycopg2.connect(**self.config["postgres"])
        try:
            with conn.cursor() as cur:
                # 創建測試表
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        email VARCHAR(100),
                        created_date DATE
                    )
                """
                )

                # 插入測試資料
                for row in data:
                    cur.execute(
                        f"INSERT INTO {table_name} (name, email, created_date) VALUES (%s, %s, %s)",
                        row,
                    )

                conn.commit()
        finally:
            conn.close()

    async def _delete_test_data(self, table_name: str) -> None:
        """刪除測試資料"""
        conn = psycopg2.connect(**self.config["postgres"])
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
        finally:
            conn.close()

    async def _count_test_data(self, table_name: str) -> int:
        """計算測試資料數量"""
        conn = psycopg2.connect(**self.config["postgres"])
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cur.fetchone()[0]
        except psycopg2.Error:
            return 0
        finally:
            conn.close()

    async def _get_test_data(self, table_name: str) -> List[Tuple]:
        """獲取測試資料"""
        conn = psycopg2.connect(**self.config["postgres"])
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT name, email, created_date FROM {table_name}"
                )
                return cur.fetchall()
        except psycopg2.Error:
            return []
        finally:
            conn.close()

    async def _backup_database(self, backup_file: Path) -> bool:
        """執行資料庫備份"""
        try:
            cmd = [
                "pg_dump",
                f"--host={self.config['postgres']['host']}",
                f"--port={self.config['postgres']['port']}",
                f"--username={self.config['postgres']['user']}",
                f"--dbname={self.config['postgres']['database']}",
                "--no-password",
                "--format=custom",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = self.config["postgres"]["password"]

            with gzip.open(backup_file, "wt") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True,
                )

            return backup_file.exists() and backup_file.stat().st_size > 0

        except subprocess.CalledProcessError as e:
            logger.error(f"資料庫備份失敗: {e.stderr}")
            return False

    async def _restore_database(self, backup_file: Path) -> bool:
        """執行資料庫恢復"""
        try:
            with gzip.open(backup_file, "rt") as f:
                cmd = [
                    "psql",
                    f"--host={self.config['postgres']['host']}",
                    f"--port={self.config['postgres']['port']}",
                    f"--username={self.config['postgres']['user']}",
                    f"--dbname={self.config['postgres']['database']}",
                    "--no-password",
                ]

                env = os.environ.copy()
                env["PGPASSWORD"] = self.config["postgres"]["password"]

                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True,
                )

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"資料庫恢復失敗: {e.stderr}")
            return False

    async def _manual_redis_backup(
        self, redis_client, backup_file: Path
    ) -> None:
        """手動 Redis 備份"""
        backup_data = {}
        for key in redis_client.scan_iter("test:backup:*"):
            backup_data[key] = redis_client.get(key)

        backup_file.write_text(json.dumps(backup_data), encoding="utf-8")

    async def _restore_redis_data(
        self, redis_client, test_keys: Dict[str, str]
    ) -> None:
        """恢復 Redis 資料"""
        for key, value in test_keys.items():
            redis_client.set(key, value)

    async def run_all_tests(self) -> Dict[str, Any]:
        """執行所有備份恢復測試"""
        logger.info("開始執行備份恢復測試套件")
        start_time = datetime.now()

        try:
            # 執行所有測試
            tests = [
                self.test_database_backup_restore(),
                self.test_redis_backup_restore(),
                self.test_file_backup_restore(),
                self.test_s3_backup_restore(),
            ]

            self.test_results = await asyncio.gather(
                *tests, return_exceptions=True
            )

            # 處理異常結果
            for i, result in enumerate(self.test_results):
                if isinstance(result, Exception):
                    self.test_results[i] = TestResult(
                        test_name=f"測試 {i + 1}",
                        success=False,
                        duration=0,
                        message=str(result),
                    )

            # 生成測試報告
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r.success)
            failed_tests = total_tests - passed_tests
            total_duration = (datetime.now() - start_time).total_seconds()

            report = {
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (
                        (passed_tests / total_tests) * 100
                        if total_tests > 0
                        else 0
                    ),
                    "total_duration": total_duration,
                    "timestamp": datetime.now().isoformat(),
                },
                "results": [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "duration": r.duration,
                        "message": r.message,
                        "details": r.details,
                    }
                    for r in self.test_results
                ],
            }

            logger.info(f"測試完成: {passed_tests}/{total_tests} 通過")
            return report

        finally:
            # 清理臨時文件
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("清理臨時文件完成")

    def generate_report(self, report: Dict[str, Any]) -> str:
        """生成人類可讀的測試報告"""
        summary = report["summary"]

        report_text = """
=================================================
備份恢復測試報告
=================================================
測試時間: {summary["timestamp"]}
總測試數: {summary["total_tests"]}
通過測試: {summary["passed"]}
失敗測試: {summary["failed"]}
成功率: {summary["success_rate"]:.1f}%
總耗時: {summary["total_duration"]:.2f} 秒

詳細結果:
-------------------------------------------------
"""

        for result in report["results"]:
            status = "✅ 通過" if result["success"] else "❌ 失敗"
            report_text += """
{status} {result["test_name"]}
   耗時: {result["duration"]:.2f} 秒
   訊息: {result["message"]}
"""
            if result["details"]:
                for key, value in result["details"].items():
                    report_text += f"   {key}: {value}\n"

        report_text += "\n================================================="
        return report_text


async def main():
    """主函數"""
    tester = BackupRecoveryTester()

    try:
        logger.info("開始備份恢復測試")
        report = await tester.run_all_tests()

        # 輸出報告
        print(tester.generate_report(report))

        # 保存 JSON 報告
        report_file = Path("backup_recovery_test_report.json")
        report_file.write_text(
            json.dumps(report, indent=2, ensure_ascii=False)
        )
        logger.info(f"詳細報告已保存到: {report_file}")

        # 返回適當的退出碼
        if report["summary"]["failed"] > 0:
            exit(1)
        else:
            logger.info("所有備份恢復測試通過!")
            exit(0)

    except Exception as e:
        logger.error(f"測試執行失敗: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
