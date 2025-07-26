from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class StoredFile(Base):
    """Model for tracking stored files"""

    __tablename__ = "stored_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    # File metadata
    original_filename = Column(String, nullable=False)
    filename = Column(String, nullable=False)  # Generated filename
    file_path = Column(String, nullable=False)  # Storage path
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)  # SHA-256 hash for deduplication

    # File categorization
    file_type = Column(String, nullable=False)  # image, audio, video, document
    category = Column(String)  # generated, uploaded, processed

    # Storage information
    storage_backend = Column(String, nullable=False)  # s3, minio, local
    bucket_name = Column(String)
    object_key = Column(String)
    public_url = Column(String)
    cdn_url = Column(String)

    # Processing information
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_metadata = Column(JSON)

    # Image-specific metadata
    image_width = Column(Integer)
    image_height = Column(Integer)
    image_format = Column(String)
    has_thumbnail = Column(Boolean, default=False)
    thumbnail_path = Column(String)

    # Audio-specific metadata
    audio_duration = Column(Integer)  # Duration in seconds
    audio_bitrate = Column(Integer)
    audio_sample_rate = Column(Integer)
    audio_channels = Column(Integer)

    # Video-specific metadata
    video_duration = Column(Integer)  # Duration in seconds
    video_width = Column(Integer)
    video_height = Column(Integer)
    video_fps = Column(Integer)
    video_bitrate = Column(Integer)
    video_codec = Column(String)

    # Security and moderation
    virus_scan_status = Column(String, default="pending")  # pending, clean, infected, failed
    content_moderation_status = Column(String, default="pending")  # pending, approved, rejected
    content_moderation_flags = Column(JSON)

    # Access control
    is_public = Column(Boolean, default=False)
    access_level = Column(String, default="private")  # private, public, shared
    shared_token = Column(String)
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True))

    # Metadata
    tags = Column(JSON)
    description = Column(Text)
    project_id = Column(String, index=True)

    def __repr__(self):
        return f"<StoredFile(id={self.id}, filename={self.filename}, file_type={self.file_type})>"


class FileProcessingJob(Base):
    """Model for tracking file processing jobs"""

    __tablename__ = "file_processing_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Job information
    job_type = Column(String, nullable=False)  # thumbnail, transcode, compress, enhance
    status = Column(String, default="pending")  # pending, processing, completed, failed
    priority = Column(Integer, default=5)  # 1-10, lower is higher priority

    # Processing parameters
    input_parameters = Column(JSON)
    output_parameters = Column(JSON)

    # Results
    output_file_id = Column(String)
    output_file_path = Column(String)
    processing_time_seconds = Column(Integer)
    error_message = Column(Text)

    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String)
    total_steps = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<FileProcessingJob(id={self.id}, job_type={self.job_type}, status={self.status})>"


class FileDownload(Base):
    """Model for tracking file downloads"""

    __tablename__ = "file_downloads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, nullable=False, index=True)
    user_id = Column(String, index=True)

    # Download information
    ip_address = Column(String)
    user_agent = Column(String)
    referer = Column(String)
    download_token = Column(String)

    # Timestamps
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FileDownload(id={self.id}, file_id={self.file_id})>"
