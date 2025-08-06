from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Main database engine (read/write)
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
    echo=settings.debug,
)

# Read replica engine (if configured)
read_engine = None
if settings.database_read_url:
    read_engine = create_engine(
        settings.database_read_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
        pool_pre_ping=True,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engine or engine)

Base = declarative_base()


def get_db():
    """Database dependency for FastAPI (read/write)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db():
    """Database dependency for FastAPI (read-only)"""
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions (read/write)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_read_db_context():
    """Context manager for database sessions (read-only)"""
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()
