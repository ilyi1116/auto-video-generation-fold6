#!/usr/bin/env python3
"""
資料庫版本同步管理器
Auto Video Generation System - Database Sync Manager
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import asyncpg
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)


class DatabaseSyncManager:
    """資料庫版本同步管理器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.alembic_cfg = Config(str(project_root / "alembic.ini"))

        # 資料庫配置
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "password"),
            "database": os.getenv("DB_NAME", "auto_video_generation"),
        }

        self.database_url = (
            f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
            f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )

        self.async_database_url = (
            f"postgresql+asyncpg://{self.db_config['user']}:{self.db_config['password']}@"
            f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )

    async def get_current_revision(self) -> Optional[str]:
        """獲取當前資料庫版本"""
        try:
            engine = create_async_engine(self.async_database_url)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"
                    )
                )
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.warning(f"無法獲取當前版本: {e}")
            return None
        finally:
            await engine.dispose()

    async def get_latest_revision(self) -> str:
        """獲取最新的遷移版本"""
        try:
            # 使用 alembic 命令獲取最新版本
            from alembic.script import ScriptDirectory

            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            return script_dir.get_current_head()
        except Exception as e:
            logger.error(f"無法獲取最新版本: {e}")
            return "head"

    async def check_sync_status(self) -> Dict[str, any]:
        """檢查同步狀態"""
        current = await self.get_current_revision()
        latest = await self.get_latest_revision()

        is_synced = current == latest

        return {
            "current_revision": current,
            "latest_revision": latest,
            "is_synced": is_synced,
            "needs_upgrade": not is_synced and current != latest,
            "database_url": self.database_url.replace(
                self.db_config["password"], "***"
            ),
        }

    async def ensure_database_exists(self) -> bool:
        """確保資料庫存在"""
        try:
            # 連接到 postgres 系統資料庫
            system_url = (
                f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
                f"{self.db_config['host']}:{self.db_config['port']}/postgres"
            )

            conn = await asyncpg.connect(system_url)

            # 檢查資料庫是否存在
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.db_config["database"],
            )

            if not result:
                # 建立資料庫
                await conn.execute(
                    f'CREATE DATABASE "{self.db_config["database"]}"'
                )
                logger.info(f"✅ 建立資料庫: {self.db_config['database']}")
            else:
                logger.info(f"📋 資料庫已存在: {self.db_config['database']}")

            await conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 資料庫建立失敗: {e}")
            return False

    async def init_alembic_version_table(self) -> bool:
        """初始化 Alembic 版本表"""
        try:
            engine = create_async_engine(self.async_database_url)
            async with engine.connect() as conn:
                # 檢查版本表是否存在
                result = await conn.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'alembic_version')"
                    )
                )
                exists = result.fetchone()[0]

                if not exists:
                    # 建立版本表
                    await conn.execute(
                        text(
                            """
                        CREATE TABLE alembic_version (
                            version_num VARCHAR(32) NOT NULL,
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        )
                        """
                        )
                    )
                    await conn.commit()
                    logger.info("✅ 建立 Alembic 版本表")
                else:
                    logger.info("📋 Alembic 版本表已存在")

            await engine.dispose()
            return True

        except Exception as e:
            logger.error(f"❌ 初始化版本表失敗: {e}")
            return False

    async def sync_to_latest(self, dry_run: bool = False) -> bool:
        """同步到最新版本"""
        try:
            status = await self.check_sync_status()

            if status["is_synced"]:
                logger.info("✅ 資料庫已是最新版本")
                return True

            if dry_run:
                logger.info(
                    f"🔍 Dry run: 將升級從 {status['current_revision']} 到 {status['latest_revision']}"
                )
                return True

            # 設定環境變數
            os.environ["DATABASE_URL"] = self.database_url

            # 執行升級
            command.upgrade(self.alembic_cfg, "head")
            logger.info("✅ 資料庫升級完成")

            return True

        except Exception as e:
            logger.error(f"❌ 資料庫升級失敗: {e}")
            return False

    async def rollback_to_revision(
        self, revision: str, dry_run: bool = False
    ) -> bool:
        """回滾到指定版本"""
        try:
            if dry_run:
                logger.info(f"🔍 Dry run: 將回滾到版本 {revision}")
                return True

            # 設定環境變數
            os.environ["DATABASE_URL"] = self.database_url

            # 執行回滾
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"✅ 資料庫回滾到版本 {revision} 完成")

            return True

        except Exception as e:
            logger.error(f"❌ 資料庫回滾失敗: {e}")
            return False

    async def create_migration(
        self, message: str, auto_generate: bool = True
    ) -> bool:
        """建立新的遷移"""
        try:
            # 設定環境變數
            os.environ["DATABASE_URL"] = self.database_url

            if auto_generate:
                command.revision(
                    self.alembic_cfg, message=message, autogenerate=True
                )
            else:
                command.revision(self.alembic_cfg, message=message)

            logger.info(f"✅ 建立遷移: {message}")
            return True

        except Exception as e:
            logger.error(f"❌ 建立遷移失敗: {e}")
            return False

    async def validate_database_integrity(self) -> Dict[str, any]:
        """驗證資料庫完整性"""
        integrity_report = {
            "tables_exist": [],
            "missing_tables": [],
            "foreign_key_issues": [],
            "index_issues": [],
            "overall_status": "unknown",
        }

        try:
            engine = create_async_engine(self.async_database_url)
            async with engine.connect() as conn:
                # 檢查預期的表是否存在
                expected_tables = [
                    "users",
                    "trending_topics",
                    "keyword_research",
                    "viral_content",
                    "trend_analysis",
                    "stored_files",
                    "file_processing_jobs",
                    "file_downloads",
                    "video_projects",
                    "video_generations",
                    "video_assets",
                    "scheduled_tasks",
                    "task_executions",
                ]

                for table in expected_tables:
                    result = await conn.execute(
                        text(
                            "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = :table)"
                        ),
                        {"table": table},
                    )
                    exists = result.fetchone()[0]

                    if exists:
                        integrity_report["tables_exist"].append(table)
                    else:
                        integrity_report["missing_tables"].append(table)

                # 檢查外鍵約束
                fk_result = await conn.execute(
                    text(
                        """
                    SELECT conname, conrelid::regclass, confrelid::regclass
                    FROM pg_constraint
                    WHERE contype = 'f'
                    """
                    )
                )
                fks = fk_result.fetchall()
                integrity_report["foreign_keys_count"] = len(fks)

                # 檢查索引
                idx_result = await conn.execute(
                    text(
                        """
                    SELECT indexname, tablename
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    """
                    )
                )
                indexes = idx_result.fetchall()
                integrity_report["indexes_count"] = len(indexes)

            await engine.dispose()

            # 判斷整體狀態
            if len(integrity_report["missing_tables"]) == 0:
                integrity_report["overall_status"] = "healthy"
            elif len(integrity_report["tables_exist"]) > len(
                integrity_report["missing_tables"]
            ):
                integrity_report["overall_status"] = "partial"
            else:
                integrity_report["overall_status"] = "critical"

        except Exception as e:
            logger.error(f"驗證資料庫完整性失敗: {e}")
            integrity_report["error"] = str(e)
            integrity_report["overall_status"] = "error"

        return integrity_report

    async def get_migration_history(self) -> List[Dict[str, any]]:
        """獲取遷移歷史"""
        try:
            from alembic.script import ScriptDirectory

            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            revisions = []

            for rev in script_dir.walk_revisions():
                revisions.append(
                    {
                        "revision": rev.revision,
                        "down_revision": rev.down_revision,
                        "branch_labels": rev.branch_labels,
                        "message": rev.doc,
                        "create_date": getattr(
                            rev.module, "create_date", None
                        ),
                    }
                )

            return revisions

        except Exception as e:
            logger.error(f"獲取遷移歷史失敗: {e}")
            return []

    async def health_check(self) -> Dict[str, any]:
        """資料庫健康檢查"""
        health_status = {
            "database_reachable": False,
            "alembic_table_exists": False,
            "current_revision": None,
            "sync_status": {},
            "integrity_status": {},
            "timestamp": asyncio.get_event_loop().time(),
        }

        try:
            # 檢查資料庫可達性
            engine = create_async_engine(self.async_database_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                health_status["database_reachable"] = True
            await engine.dispose()

            # 檢查 Alembic 表
            current_rev = await self.get_current_revision()
            health_status["alembic_table_exists"] = current_rev is not None
            health_status["current_revision"] = current_rev

            # 同步狀態
            health_status["sync_status"] = await self.check_sync_status()

            # 完整性檢查
            health_status["integrity_status"] = (
                await self.validate_database_integrity()
            )

        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            health_status["error"] = str(e)

        return health_status


async def main():
    """測試函數"""
    project_root = Path(__file__).parent.parent.parent
    sync_manager = DatabaseSyncManager(project_root)

    print("🔍 執行資料庫健康檢查...")
    health = await sync_manager.health_check()
    print(f"健康檢查結果: {health}")

    print("\n📊 檢查同步狀態...")
    status = await sync_manager.check_sync_status()
    print(f"同步狀態: {status}")


if __name__ == "__main__":
    asyncio.run(main())
