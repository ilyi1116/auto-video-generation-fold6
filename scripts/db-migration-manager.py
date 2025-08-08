#!/usr/bin/env python3
"""
統一資料庫遷移管理腳本
Auto Video Generation System - Database Migration Manager
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DatabaseMigrationManager:
    """統一資料庫遷移管理器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.alembic_dir = project_root / "alembic"
        self.services_dir = project_root / "auto_generate_video_fold6" / "services"

        # 服務配置
        self.services = {
            "auth-service": {
                "path": self.services_dir / "auth-service",
                "database": "auth_db",
                "tables": ["users"],
            },
            "trend-service": {
                "path": self.services_dir / "trend-service",
                "database": "trend_db",
                "tables": [
                    "trending_topics",
                    "keyword_research",
                    "viral_content",
                    "trend_analysis",
                ],
            },
            "storage-service": {
                "path": self.services_dir / "storage-service",
                "database": "storage_db",
                "tables": [
                    "stored_files",
                    "file_processing_jobs",
                    "file_downloads",
                ],
            },
            "scheduler-service": {
                "path": self.services_dir / "scheduler-service",
                "database": "scheduler_db",
                "tables": [],
            },
            "video-service": {
                "path": self.services_dir / "video-service",
                "database": "video_db",
                "tables": [],
            },
            "inference-service": {
                "path": self.services_dir / "inference-service",
                "database": "inference_db",
                "tables": [],
            },
        }

        # 資料庫配置
        self.db_config = {
            "url": os.getenv("DATABASE_URL"),
        }

    def get_db_connection(self, database: Optional[str] = None):
        """建立資料庫連接"""
        if database:
            # If a specific database is requested, modify the URL
            # This assumes the DATABASE_URL is in the format postgresql://user:password@host:port/dbname
            parts = self.db_config["url"].rsplit("/", 1)
            db_url = f"{parts[0]}/{database}"
        else:
            db_url = self.db_config["url"]
        return psycopg2.connect(db_url)

    def create_databases(self) -> None:
        """建立所有必要的資料庫"""
        print("🗄️  建立資料庫...")

        # 連接到 postgres 系統資料庫來建立其他資料庫
        # Assuming the main DATABASE_URL points to the 'auto_video_generation' database
        # We need to connect to 'postgres' database to create new databases
        postgres_url = self.db_config["url"].rsplit("/", 1)[0] + "/postgres"
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Extract main_database name from DATABASE_URL
        main_database_name = self.db_config["url"].split("/")[-1]

        # 建立主資料庫
        try:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(main_database_name)
                )
            )
            print(f"✅ 建立主資料庫: {main_database_name}")
        except psycopg2.errors.DuplicateDatabase:
            print(f"📋 主資料庫已存在: {main_database_name}")

        # 建立各服務的獨立資料庫（如果需要的話）
        for service_name, config in self.services.items():
            if config.get("separate_db", False):
                try:
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config["database"]))
                    )
                    print(f"✅ 建立服務資料庫: {config['database']}")
                except psycopg2.errors.DuplicateDatabase:
                    print(f"📋 服務資料庫已存在: {config['database']}")

        cursor.close()
        conn.close()

    def init_alembic(self) -> None:
        """初始化 Alembic 配置"""
        print("🏗️  初始化 Alembic...")

        if not self.alembic_dir.exists():
            subprocess.run(
                ["alembic", "init", str(self.alembic_dir)],
                cwd=self.project_root,
                check=True,
            )
            print("✅ Alembic 初始化完成")
        else:
            print("📋 Alembic 已初始化")

    def create_initial_migration(self) -> None:
        """建立初始遷移"""
        print("📝 建立初始遷移...")

        os.environ["DATABASE_URL"] = self.db_config["url"]

        try:
            result = subprocess.run(
                [
                    "alembic",
                    "revision",
                    "--autogenerate",
                    "-m",
                    "Initial migration - unified services",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ 初始遷移建立成功")
                print(result.stdout)
            else:
                print("❌ 初始遷移建立失敗")
                print(result.stderr)
        except Exception as e:
            print(f"❌ 建立遷移時發生錯誤: {e}")

    def upgrade_database(self, revision: str = "head") -> None:
        """升級資料庫"""
        print(f"⬆️  升級資料庫到版本: {revision}")

        os.environ["DATABASE_URL"] = self.db_config["url"]

        try:
            result = subprocess.run(
                ["alembic", "upgrade", revision],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ 資料庫升級成功")
                print(result.stdout)
            else:
                print("❌ 資料庫升級失敗")
                print(result.stderr)
        except Exception as e:
            print(f"❌ 升級資料庫時發生錯誤: {e}")

    def downgrade_database(self, revision: str) -> None:
        """降級資料庫"""
        print(f"⬇️  降級資料庫到版本: {revision}")

        os.environ["DATABASE_URL"] = self.db_config["url"]

        try:
            result = subprocess.run(
                ["alembic", "downgrade", revision],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ 資料庫降級成功")
                print(result.stdout)
            else:
                print("❌ 資料庫降級失敗")
                print(result.stderr)
        except Exception as e:
            print(f"❌ 降級資料庫時發生錯誤: {e}")

    def show_current_revision(self) -> None:
        """顯示當前資料庫版本"""
        print("📋 檢查當前資料庫版本...")

        os.environ["DATABASE_URL"] = self.db_config["url"]

        try:
            result = subprocess.run(
                ["alembic", "current"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("📊 當前版本資訊:")
                print(result.stdout)
            else:
                print("❌ 無法獲取當前版本")
                print(result.stderr)
        except Exception as e:
            print(f"❌ 檢查版本時發生錯誤: {e}")

    def show_migration_history(self) -> None:
        """顯示遷移歷史"""
        print("📜 遷移歷史:")

        try:
            result = subprocess.run(
                ["alembic", "history", "--verbose"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(result.stdout)
            else:
                print("❌ 無法獲取遷移歷史")
                print(result.stderr)
        except Exception as e:
            print(f"❌ 獲取歷史時發生錯誤: {e}")

    def validate_migration_environment(self) -> bool:
        """驗證遷移環境"""
        print("🔍 驗證遷移環境...")

        # 檢查必要的檔案
        required_files = [
            self.project_root / "alembic.ini",
            self.alembic_dir / "env.py",
            self.alembic_dir / "script.py.mako",
        ]

        for file_path in required_files:
            if not file_path.exists():
                print(f"❌ 缺少必要檔案: {file_path}")
                return False

        # 檢查資料庫連接
        try:
            conn = psycopg2.connect(self.db_config["url"])
            conn.close()
            print("✅ 資料庫連接正常")
        except Exception as e:
            print(f"❌ 資料庫連接失敗: {e}")
            return False

        print("✅ 遷移環境驗證通過")
        return True

    def backup_database(self, backup_path: Optional[Path] = None) -> None:
        """備份資料庫"""
        if backup_path is None:
            backup_path = self.project_root / f"backup_{self.db_config['main_database']}.sql"

        print(f"💾 備份資料庫到: {backup_path}")

        try:
            with open(backup_path, "w") as f:
                subprocess.run(
                    [
                        "pg_dump",
                        self.db_config["url"],
                    ],
                    stdout=f,
                    check=True,
                )

            print("✅ 資料庫備份完成")
        except Exception as e:
            print(f"❌ 備份失敗: {e}")

    def restore_database(self, backup_path: Path) -> None:
        """還原資料庫"""
        print(f"♻️  從備份還原資料庫: {backup_path}")

        if not backup_path.exists():
            print(f"❌ 備份檔案不存在: {backup_path}")
            return

        try:
            with open(backup_path, "r") as f:
                subprocess.run(
                    [
                        "psql",
                        self.db_config["url"],
                    ],
                    stdin=f,
                    check=True,
                )

            print("✅ 資料庫還原完成")
        except Exception as e:
            print(f"❌ 還原失敗: {e}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="統一資料庫遷移管理")
    parser.add_argument(
        "command",
        choices=[
            "init",
            "create-db",
            "migrate",
            "upgrade",
            "downgrade",
            "current",
            "history",
            "validate",
            "backup",
            "restore",
        ],
        help="執行的命令",
    )

    parser.add_argument("--revision", help="指定版本 (用於 upgrade/downgrade)")
    parser.add_argument("--backup-path", help="備份檔案路徑")
    parser.add_argument("--message", "-m", help="遷移訊息")

    args = parser.parse_args()

    # 獲取專案根目錄
    project_root = Path(__file__).parent.parent
    manager = DatabaseMigrationManager(project_root)

    if args.command == "init":
        manager.create_databases()
        manager.init_alembic()
        manager.create_initial_migration()

    elif args.command == "create-db":
        manager.create_databases()

    elif args.command == "migrate":
        args.message or "Auto migration"
        manager.create_initial_migration()

    elif args.command == "upgrade":
        revision = args.revision or "head"
        manager.upgrade_database(revision)

    elif args.command == "downgrade":
        if not args.revision:
            print("❌ 降級需要指定版本 --revision")
            sys.exit(1)
        manager.downgrade_database(args.revision)

    elif args.command == "current":
        manager.show_current_revision()

    elif args.command == "history":
        manager.show_migration_history()

    elif args.command == "validate":
        manager.validate_migration_environment()

    elif args.command == "backup":
        backup_path = Path(args.backup_path) if args.backup_path else None
        manager.backup_database(backup_path)

    elif args.command == "restore":
        if not args.backup_path:
            print("❌ 還原需要指定備份檔案 --backup-path")
            sys.exit(1)
        manager.restore_database(Path(args.backup_path))


if __name__ == "__main__":
    main()
