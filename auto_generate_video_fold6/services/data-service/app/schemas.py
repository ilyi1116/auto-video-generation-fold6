from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    INFERENCE = "inference"


class VoiceFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class VoiceFileCreate(VoiceFileBase):
    user_id: int
    file_path: str
    s3_key: Optional[str] = None


class VoiceFileUpdate(BaseModel):
    status: Optional[FileStatus] = None
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    s3_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VoiceFile(VoiceFileBase):
    id: int
    user_id: int
    file_path: str
    s3_key: Optional[str] = None
    status: FileStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcessingJobBase(BaseModel):
    job_type: JobType
    progress: int = 0
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ProcessingJobCreate(ProcessingJobBase):
    user_id: int
    voice_file_id: int
    celery_task_id: Optional[str] = None


class ProcessingJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingJob(ProcessingJobBase):
    id: int
    user_id: int
    voice_file_id: int
    status: JobStatus
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    message: str
    file_id: int
    filename: str
    size: int
    job_id: Optional[int] = None


class ProcessingResponse(BaseModel):
    message: str
    job_id: int
    status: JobStatus


class FileValidationError(BaseModel):
    error: str
    details: Dict[str, Any]
