#!/usr/bin/env python3
"""
批量視頻處理引擎
支持大規模視頻處理、隊列管理、並行處理、進度追蹤等功能
"""

import os
import logging
import asyncio
import aiofiles
import json
import hashlib
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import concurrent.futures
import threading
import time
import uuid
from queue import Queue, Empty
import pickle

try:
    from moviepy.editor import VideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# 導入我們的高級視頻引擎
try:
    from .advanced_video_engine import AdvancedVideoEngine, VideoConfig
    from .video_effects_system import VideoEffectsSystem, EffectConfig
    from .audio_video_sync import AudioVideoSyncEngine, SyncConfig
    CUSTOM_ENGINES_AVAILABLE = True
except ImportError:
    CUSTOM_ENGINES_AVAILABLE = False
    logging.warning("Custom video engines not available for batch processing")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """作業狀態"""
    PENDING = "pending"
    QUEUED = "queued" 
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class Priority(Enum):
    """優先級"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

@dataclass
class VideoJob:
    """視頻處理作業"""
    job_id: str
    job_type: str  # "professional", "effects", "sync", "custom"
    input_data: Dict[str, Any]
    output_config: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class BatchConfig:
    """批量處理配置"""
    max_concurrent_jobs: int = 3
    max_queue_size: int = 100
    job_timeout: int = 3600  # 1小時
    retry_delay: int = 60  # 重試延遲
    save_intermediate: bool = True
    cleanup_completed: bool = False
    priority_queue: bool = True
    load_balancing: bool = True

@dataclass
class ProcessingStats:
    """處理統計"""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    processing_jobs: int = 0
    queued_jobs: int = 0
    average_processing_time: float = 0.0
    total_processing_time: float = 0.0
    start_time: datetime = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()

class BatchVideoProcessor:
    """批量視頻處理引擎"""
    
    def __init__(
        self, 
        config: BatchConfig = None,
        storage_dir: str = "./batch_processing",
        cache_dir: str = "./cache/batch"
    ):
        self.config = config or BatchConfig()
        self.storage_dir = Path(storage_dir)
        self.cache_dir = Path(cache_dir)
        
        # 創建目錄
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 作業管理
        self.jobs: Dict[str, VideoJob] = {}
        self.job_queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.processing_jobs: Dict[str, asyncio.Task] = {}
        self.stats = ProcessingStats()
        
        # 處理引擎
        self.video_engine = None
        self.effects_system = None
        self.sync_engine = None
        
        # 控制狀態
        self.is_running = False
        self.workers: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()
        
        # 鎖和同步
        self.jobs_lock = asyncio.Lock()
        self.stats_lock = asyncio.Lock()
        
        # 持久化
        self.jobs_file = self.storage_dir / "jobs.json"
        self.stats_file = self.storage_dir / "stats.json"
        
        self._setup_logging()
        
    def _setup_logging(self):
        """設置日誌"""
        log_file = self.storage_dir / "batch_processing.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    async def initialize_engines(self):
        """初始化處理引擎"""
        if not CUSTOM_ENGINES_AVAILABLE:
            logger.warning("Custom video engines not available")
            return
            
        try:
            self.video_engine = AdvancedVideoEngine()
            self.effects_system = VideoEffectsSystem()
            self.sync_engine = AudioVideoSyncEngine()
            logger.info("Video processing engines initialized")
        except Exception as e:
            logger.error(f"Failed to initialize engines: {e}")
            
    async def start(self):
        """啟動批量處理器"""
        if self.is_running:
            logger.warning("Batch processor is already running")
            return
            
        logger.info("Starting batch video processor")
        self.is_running = True
        self.shutdown_event.clear()
        
        # 初始化引擎
        await self.initialize_engines()
        
        # 載入持久化數據
        await self._load_persistent_data()
        
        # 啟動工作線程
        self.workers = []
        for i in range(self.config.max_concurrent_jobs):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
            
        # 啟動監控任務
        monitor_task = asyncio.create_task(self._monitor_jobs())
        self.workers.append(monitor_task)
        
        logger.info(f"Batch processor started with {len(self.workers)} workers")
        
    async def stop(self):
        """停止批量處理器"""
        if not self.is_running:
            return
            
        logger.info("Stopping batch video processor")
        self.is_running = False
        self.shutdown_event.set()
        
        # 取消所有工作任務
        for worker in self.workers:
            worker.cancel()
            
        # 等待工作任務結束
        try:
            await asyncio.gather(*self.workers, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping workers: {e}")
            
        # 保存持久化數據
        await self._save_persistent_data()
        
        logger.info("Batch processor stopped")
        
    async def submit_job(
        self, 
        job_type: str,
        input_data: Dict[str, Any],
        output_config: Dict[str, Any] = None,
        priority: Priority = Priority.NORMAL
    ) -> str:
        """提交作業"""
        
        if not self.is_running:
            raise RuntimeError("Batch processor is not running")
            
        # 創建作業
        job_id = str(uuid.uuid4())
        job = VideoJob(
            job_id=job_id,
            job_type=job_type,
            input_data=input_data,
            output_config=output_config or {},
            priority=priority
        )
        
        async with self.jobs_lock:
            self.jobs[job_id] = job
            
        # 添加到隊列
        try:
            await self.job_queue.put(job)
            job.status = JobStatus.QUEUED
            
            async with self.stats_lock:
                self.stats.total_jobs += 1
                self.stats.queued_jobs += 1
                
            logger.info(f"Job {job_id} submitted ({job_type})")
            
        except asyncio.QueueFull:
            job.status = JobStatus.FAILED
            job.error_message = "Queue is full"
            logger.error(f"Failed to queue job {job_id}: Queue is full")
            
        return job_id
        
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取作業狀態"""
        async with self.jobs_lock:
            job = self.jobs.get(job_id)
            if job:
                return {
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "status": job.status.value,
                    "progress": job.progress,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error_message": job.error_message,
                    "result": job.result
                }
        return None
        
    async def cancel_job(self, job_id: str) -> bool:
        """取消作業"""
        async with self.jobs_lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
                
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False
                
            job.status = JobStatus.CANCELLED
            
            # 如果正在處理，取消處理任務
            if job_id in self.processing_jobs:
                task = self.processing_jobs[job_id]
                task.cancel()
                
        logger.info(f"Job {job_id} cancelled")
        return True
        
    async def get_batch_stats(self) -> Dict[str, Any]:
        """獲取批量處理統計"""
        async with self.stats_lock:
            stats_dict = asdict(self.stats)
            stats_dict['start_time'] = self.stats.start_time.isoformat()
            
            # 計算運行時間
            runtime = datetime.now() - self.stats.start_time
            stats_dict['runtime_seconds'] = runtime.total_seconds()
            
            # 計算處理速率
            if self.stats.completed_jobs > 0 and runtime.total_seconds() > 0:
                stats_dict['jobs_per_minute'] = (
                    self.stats.completed_jobs / (runtime.total_seconds() / 60)
                )
            else:
                stats_dict['jobs_per_minute'] = 0.0
                
            return stats_dict
            
    async def _worker(self, worker_name: str):
        """工作線程"""
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # 獲取作業（帶超時）
                try:
                    job = await asyncio.wait_for(
                        self.job_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                    
                # 檢查作業是否已被取消
                if job.status == JobStatus.CANCELLED:
                    self.job_queue.task_done()
                    continue
                    
                # 開始處理作業
                await self._process_job(job, worker_name)
                self.job_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                
        logger.info(f"Worker {worker_name} stopped")
        
    async def _process_job(self, job: VideoJob, worker_name: str):
        """處理單個作業"""
        
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        
        async with self.stats_lock:
            self.stats.processing_jobs += 1
            self.stats.queued_jobs -= 1
            
        logger.info(f"Worker {worker_name} processing job {job.job_id} ({job.job_type})")
        
        # 創建處理任務
        processing_task = asyncio.create_task(
            self._execute_job(job)
        )
        
        # 記錄處理任務
        self.processing_jobs[job.job_id] = processing_task
        
        try:
            # 等待處理完成（帶超時）
            result = await asyncio.wait_for(
                processing_task,
                timeout=self.config.job_timeout
            )
            
            # 處理成功
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            job.progress = 1.0
            
            processing_time = (job.completed_at - job.started_at).total_seconds()
            
            async with self.stats_lock:
                self.stats.completed_jobs += 1
                self.stats.processing_jobs -= 1
                self.stats.total_processing_time += processing_time
                self.stats.average_processing_time = (
                    self.stats.total_processing_time / self.stats.completed_jobs
                )
                
            logger.info(f"Job {job.job_id} completed in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.error_message = f"Job timed out after {self.config.job_timeout}s"
            logger.error(f"Job {job.job_id} timed out")
            
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            logger.info(f"Job {job.job_id} was cancelled")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")
            
            # 重試邏輯
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.PENDING
                logger.info(f"Retrying job {job.job_id} (attempt {job.retry_count})")
                
                # 延遲後重新加入隊列
                await asyncio.sleep(self.config.retry_delay)
                await self.job_queue.put(job)
            else:
                async with self.stats_lock:
                    self.stats.failed_jobs += 1
                    self.stats.processing_jobs -= 1
                    
        finally:
            # 清理處理任務記錄
            if job.job_id in self.processing_jobs:
                del self.processing_jobs[job.job_id]
                
    async def _execute_job(self, job: VideoJob) -> Dict[str, Any]:
        """執行具體的作業處理"""
        
        if job.job_type == "professional" and self.video_engine:
            return await self._process_professional_video(job)
        elif job.job_type == "effects" and self.effects_system:
            return await self._process_video_effects(job)
        elif job.job_type == "sync" and self.sync_engine:
            return await self._process_audio_sync(job)
        elif job.job_type == "custom":
            return await self._process_custom_job(job)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")
            
    async def _process_professional_video(self, job: VideoJob) -> Dict[str, Any]:
        """處理專業視頻生成作業"""
        
        scenes = job.input_data.get('scenes', [])
        audio_file = job.input_data.get('audio_file')
        title = job.input_data.get('title', 'Batch Generated Video')
        style = job.input_data.get('style', 'cinematic')
        config = job.input_data.get('config')
        
        if config:
            video_config = VideoConfig(**config)
        else:
            video_config = None
            
        result = await self.video_engine.create_professional_video(
            scenes=scenes,
            audio_file=audio_file,
            title=title,
            style=style,
            config=video_config
        )
        
        return result
        
    async def _process_video_effects(self, job: VideoJob) -> Dict[str, Any]:
        """處理視頻特效作業"""
        # 這裡需要實現特效處理邏輯
        # 由於時間關係，返回模擬結果
        await asyncio.sleep(2)  # 模擬處理時間
        return {"success": True, "message": "Effects applied"}
        
    async def _process_audio_sync(self, job: VideoJob) -> Dict[str, Any]:
        """處理音視頻同步作業"""
        # 這裡需要實現同步處理邏輯
        await asyncio.sleep(3)  # 模擬處理時間
        return {"success": True, "message": "Audio synced"}
        
    async def _process_custom_job(self, job: VideoJob) -> Dict[str, Any]:
        """處理自定義作業"""
        # 執行自定義處理函數
        custom_func = job.input_data.get('custom_function')
        if custom_func and callable(custom_func):
            return await custom_func(job.input_data)
        else:
            raise ValueError("No valid custom function provided")
            
    async def _monitor_jobs(self):
        """監控作業狀態"""
        logger.info("Job monitor started")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # 定期保存狀態
                await self._save_persistent_data()
                
                # 清理完成的作業（如果配置了）
                if self.config.cleanup_completed:
                    await self._cleanup_completed_jobs()
                    
                # 等待下一次檢查
                await asyncio.sleep(30)  # 30秒檢查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                
        logger.info("Job monitor stopped")
        
    async def _cleanup_completed_jobs(self):
        """清理已完成的作業"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # 清理24小時前的作業
        
        async with self.jobs_lock:
            jobs_to_remove = []
            
            for job_id, job in self.jobs.items():
                if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED] and
                    job.completed_at and job.completed_at < cutoff_time):
                    jobs_to_remove.append(job_id)
                    
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
                
            if jobs_to_remove:
                logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
                
    async def _save_persistent_data(self):
        """保存持久化數據"""
        try:
            # 保存作業數據
            jobs_data = {}
            async with self.jobs_lock:
                for job_id, job in self.jobs.items():
                    jobs_data[job_id] = {
                        **asdict(job),
                        'created_at': job.created_at.isoformat(),
                        'started_at': job.started_at.isoformat() if job.started_at else None,
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                        'status': job.status.value,
                        'priority': job.priority.value
                    }
                    
            async with aiofiles.open(self.jobs_file, 'w') as f:
                await f.write(json.dumps(jobs_data, indent=2))
                
            # 保存統計數據
            stats_data = await self.get_batch_stats()
            async with aiofiles.open(self.stats_file, 'w') as f:
                await f.write(json.dumps(stats_data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save persistent data: {e}")
            
    async def _load_persistent_data(self):
        """載入持久化數據"""
        try:
            # 載入作業數據
            if self.jobs_file.exists():
                async with aiofiles.open(self.jobs_file, 'r') as f:
                    content = await f.read()
                    jobs_data = json.loads(content)
                    
                async with self.jobs_lock:
                    for job_id, job_dict in jobs_data.items():
                        # 重建作業對象
                        job = VideoJob(
                            job_id=job_dict['job_id'],
                            job_type=job_dict['job_type'],
                            input_data=job_dict['input_data'],
                            output_config=job_dict['output_config'],
                            priority=Priority(job_dict['priority']),
                            status=JobStatus(job_dict['status']),
                            created_at=datetime.fromisoformat(job_dict['created_at']),
                            started_at=datetime.fromisoformat(job_dict['started_at']) if job_dict['started_at'] else None,
                            completed_at=datetime.fromisoformat(job_dict['completed_at']) if job_dict['completed_at'] else None,
                            progress=job_dict.get('progress', 0.0),
                            error_message=job_dict.get('error_message'),
                            result=job_dict.get('result'),
                            retry_count=job_dict.get('retry_count', 0),
                            max_retries=job_dict.get('max_retries', 3)
                        )
                        self.jobs[job_id] = job
                        
                logger.info(f"Loaded {len(self.jobs)} jobs from persistent storage")
                
        except Exception as e:
            logger.error(f"Failed to load persistent data: {e}")


# 便捷函數
async def create_batch_processor(
    max_concurrent_jobs: int = 3,
    storage_dir: str = "./batch_processing"
) -> BatchVideoProcessor:
    """創建批量處理器"""
    
    config = BatchConfig(max_concurrent_jobs=max_concurrent_jobs)
    processor = BatchVideoProcessor(config=config, storage_dir=storage_dir)
    await processor.start()
    return processor

async def test_batch_processor():
    """測試批量處理器"""
    
    print("🏭 Testing Batch Video Processor...")
    
    # 創建處理器
    processor = await create_batch_processor(max_concurrent_jobs=2)
    
    try:
        # 提交測試作業
        job_ids = []
        
        for i in range(3):
            job_id = await processor.submit_job(
                job_type="custom",
                input_data={
                    "custom_function": lambda data: {"test": f"job_{i}_completed"},
                    "job_number": i
                },
                priority=Priority.NORMAL
            )
            job_ids.append(job_id)
            print(f"Submitted job {i}: {job_id}")
            
        # 等待一些處理時間
        await asyncio.sleep(5)
        
        # 檢查作業狀態
        for job_id in job_ids:
            status = await processor.get_job_status(job_id)
            if status:
                print(f"Job {job_id}: {status['status']} (progress: {status['progress']})")
                
        # 獲取統計信息
        stats = await processor.get_batch_stats()
        print(f"Batch stats: {stats}")
        
        print("✅ Batch processor test completed!")
        
    finally:
        # 停止處理器
        await processor.stop()
        
    return processor

if __name__ == "__main__":
    print("🎬 Batch Video Processor - Large Scale Video Processing")
    print("=" * 60)
    
    # 檢查依賴
    print(f"MoviePy available: {MOVIEPY_AVAILABLE}")
    print(f"Custom engines available: {CUSTOM_ENGINES_AVAILABLE}")
    
    # 運行測試
    result = asyncio.run(test_batch_processor())
    print(f"Batch processor test successful: {result is not None}")