"""
Database Connection and Management

This module handles PostgreSQL database connections, connection pooling,
and database initialization for the video service.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and pool management"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = self._get_database_url()

    def _get_database_url(self) -> str:
        """Construct database URL from environment variables"""

        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "video_service")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    async def initialize(
        self, min_connections: int = 5, max_connections: int = 20
    ):
        """Initialize database connection pool"""

        try:
            logger.info("Initializing database connection pool...")

            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_connections,
                max_size=max_connections,
                command_timeout=60,
                server_settings={
                    "jit": "off",  # Disable JIT for better compatibility
                    "application_name": "video-service",
                },
            )

            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Connected to PostgreSQL: {version}")

            # Initialize database schema
            await self._initialize_schema()

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def _initialize_schema(self):
        """Initialize database schema and tables"""

        try:
            async with self.pool.acquire() as conn:
                # Create extensions if needed
                await conn.execute(
                    'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
                )
                await conn.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm";')

                # Import and create tables
                from .models.video_project import VideoProject

                await VideoProject.create_table(self.pool)

                logger.info("Database schema initialized")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {str(e)}")
            raise

    async def close(self):
        """Close database connection pool"""

        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool (context manager)"""

        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as conn:
            yield conn

    async def health_check(self) -> dict:
        """Check database health status"""

        try:
            async with self.pool.acquire() as conn:
                # Simple query to test connection
                result = await conn.fetchval("SELECT 1")

                # Get pool stats
                pool_stats = {
                    "size": self.pool.get_size(),
                    "available": len(self.pool._holders),
                    "max_size": self.pool.get_max_size(),
                    "min_size": self.pool.get_min_size(),
                }

                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "query_result": result,
                    "pool_stats": pool_stats,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "postgresql",
                "error": str(e),
            }


# Global database manager instance
_db_manager = None


async def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""

    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()

    return _db_manager


async def get_db_connection():
    """FastAPI dependency for database connections"""

    db_manager = await get_database_manager()
    return db_manager.pool


@asynccontextmanager
async def get_db_transaction():
    """Get database transaction (context manager)"""

    db_manager = await get_database_manager()

    async with db_manager.pool.acquire() as conn:
        async with conn.transaction():
            yield conn


async def execute_query(query: str, *args) -> list:
    """Execute query and return results"""

    db_manager = await get_database_manager()

    async with db_manager.pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute_single(query: str, *args):
    """Execute query and return single result"""

    db_manager = await get_database_manager()

    async with db_manager.pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute_scalar(query: str, *args):
    """Execute query and return scalar value"""

    db_manager = await get_database_manager()

    async with db_manager.pool.acquire() as conn:
        return await conn.fetchval(query, *args)


async def execute_command(query: str, *args) -> str:
    """Execute command and return status"""

    db_manager = await get_database_manager()

    async with db_manager.pool.acquire() as conn:
        return await conn.execute(query, *args)


class DatabaseError(Exception):
    """Custom database error"""



class TransactionManager:
    """Transaction management utility"""

    def __init__(self, connection):
        self.connection = connection
        self.transaction = None

    async def __aenter__(self):
        self.transaction = self.connection.transaction()
        await self.transaction.start()
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.transaction.commit()
        else:
            await self.transaction.rollback()


async def run_migrations():
    """Run database migrations"""

    logger.info("Running database migrations...")

    try:
        db_manager = await get_database_manager()

        async with db_manager.pool.acquire() as conn:
            # Create migrations table if it doesn't exist
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # Get current version
            current_version = (
                await conn.fetchval(
                    "SELECT MAX(version) FROM schema_migrations"
                )
                or 0
            )

            # Define migrations
            migrations = {
                1: """
                    -- Initial video projects table
                    -- Already created in VideoProject.create_table()
                    SELECT 1;
                """,
                2: """
                    -- Add indexes for better performance
                    CREATE INDEX IF NOT EXISTS idx_video_projects_theme ON video_projects(theme);
                    CREATE INDEX IF NOT EXISTS idx_video_projects_platform ON video_projects(target_platform);
                """,
                3: """
                    -- Add analytics columns
                    ALTER TABLE video_projects 
                    ADD COLUMN IF NOT EXISTS processing_time INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS file_size BIGINT DEFAULT 0;
                """,
            }

            # Apply new migrations
            for version, sql in migrations.items():
                if version > current_version:
                    logger.info(f"Applying migration version {version}")

                    async with conn.transaction():
                        await conn.execute(sql)
                        await conn.execute(
                            "INSERT INTO schema_migrations (version) VALUES ($1)",
                            version,
                        )

                    logger.info(
                        f"Migration version {version} applied successfully"
                    )

            logger.info("All migrations completed")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise DatabaseError(f"Migration failed: {str(e)}")


async def cleanup_old_data(days: int = 30):
    """Clean up old video generation data"""

    logger.info(f"Cleaning up data older than {days} days...")

    try:
        db_manager = await get_database_manager()

        async with db_manager.pool.acquire() as conn:
            # Delete old failed/cancelled projects
            result = await conn.execute(
                """
                DELETE FROM video_projects 
                WHERE status IN ('failed', 'cancelled') 
                AND created_at < NOW() - INTERVAL '%s days'
            """,
                days,
            )

            logger.info(f"Cleaned up old projects: {result}")

    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        raise DatabaseError(f"Data cleanup failed: {str(e)}")


# Startup and shutdown handlers
async def startup_database():
    """Database startup handler"""

    try:
        db_manager = await get_database_manager()
        await run_migrations()
        logger.info("Database startup completed")

    except Exception as e:
        logger.error(f"Database startup failed: {str(e)}")
        raise


async def shutdown_database():
    """Database shutdown handler"""

    global _db_manager

    if _db_manager:
        await _db_manager.close()
        _db_manager = None
        logger.info("Database shutdown completed")
