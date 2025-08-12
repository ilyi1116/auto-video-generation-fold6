"""
Test Data Cleanup System
智能測試數據清理系統 - 確保測試環境的一致性和可靠性
"""

import asyncio
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import aiofiles
import aioredis
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TestDataCleaner:
    """Comprehensive test data cleanup manager"""
    
    def __init__(self):
        self.cleanup_tasks: List[Dict[str, Any]] = []
        self.temp_files: Set[Path] = set()
        self.temp_directories: Set[Path] = set()
        self.redis_keys: Set[str] = set()
        self.database_records: List[Dict[str, Any]] = []
        self.external_resources: List[Dict[str, Any]] = []
        
    def register_temp_file(self, file_path: Path):
        """Register a temporary file for cleanup"""
        self.temp_files.add(file_path)
        
    def register_temp_directory(self, dir_path: Path):
        """Register a temporary directory for cleanup"""
        self.temp_directories.add(dir_path)
        
    def register_redis_key(self, key: str):
        """Register a Redis key for cleanup"""
        self.redis_keys.add(key)
        
    def register_database_record(self, table: str, record_id: Any):
        """Register a database record for cleanup"""
        self.database_records.append({
            'table': table,
            'id': record_id,
            'type': 'database'
        })
        
    def register_external_resource(self, resource_type: str, resource_id: str, cleanup_func=None):
        """Register an external resource for cleanup"""
        self.external_resources.append({
            'type': resource_type,
            'id': resource_id,
            'cleanup_function': cleanup_func
        })
        
    def register_cleanup_task(self, cleanup_func, description: str = ""):
        """Register a custom cleanup task"""
        self.cleanup_tasks.append({
            'function': cleanup_func,
            'description': description
        })
        
    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        logger.info(f"Cleaning up {len(self.temp_files)} temporary files")
        
        for file_path in self.temp_files:
            try:
                if file_path.exists():
                    await aiofiles.os.remove(file_path)
                    logger.debug(f"Removed temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")
                
        self.temp_files.clear()
        
    async def cleanup_temp_directories(self):
        """Clean up temporary directories"""
        logger.info(f"Cleaning up {len(self.temp_directories)} temporary directories")
        
        for dir_path in self.temp_directories:
            try:
                if dir_path.exists() and dir_path.is_dir():
                    # Remove all files in directory first
                    for file_path in dir_path.rglob('*'):
                        if file_path.is_file():
                            await aiofiles.os.remove(file_path)
                    
                    # Remove directory
                    await aiofiles.os.rmdir(dir_path)
                    logger.debug(f"Removed temp directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temp directory {dir_path}: {e}")
                
        self.temp_directories.clear()
        
    async def cleanup_redis_keys(self, redis_url: str = "redis://localhost:6379/15"):
        """Clean up Redis keys"""
        if not self.redis_keys:
            return
            
        logger.info(f"Cleaning up {len(self.redis_keys)} Redis keys")
        
        try:
            redis = await aioredis.from_url(redis_url)
            
            for key in self.redis_keys:
                try:
                    await redis.delete(key)
                    logger.debug(f"Removed Redis key: {key}")
                except Exception as e:
                    logger.warning(f"Failed to remove Redis key {key}: {e}")
                    
            await redis.close()
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis for cleanup: {e}")
            
        self.redis_keys.clear()
        
    async def cleanup_database_records(self, db_session: AsyncSession):
        """Clean up database records"""
        if not self.database_records:
            return
            
        logger.info(f"Cleaning up {len(self.database_records)} database records")
        
        try:
            for record in reversed(self.database_records):  # Reverse order for FK constraints
                try:
                    table_name = record['table']
                    record_id = record['id']
                    
                    # Execute delete query
                    await db_session.execute(
                        f"DELETE FROM {table_name} WHERE id = :id",
                        {'id': record_id}
                    )
                    logger.debug(f"Removed {table_name} record: {record_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to remove {record['table']} record {record['id']}: {e}")
                    
            await db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to cleanup database records: {e}")
            await db_session.rollback()
            
        self.database_records.clear()
        
    async def cleanup_external_resources(self):
        """Clean up external resources"""
        if not self.external_resources:
            return
            
        logger.info(f"Cleaning up {len(self.external_resources)} external resources")
        
        for resource in self.external_resources:
            try:
                cleanup_func = resource.get('cleanup_function')
                if cleanup_func and callable(cleanup_func):
                    await cleanup_func(resource['id'])
                    logger.debug(f"Cleaned up {resource['type']}: {resource['id']}")
                else:
                    logger.debug(f"No cleanup function for {resource['type']}: {resource['id']}")
                    
            except Exception as e:
                logger.warning(f"Failed to cleanup {resource['type']} {resource['id']}: {e}")
                
        self.external_resources.clear()
        
    async def run_custom_cleanup_tasks(self):
        """Run custom cleanup tasks"""
        if not self.cleanup_tasks:
            return
            
        logger.info(f"Running {len(self.cleanup_tasks)} custom cleanup tasks")
        
        for task in self.cleanup_tasks:
            try:
                cleanup_func = task['function']
                description = task.get('description', 'Custom cleanup task')
                
                if callable(cleanup_func):
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await cleanup_func()
                    else:
                        cleanup_func()
                    logger.debug(f"Completed cleanup task: {description}")
                    
            except Exception as e:
                logger.warning(f"Cleanup task failed: {task.get('description', 'Unknown')}: {e}")
                
        self.cleanup_tasks.clear()
        
    async def cleanup_all(self, db_session: Optional[AsyncSession] = None, redis_url: str = "redis://localhost:6379/15"):
        """Run all cleanup operations"""
        logger.info("Starting comprehensive test data cleanup")
        
        # Clean up in reverse order of creation
        cleanup_operations = [
            ("Custom cleanup tasks", self.run_custom_cleanup_tasks()),
            ("External resources", self.cleanup_external_resources()),
            ("Redis keys", self.cleanup_redis_keys(redis_url)),
            ("Temporary files", self.cleanup_temp_files()),
            ("Temporary directories", self.cleanup_temp_directories()),
        ]
        
        # Add database cleanup if session provided
        if db_session:
            cleanup_operations.insert(-2, ("Database records", self.cleanup_database_records(db_session)))
            
        # Execute cleanup operations
        for description, operation in cleanup_operations:
            try:
                await operation
                logger.debug(f"Completed: {description}")
            except Exception as e:
                logger.error(f"Failed {description}: {e}")
                
        logger.info("Test data cleanup completed")
        
    def get_cleanup_summary(self) -> Dict[str, int]:
        """Get summary of items to be cleaned up"""
        return {
            'temp_files': len(self.temp_files),
            'temp_directories': len(self.temp_directories),
            'redis_keys': len(self.redis_keys),
            'database_records': len(self.database_records),
            'external_resources': len(self.external_resources),
            'custom_tasks': len(self.cleanup_tasks),
        }


class TestFileManager:
    """Manage test files with automatic cleanup"""
    
    def __init__(self, cleaner: TestDataCleaner):
        self.cleaner = cleaner
        self.base_temp_dir = None
        
    @asynccontextmanager
    async def temp_directory(self, prefix: str = "test_"):
        """Context manager for temporary directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.cleaner.register_temp_directory(temp_dir)
        
        try:
            yield temp_dir
        finally:
            # Cleanup is handled by the cleaner
            pass
            
    @asynccontextmanager
    async def temp_file(self, suffix: str = "", prefix: str = "test_", content: Optional[str] = None):
        """Context manager for temporary file"""
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        temp_file_path = Path(temp_path)
        
        try:
            os.close(fd)  # Close the file descriptor
            
            if content is not None:
                async with aiofiles.open(temp_file_path, 'w') as f:
                    await f.write(content)
                    
            self.cleaner.register_temp_file(temp_file_path)
            yield temp_file_path
            
        finally:
            # Cleanup is handled by the cleaner
            pass
            
    async def create_test_video_file(self, duration_seconds: int = 30) -> Path:
        """Create a test video file"""
        async with self.temp_file(suffix=".mp4", prefix="test_video_") as video_path:
            # Create a dummy video file (in real implementation, use ffmpeg)
            async with aiofiles.open(video_path, 'wb') as f:
                # Write dummy video header
                dummy_content = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom'
                await f.write(dummy_content)
                
            return video_path
            
    async def create_test_audio_file(self, duration_seconds: int = 30) -> Path:
        """Create a test audio file"""
        async with self.temp_file(suffix=".mp3", prefix="test_audio_") as audio_path:
            # Create a dummy audio file
            async with aiofiles.open(audio_path, 'wb') as f:
                # Write dummy MP3 header
                dummy_content = b'\xFF\xFB\x90\x00'  # Basic MP3 header
                await f.write(dummy_content)
                
            return audio_path
            
    async def create_test_image_file(self, width: int = 1920, height: int = 1080) -> Path:
        """Create a test image file"""
        async with self.temp_file(suffix=".jpg", prefix="test_image_") as image_path:
            # Create a dummy image file
            async with aiofiles.open(image_path, 'wb') as f:
                # Write dummy JPEG header
                dummy_content = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
                await f.write(dummy_content)
                
            return image_path


class MockResourceManager:
    """Manage mock external resources"""
    
    def __init__(self, cleaner: TestDataCleaner):
        self.cleaner = cleaner
        self.mock_endpoints = {}
        self.mock_responses = {}
        
    def register_mock_api_endpoint(self, url: str, response_data: Dict[str, Any]):
        """Register a mock API endpoint"""
        self.mock_endpoints[url] = response_data
        self.cleaner.register_cleanup_task(
            lambda: self.mock_endpoints.pop(url, None),
            f"Remove mock endpoint: {url}"
        )
        
    def register_mock_file_upload(self, file_id: str, file_url: str):
        """Register a mock file upload"""
        self.mock_responses[file_id] = file_url
        self.cleaner.register_external_resource(
            'mock_file_upload', 
            file_id,
            self._cleanup_mock_file
        )
        
    async def _cleanup_mock_file(self, file_id: str):
        """Clean up mock file"""
        self.mock_responses.pop(file_id, None)


# Global test data cleaner instance
global_test_cleaner = TestDataCleaner()


# Pytest integration
import pytest


@pytest.fixture(scope="function")
async def test_data_cleaner():
    """Test data cleaner fixture with automatic cleanup"""
    cleaner = TestDataCleaner()
    yield cleaner
    
    # Automatic cleanup
    try:
        await cleaner.cleanup_all()
    except Exception as e:
        logger.error(f"Fixture cleanup failed: {e}")


@pytest.fixture(scope="function")
async def test_file_manager(test_data_cleaner):
    """Test file manager fixture"""
    return TestFileManager(test_data_cleaner)


@pytest.fixture(scope="function")
async def mock_resource_manager(test_data_cleaner):
    """Mock resource manager fixture"""
    return MockResourceManager(test_data_cleaner)


@pytest.fixture(scope="session")
async def global_test_cleanup():
    """Global test cleanup for session"""
    yield
    
    # Final cleanup at session end
    try:
        await global_test_cleaner.cleanup_all()
    except Exception as e:
        logger.error(f"Global cleanup failed: {e}")


# Test utility functions
async def assert_cleanup_successful(cleaner: TestDataCleaner):
    """Assert that cleanup was successful"""
    summary = cleaner.get_cleanup_summary()
    
    # Check that all collections are empty
    for resource_type, count in summary.items():
        assert count == 0, f"Cleanup incomplete: {count} {resource_type} remaining"
        
    logger.info("Cleanup verification successful")


def cleanup_on_failure(cleaner: TestDataCleaner):
    """Decorator to ensure cleanup on test failure"""
    def decorator(test_func):
        async def wrapper(*args, **kwargs):
            try:
                return await test_func(*args, **kwargs)
            except Exception as e:
                await cleaner.cleanup_all()
                raise e
        return wrapper
    return decorator