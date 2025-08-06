"""
語音模型數據庫模型
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ModelStatus(enum.Enum):
    """模型狀態"""

    TRAINING = "training"  # 訓練中
    TRAINED = "trained"  # 已訓練
    VALIDATING = "validating"  # 驗證中
    READY = "ready"  # 就緒
    DEPLOYED = "deployed"  # 已部署
    FAILED = "failed"  # 失敗
    ARCHIVED = "archived"  # 已歸檔


class ModelType(enum.Enum):
    """模型類型"""

    TTS = "tts"  # 文本轉語音
    VOICE_CLONE = "voice_clone"  # 語音克隆
    VOICE_ENHANCE = "voice_enhance"  # 語音增強
    VOICE_CONVERT = "voice_convert"  # 語音轉換


class VoiceModel(Base):
    """語音模型表"""

    __tablename__ = "voice_models"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # 模型類型和狀態
    model_type = Column(Enum(ModelType), nullable=False)
    status = Column(Enum(ModelStatus), default=ModelStatus.TRAINING)
    version = Column(String(20), default="1.0.0")

    # 模型文件信息
    model_path = Column(String(500))
    config_path = Column(String(500))
    checkpoint_path = Column(String(500))

    # 訓練信息
    training_dataset = Column(String(200))
    training_duration = Column(Integer)  # 訓練時長（秒）
    training_epochs = Column(Integer)
    training_batch_size = Column(Integer)
    training_loss = Column(Float)
    validation_loss = Column(Float)

    # 性能指標
    model_size = Column(Integer)  # 模型文件大小（字節）
    inference_speed = Column(Float)  # 推理速度（秒/樣本）
    memory_usage = Column(Integer)  # 內存使用量（MB）
    accuracy_score = Column(Float)  # 準確率分數
    quality_score = Column(Float)  # 品質分數

    # 模型元數據
    metadata = Column(JSON)
    tags = Column(JSON)  # 標籤列表

    # 使用統計
    usage_count = Column(Integer, default=0)
    total_inference_time = Column(Float, default=0.0)

    # 部署信息
    deployment_config = Column(JSON)
    endpoint_url = Column(String(500))
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # 創建和更新時間
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "model_id": self.model_id,
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type.value if self.model_type else None,
            "status": self.status.value if self.status else None,
            "version": self.version,
            "model_path": self.model_path,
            "config_path": self.config_path,
            "checkpoint_path": self.checkpoint_path,
            "training_dataset": self.training_dataset,
            "training_duration": self.training_duration,
            "training_epochs": self.training_epochs,
            "training_batch_size": self.training_batch_size,
            "training_loss": self.training_loss,
            "validation_loss": self.validation_loss,
            "model_size": self.model_size,
            "inference_speed": self.inference_speed,
            "memory_usage": self.memory_usage,
            "accuracy_score": self.accuracy_score,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "total_inference_time": self.total_inference_time,
            "deployment_config": self.deployment_config,
            "endpoint_url": self.endpoint_url,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }


class ModelVersion(Base):
    """模型版本表"""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(50), nullable=False, index=True)
    version = Column(String(20), nullable=False)

    # 版本信息
    changelog = Column(Text)
    performance_metrics = Column(JSON)

    # 文件路徑
    model_path = Column(String(500))
    config_path = Column(String(500))

    # 創建信息
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "model_id": self.model_id,
            "version": self.version,
            "changelog": self.changelog,
            "performance_metrics": self.performance_metrics,
            "model_path": self.model_path,
            "config_path": self.config_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


class ModelDeployment(Base):
    """模型部署表"""

    __tablename__ = "model_deployments"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(String(50), unique=True, index=True)
    model_id = Column(String(50), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)

    # 部署信息
    environment = Column(String(20))  # dev, staging, production
    endpoint_url = Column(String(500))
    status = Column(String(20))  # deploying, running, stopped, failed

    # 資源配置
    cpu_limit = Column(Float)
    memory_limit = Column(Integer)  # MB
    gpu_enabled = Column(Boolean, default=False)

    # 部署配置
    replicas = Column(Integer, default=1)
    auto_scale = Column(Boolean, default=False)
    health_check_path = Column(String(200))

    # 創建和更新時間
    deployed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deployed_by = Column(String(100))

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "deployment_id": self.deployment_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "environment": self.environment,
            "endpoint_url": self.endpoint_url,
            "status": self.status,
            "cpu_limit": self.cpu_limit,
            "memory_limit": self.memory_limit,
            "gpu_enabled": self.gpu_enabled,
            "replicas": self.replicas,
            "auto_scale": self.auto_scale,
            "health_check_path": self.health_check_path,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deployed_by": self.deployed_by,
        }
