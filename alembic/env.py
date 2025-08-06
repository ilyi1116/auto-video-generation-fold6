#!/usr/bin/env python3
"""
統一資料庫遷移環境配置
支援多服務資料庫遷移管理
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auto_generate_video_fold6"))

# 導入統一的資料庫模型
try:
    from src.shared.database.models import (
        Base,
    )

    print("✅ 成功導入所有統一資料庫模型")

except ImportError as e:
    print(f"警告: 無法導入統一模型: {e}")
    # 嘗試舊版導入
    try:
        from auto_generate_video_fold6.models import Base

        print("✅ 使用舊版模型作為備選")
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()
        print("⚠️ 使用基礎 Base 物件")

# 配置設定
config = context.config

# 設定資料庫 URL
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/auto_video_db",
)

config.set_main_option("sqlalchemy.url", database_url)

# 解析配置文件的日誌設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 統一所有服務的 metadata
target_metadata = Base.metadata


def get_database_url() -> str:
    """獲取資料庫連接 URL"""
    return database_url


def run_migrations_offline() -> None:
    """離線模式執行遷移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """執行遷移的核心邏輯"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # 指定遷移時的模式名稱
        version_table_schema=None,
        # 忽略某些表的自動生成
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同步模式執行遷移"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """線上模式執行遷移"""
    asyncio.run(run_async_migrations())


# 檢查執行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
