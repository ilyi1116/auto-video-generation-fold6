"""
統一的資料庫連接管理
"""

import os
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from .models import Base

# 從環境變數獲取資料庫連接字符串
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./auto_video.db"  # 開發時使用SQLite，生產時使用PostgreSQL
)

# 轉換為異步連接字符串
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# 創建同步和異步引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite 特殊配置
    sync_engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )
else:
    # PostgreSQL 或其他資料庫配置
    sync_engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# 創建會話工廠
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """同步資料庫會話依賴"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """異步資料庫會話依賴"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


async def create_tables():
    """創建所有資料表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """刪除所有資料表 (慎用!)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def create_tables_sync():
    """同步創建所有資料表"""
    Base.metadata.create_all(bind=sync_engine)


def drop_tables_sync():
    """同步刪除所有資料表 (慎用!)"""
    Base.metadata.drop_all(bind=sync_engine)
