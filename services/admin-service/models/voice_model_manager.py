"""
語音模型管理器
提供模型的創建、訓練、部署、監控和優化功能
"""

import os
import json
import logging
import asyncio
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import aiofiles
import psutil

from .voice_model import VoiceModel, ModelVersion, ModelDeployment, ModelStatus, ModelType
from ..database import get_db
from ..utils.file_manager import FileManager

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformanceMetrics:
    """模型性能指標"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    inference_time: float  # 平均推理時間
    memory_usage: int      # 內存使用量 (MB)
    model_size: int        # 模型大小 (bytes)
    quality_score: float   # 整體品質分數


@dataclass
class TrainingConfig:
    """訓練配置"""
    dataset_path: str
    epochs: int
    batch_size: int
    learning_rate: float
    optimizer: str
    loss_function: str
    validation_split: float
    early_stopping: bool
    checkpoint_interval: int


@dataclass
class DeploymentConfig:
    """部署配置"""
    environment: str
    cpu_limit: float
    memory_limit: int
    gpu_enabled: bool
    replicas: int
    auto_scale: bool
    health_check_path: str


class VoiceModelManager:
    """語音模型管理器"""
    
    def __init__(self, base_path: str = "/data/data/com.termux/files/home/myProject/models"):
        """
        初始化模型管理器
        
        Args:
            base_path: 模型存儲根目錄
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 子目錄結構
        self.models_dir = self.base_path / "models"
        self.checkpoints_dir = self.base_path / "checkpoints"
        self.configs_dir = self.base_path / "configs"
        self.logs_dir = self.base_path / "logs"
        
        # 創建目錄結構
        for dir_path in [self.models_dir, self.checkpoints_dir, self.configs_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.file_manager = FileManager()
        
    async def create_model(self, model_data: Dict[str, Any], created_by: str) -> str:
        """
        創建新模型
        
        Args:
            model_data: 模型數據
            created_by: 創建者
            
        Returns:
            模型ID
        """
        try:
            # 生成唯一模型ID
            model_id = self._generate_model_id(model_data["name"])
            
            # 創建模型記錄
            async with get_db() as db:
                new_model = VoiceModel(
                    model_id=model_id,
                    name=model_data["name"],
                    description=model_data.get("description", ""),
                    model_type=ModelType(model_data["model_type"]),
                    status=ModelStatus.TRAINING,
                    version="1.0.0",
                    tags=model_data.get("tags", []),
                    metadata=model_data.get("metadata", {}),
                    created_by=created_by
                )
                
                db.add(new_model)
                await db.commit()
            
            # 創建模型目錄結構
            model_dir = self.models_dir / model_id
            model_dir.mkdir(exist_ok=True)
            
            (model_dir / "versions").mkdir(exist_ok=True)
            (model_dir / "configs").mkdir(exist_ok=True)
            (model_dir / "logs").mkdir(exist_ok=True)
            
            logger.info(f"模型 {model_id} 創建成功")
            return model_id
            
        except Exception as e:
            logger.error(f"創建模型失敗: {e}")
            raise
    
    async def start_training(self, model_id: str, training_config: TrainingConfig, 
                           created_by: str) -> bool:
        """
        開始模型訓練
        
        Args:
            model_id: 模型ID
            training_config: 訓練配置
            created_by: 訓練發起者
            
        Returns:
            是否成功開始訓練
        """
        try:
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                
                if not model:
                    raise ValueError(f"模型 {model_id} 不存在")
                
                # 更新模型狀態
                model.status = ModelStatus.TRAINING
                model.training_dataset = training_config.dataset_path
                model.training_epochs = training_config.epochs
                model.training_batch_size = training_config.batch_size
                model.updated_at = datetime.utcnow()
                
                await db.commit()
            
            # 保存訓練配置
            config_path = self.configs_dir / f"{model_id}_training.json"
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(json.dumps({
                    "dataset_path": training_config.dataset_path,
                    "epochs": training_config.epochs,
                    "batch_size": training_config.batch_size,
                    "learning_rate": training_config.learning_rate,
                    "optimizer": training_config.optimizer,
                    "loss_function": training_config.loss_function,
                    "validation_split": training_config.validation_split,
                    "early_stopping": training_config.early_stopping,
                    "checkpoint_interval": training_config.checkpoint_interval,
                    "created_by": created_by,
                    "created_at": datetime.utcnow().isoformat()
                }, indent=2))
            
            # 這裡應該啟動實際的訓練任務
            # 在實際實現中，這會是一個 Celery 任務或其他異步任務
            logger.info(f"模型 {model_id} 開始訓練")
            return True
            
        except Exception as e:
            logger.error(f"開始訓練失敗: {e}")
            return False
    
    async def update_training_progress(self, model_id: str, epoch: int, 
                                     training_loss: float, validation_loss: float):
        """
        更新訓練進度
        
        Args:
            model_id: 模型ID
            epoch: 當前輪次
            training_loss: 訓練損失
            validation_loss: 驗證損失
        """
        try:
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                
                if model:
                    model.training_loss = training_loss
                    model.validation_loss = validation_loss
                    model.updated_at = datetime.utcnow()
                    
                    # 更新元數據
                    if not model.metadata:
                        model.metadata = {}
                    model.metadata["current_epoch"] = epoch
                    model.metadata["last_updated"] = datetime.utcnow().isoformat()
                    
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"更新訓練進度失敗: {e}")
    
    async def complete_training(self, model_id: str, model_path: str, 
                              metrics: ModelPerformanceMetrics) -> bool:
        """
        完成模型訓練
        
        Args:
            model_id: 模型ID
            model_path: 模型文件路徑
            metrics: 性能指標
            
        Returns:
            是否成功完成
        """
        try:
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                
                if not model:
                    raise ValueError(f"模型 {model_id} 不存在")
                
                # 更新模型狀態和指標
                model.status = ModelStatus.TRAINED
                model.model_path = model_path
                model.model_size = metrics.model_size
                model.inference_speed = metrics.inference_time
                model.memory_usage = metrics.memory_usage
                model.accuracy_score = metrics.accuracy
                model.quality_score = metrics.quality_score
                model.updated_at = datetime.utcnow()
                
                await db.commit()
            
            # 創建版本記錄
            await self._create_version_record(model_id, "1.0.0", model_path, metrics)
            
            logger.info(f"模型 {model_id} 訓練完成")
            return True
            
        except Exception as e:
            logger.error(f"完成訓練失敗: {e}")
            return False
    
    async def deploy_model(self, model_id: str, version: str, 
                          deploy_config: DeploymentConfig, deployed_by: str) -> str:
        """
        部署模型
        
        Args:
            model_id: 模型ID
            version: 模型版本
            deploy_config: 部署配置
            deployed_by: 部署者
            
        Returns:
            部署ID
        """
        try:
            # 檢查模型是否存在且可部署
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id,
                    VoiceModel.status.in_([ModelStatus.TRAINED, ModelStatus.READY])
                ).first()
                
                if not model:
                    raise ValueError(f"模型 {model_id} 不存在或未準備好部署")
            
            # 生成部署ID
            deployment_id = self._generate_deployment_id(model_id, deploy_config.environment)
            
            # 創建部署記錄
            async with get_db() as db:
                deployment = ModelDeployment(
                    deployment_id=deployment_id,
                    model_id=model_id,
                    model_version=version,
                    environment=deploy_config.environment,
                    endpoint_url=f"/api/v1/models/{model_id}/predict",
                    status="deploying",
                    cpu_limit=deploy_config.cpu_limit,
                    memory_limit=deploy_config.memory_limit,
                    gpu_enabled=deploy_config.gpu_enabled,
                    replicas=deploy_config.replicas,
                    auto_scale=deploy_config.auto_scale,
                    health_check_path=deploy_config.health_check_path,
                    deployed_by=deployed_by
                )
                
                db.add(deployment)
                await db.commit()
            
            # 這裡應該執行實際的部署邏輯
            # 例如：創建 Docker 容器、更新負載均衡器等
            
            # 模擬部署成功
            await asyncio.sleep(1)
            
            # 更新部署狀態
            async with get_db() as db:
                deployment = await db.query(ModelDeployment).filter(
                    ModelDeployment.deployment_id == deployment_id
                ).first()
                deployment.status = "running"
                await db.commit()
            
            # 更新模型狀態
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                model.status = ModelStatus.DEPLOYED
                model.endpoint_url = f"/api/v1/models/{model_id}/predict"
                await db.commit()
            
            logger.info(f"模型 {model_id} 部署成功，部署ID: {deployment_id}")
            return deployment_id
            
        except Exception as e:
            logger.error(f"模型部署失敗: {e}")
            raise
    
    async def get_model_list(self, model_type: Optional[str] = None, 
                           status: Optional[str] = None, 
                           limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        獲取模型列表
        
        Args:
            model_type: 模型類型過濾
            status: 狀態過濾
            limit: 限制數量
            offset: 偏移量
            
        Returns:
            模型列表
        """
        try:
            async with get_db() as db:
                query = db.query(VoiceModel)
                
                if model_type:
                    query = query.filter(VoiceModel.model_type == ModelType(model_type))
                
                if status:
                    query = query.filter(VoiceModel.status == ModelStatus(status))
                
                models = await query.order_by(VoiceModel.created_at.desc()).offset(offset).limit(limit).all()
                
                return [model.to_dict() for model in models]
                
        except Exception as e:
            logger.error(f"獲取模型列表失敗: {e}")
            return []
    
    async def get_model_details(self, model_id: str) -> Optional[Dict]:
        """
        獲取模型詳細信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型詳細信息
        """
        try:
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                
                if not model:
                    return None
                
                # 獲取版本信息
                versions = await db.query(ModelVersion).filter(
                    ModelVersion.model_id == model_id
                ).order_by(ModelVersion.created_at.desc()).all()
                
                # 獲取部署信息
                deployments = await db.query(ModelDeployment).filter(
                    ModelDeployment.model_id == model_id
                ).order_by(ModelDeployment.deployed_at.desc()).all()
                
                result = model.to_dict()
                result["versions"] = [version.to_dict() for version in versions]
                result["deployments"] = [deployment.to_dict() for deployment in deployments]
                
                return result
                
        except Exception as e:
            logger.error(f"獲取模型詳情失敗: {e}")
            return None
    
    async def delete_model(self, model_id: str, deleted_by: str) -> bool:
        """
        刪除模型
        
        Args:
            model_id: 模型ID
            deleted_by: 刪除者
            
        Returns:
            是否成功刪除
        """
        try:
            async with get_db() as db:
                # 檢查模型是否存在
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                
                if not model:
                    return False
                
                # 檢查是否有活躍部署
                active_deployments = await db.query(ModelDeployment).filter(
                    ModelDeployment.model_id == model_id,
                    ModelDeployment.status == "running"
                ).count()
                
                if active_deployments > 0:
                    raise ValueError("無法刪除有活躍部署的模型")
                
                # 刪除相關記錄
                await db.query(ModelVersion).filter(ModelVersion.model_id == model_id).delete()
                await db.query(ModelDeployment).filter(ModelDeployment.model_id == model_id).delete()
                await db.delete(model)
                await db.commit()
            
            # 刪除模型文件
            model_dir = self.models_dir / model_id
            if model_dir.exists():
                shutil.rmtree(model_dir)
            
            logger.info(f"模型 {model_id} 已被 {deleted_by} 刪除")
            return True
            
        except Exception as e:
            logger.error(f"刪除模型失敗: {e}")
            return False
    
    async def get_model_metrics(self, model_id: str, days: int = 7) -> Dict[str, Any]:
        """
        獲取模型使用指標
        
        Args:
            model_id: 模型ID
            days: 統計天數
            
        Returns:
            使用指標
        """
        try:
            async with get_db() as db:
                model = await db.query(VoiceModel).filter(
                    VoiceModel.model_id == model_id
                ).first()
                
                if not model:
                    return {}
                
                # 這裡應該從日誌或監控系統獲取實際使用數據
                # 現在返回模擬數據
                return {
                    "model_id": model_id,
                    "total_requests": model.usage_count,
                    "total_inference_time": model.total_inference_time,
                    "average_response_time": model.inference_speed,
                    "memory_usage": model.memory_usage,
                    "accuracy_score": model.accuracy_score,
                    "quality_score": model.quality_score,
                    "uptime_percentage": 99.5,
                    "error_rate": 0.1,
                    "period_days": days
                }
                
        except Exception as e:
            logger.error(f"獲取模型指標失敗: {e}")
            return {}
    
    async def optimize_model(self, model_id: str) -> Dict[str, Any]:
        """
        模型優化建議
        
        Args:
            model_id: 模型ID
            
        Returns:
            優化建議
        """
        try:
            model_details = await self.get_model_details(model_id)
            if not model_details:
                return {"error": "模型不存在"}
            
            suggestions = []
            
            # 分析模型大小
            if model_details.get("model_size", 0) > 100 * 1024 * 1024:  # 100MB
                suggestions.append({
                    "type": "size_optimization",
                    "message": "模型文件較大，建議進行量化或剪枝優化",
                    "priority": "medium"
                })
            
            # 分析推理速度
            if model_details.get("inference_speed", 0) > 2.0:  # 2秒
                suggestions.append({
                    "type": "speed_optimization",
                    "message": "推理速度較慢，建議優化模型結構或使用 GPU 加速",
                    "priority": "high"
                })
            
            # 分析內存使用
            if model_details.get("memory_usage", 0) > 1024:  # 1GB
                suggestions.append({
                    "type": "memory_optimization",
                    "message": "內存使用量較高，建議進行內存優化",
                    "priority": "medium"
                })
            
            # 分析準確率
            if model_details.get("accuracy_score", 0) < 0.8:
                suggestions.append({
                    "type": "accuracy_improvement",
                    "message": "模型準確率較低，建議增加訓練數據或調整模型架構",
                    "priority": "high"
                })
            
            return {
                "model_id": model_id,
                "optimization_suggestions": suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成優化建議失敗: {e}")
            return {"error": str(e)}
    
    def _generate_model_id(self, name: str) -> str:
        """生成唯一模型ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"model_{timestamp}_{name_hash}"
    
    def _generate_deployment_id(self, model_id: str, environment: str) -> str:
        """生成部署ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"deploy_{model_id}_{environment}_{timestamp}"
    
    async def _create_version_record(self, model_id: str, version: str, 
                                   model_path: str, metrics: ModelPerformanceMetrics):
        """創建版本記錄"""
        try:
            async with get_db() as db:
                version_record = ModelVersion(
                    model_id=model_id,
                    version=version,
                    model_path=model_path,
                    performance_metrics={
                        "accuracy": metrics.accuracy,
                        "precision": metrics.precision,
                        "recall": metrics.recall,
                        "f1_score": metrics.f1_score,
                        "inference_time": metrics.inference_time,
                        "memory_usage": metrics.memory_usage,
                        "model_size": metrics.model_size,
                        "quality_score": metrics.quality_score
                    },
                    created_by="system"
                )
                
                db.add(version_record)
                await db.commit()
                
        except Exception as e:
            logger.error(f"創建版本記錄失敗: {e}")


# 全局模型管理器實例
model_manager = VoiceModelManager()