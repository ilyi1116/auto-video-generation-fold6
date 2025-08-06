"""
排程任務相關模型
"""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from .base import Base


class ScheduledTask(Base):
    """排程任務模型"""

    __tablename__ = "scheduled_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    # Task metadata
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(100), nullable=False)  # video_generation, trend_analysis, etc.
    description = Column(Text)

    # Scheduling configuration
    schedule_type = Column(String(50))  # once, hourly, daily, weekly, monthly, cron
    cron_expression = Column(String(100))  # for cron-based scheduling
    timezone = Column(String(50), default="Asia/Taipei")

    # Task parameters
    task_parameters = Column(JSON)

    # Status and control
    is_active = Column(Boolean, default=True)
    is_running = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed, disabled

    # Execution tracking
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))

    # Error handling
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    current_retry_count = Column(Integer, default=0)
    last_error_message = Column(Text)

    # Notifications
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notification_channels = Column(JSON)  # email, webhook, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, task_name='{self.task_name}')>"


class TaskExecution(Base):
    """任務執行記錄模型"""

    __tablename__ = "task_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Execution metadata
    execution_type = Column(String(50))  # scheduled, manual, retry
    trigger_source = Column(String(100))  # scheduler, user, webhook, etc.

    # Execution details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Status and results
    status = Column(String(20))  # running, completed, failed, cancelled
    result_data = Column(JSON)
    error_message = Column(Text)
    error_traceback = Column(Text)

    # Resource usage
    memory_usage_mb = Column(Integer)
    cpu_usage_percent = Column(Integer)

    # Output tracking
    files_created = Column(JSON)  # list of created file paths/urls
    notifications_sent = Column(JSON)  # notification delivery status

    # Retry information
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)
    parent_execution_id = Column(String)  # reference to original execution

    def __repr__(self):
        return f"<TaskExecution(id={self.id}, status='{self.status}')>"
