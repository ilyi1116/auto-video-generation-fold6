"""
語音模型管理 API 端點
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..models import AdminUser
from ..models.voice_model import ModelStatus, ModelType
from ..models.voice_model_manager import (
    DeploymentConfig,
    ModelPerformanceMetrics,
    TrainingConfig,
    model_manager,
)
from ..schemas import APIResponse
from ..security import audit_log, require_permission

router = APIRouter(prefix="/voice-models", tags=["voice-models"])


class ModelCreateRequest(BaseModel):
    """創建模型請求"""

    name: str
    description: str = ""
    model_type: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class TrainingRequest(BaseModel):
    """訓練請求"""

    dataset_path: str
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss_function: str = "mse"
    validation_split: float = 0.2
    early_stopping: bool = True
    checkpoint_interval: int = 10


class DeploymentRequest(BaseModel):
    """部署請求"""

    version: str
    environment: str
    cpu_limit: float = 2.0
    memory_limit: int = 2048
    gpu_enabled: bool = False
    replicas: int = 1
    auto_scale: bool = False
    health_check_path: str = "/health"


class MetricsUpdateRequest(BaseModel):
    """指標更新請求"""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    inference_time: float
    memory_usage: int
    model_size: int
    quality_score: float


@router.get("/")
@require_permission("system:dashboard")
async def get_models(
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: AdminUser = Depends(require_permission("system:dashboard")),
):
    """獲取模型列表"""
    try:
        models = await model_manager.get_model_list(
            model_type=model_type, status=status, limit=limit, offset=offset
        )

        return APIResponse(
            data={"models": models, "total": len(models), "limit": limit, "offset": offset}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}")
@require_permission("system:dashboard")
async def get_model_details(
    model_id: str, current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取模型詳細信息"""
    try:
        model_details = await model_manager.get_model_details(model_id)

        if not model_details:
            raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")

        return APIResponse(data=model_details)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
@require_permission("system:models")
@audit_log("create_model", "voice_model")
async def create_model(
    request: ModelCreateRequest,
    current_user: AdminUser = Depends(require_permission("system:models")),
):
    """創建新模型"""
    try:
        # 驗證模型類型
        try:
            ModelType(request.model_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的模型類型: {request.model_type}")

        model_id = await model_manager.create_model(
            model_data={
                "name": request.name,
                "description": request.description,
                "model_type": request.model_type,
                "tags": request.tags,
                "metadata": request.metadata,
            },
            created_by=current_user.username,
        )

        return APIResponse(message=f"模型 {request.name} 創建成功", data={"model_id": model_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/train")
@require_permission("system:models")
@audit_log("start_training", "voice_model")
async def start_training(
    model_id: str,
    request: TrainingRequest,
    current_user: AdminUser = Depends(require_permission("system:models")),
):
    """開始模型訓練"""
    try:
        training_config = TrainingConfig(
            dataset_path=request.dataset_path,
            epochs=request.epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            optimizer=request.optimizer,
            loss_function=request.loss_function,
            validation_split=request.validation_split,
            early_stopping=request.early_stopping,
            checkpoint_interval=request.checkpoint_interval,
        )

        success = await model_manager.start_training(
            model_id=model_id, training_config=training_config, created_by=current_user.username
        )

        if not success:
            raise HTTPException(status_code=400, detail="無法開始訓練")

        return APIResponse(
            message=f"模型 {model_id} 開始訓練", data={"model_id": model_id, "status": "training"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{model_id}/training/progress")
@require_permission("system:models")
async def update_training_progress(
    model_id: str,
    epoch: int,
    training_loss: float,
    validation_loss: float,
    current_user: AdminUser = Depends(require_permission("system:models")),
):
    """更新訓練進度"""
    try:
        await model_manager.update_training_progress(
            model_id=model_id,
            epoch=epoch,
            training_loss=training_loss,
            validation_loss=validation_loss,
        )

        return APIResponse(
            message="訓練進度已更新",
            data={
                "model_id": model_id,
                "epoch": epoch,
                "training_loss": training_loss,
                "validation_loss": validation_loss,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/training/complete")
@require_permission("system:models")
@audit_log("complete_training", "voice_model")
async def complete_training(
    model_id: str,
    model_path: str,
    metrics: MetricsUpdateRequest,
    current_user: AdminUser = Depends(require_permission("system:models")),
):
    """完成模型訓練"""
    try:
        performance_metrics = ModelPerformanceMetrics(
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
            inference_time=metrics.inference_time,
            memory_usage=metrics.memory_usage,
            model_size=metrics.model_size,
            quality_score=metrics.quality_score,
        )

        success = await model_manager.complete_training(
            model_id=model_id, model_path=model_path, metrics=performance_metrics
        )

        if not success:
            raise HTTPException(status_code=400, detail="無法完成訓練")

        return APIResponse(
            message=f"模型 {model_id} 訓練完成",
            data={"model_id": model_id, "status": "trained", "metrics": metrics.dict()},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/deploy")
@require_permission("system:deployment")
@audit_log("deploy_model", "voice_model")
async def deploy_model(
    model_id: str,
    request: DeploymentRequest,
    current_user: AdminUser = Depends(require_permission("system:deployment")),
):
    """部署模型"""
    try:
        deploy_config = DeploymentConfig(
            environment=request.environment,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit,
            gpu_enabled=request.gpu_enabled,
            replicas=request.replicas,
            auto_scale=request.auto_scale,
            health_check_path=request.health_check_path,
        )

        deployment_id = await model_manager.deploy_model(
            model_id=model_id,
            version=request.version,
            deploy_config=deploy_config,
            deployed_by=current_user.username,
        )

        return APIResponse(
            message=f"模型 {model_id} 部署成功",
            data={
                "model_id": model_id,
                "deployment_id": deployment_id,
                "environment": request.environment,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}")
@require_permission("system:models")
@audit_log("delete_model", "voice_model")
async def delete_model(
    model_id: str, current_user: AdminUser = Depends(require_permission("system:models"))
):
    """刪除模型"""
    try:
        success = await model_manager.delete_model(
            model_id=model_id, deleted_by=current_user.username
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")

        return APIResponse(message=f"模型 {model_id} 已刪除", data={"model_id": model_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/metrics")
@require_permission("system:dashboard")
async def get_model_metrics(
    model_id: str,
    days: int = 7,
    current_user: AdminUser = Depends(require_permission("system:dashboard")),
):
    """獲取模型使用指標"""
    try:
        metrics = await model_manager.get_model_metrics(model_id, days)

        if not metrics:
            raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")

        return APIResponse(data=metrics)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/optimization")
@require_permission("system:dashboard")
async def get_optimization_suggestions(
    model_id: str, current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取模型優化建議"""
    try:
        suggestions = await model_manager.optimize_model(model_id)

        if "error" in suggestions:
            raise HTTPException(status_code=404, detail=suggestions["error"])

        return APIResponse(data=suggestions)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
@require_permission("system:dashboard")
async def get_model_summary(
    current_user: AdminUser = Depends(require_permission("system:dashboard")),
):
    """獲取模型統計摘要"""
    try:
        # 獲取所有模型
        all_models = await model_manager.get_model_list(limit=1000)

        # 統計各種狀態的模型數量
        status_counts = {}
        type_counts = {}

        for model in all_models:
            status = model.get("status", "unknown")
            model_type = model.get("model_type", "unknown")

            status_counts[status] = status_counts.get(status, 0) + 1
            type_counts[model_type] = type_counts.get(model_type, 0) + 1

        # 計算平均指標
        total_models = len(all_models)
        avg_accuracy = sum(model.get("accuracy_score", 0) for model in all_models) / max(
            total_models, 1
        )
        avg_quality = sum(model.get("quality_score", 0) for model in all_models) / max(
            total_models, 1
        )
        avg_inference_time = sum(model.get("inference_speed", 0) for model in all_models) / max(
            total_models, 1
        )

        return APIResponse(
            data={
                "total_models": total_models,
                "status_distribution": status_counts,
                "type_distribution": type_counts,
                "average_metrics": {
                    "accuracy": round(avg_accuracy, 3),
                    "quality": round(avg_quality, 3),
                    "inference_time": round(avg_inference_time, 3),
                },
                "available_types": [t.value for t in ModelType],
                "available_statuses": [s.value for s in ModelStatus],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/upload")
@require_permission("system:models")
@audit_log("upload_model", "voice_model")
async def upload_model_file(
    model_id: str,
    file: UploadFile = File(...),
    file_type: str = Form(...),  # model, config, checkpoint
    current_user: AdminUser = Depends(require_permission("system:models")),
):
    """上傳模型文件"""
    try:
        if file_type not in ["model", "config", "checkpoint"]:
            raise HTTPException(status_code=400, detail="無效的文件類型")

        # 檢查模型是否存在
        model_details = await model_manager.get_model_details(model_id)
        if not model_details:
            raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")

        # 保存文件
        from pathlib import Path

        import aiofiles

        model_dir = Path(f"/data/data/com.termux/files/home/myProject/models/models/{model_id}")
        model_dir.mkdir(parents=True, exist_ok=True)

        file_path = model_dir / f"{file_type}_{file.filename}"

        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        return APIResponse(
            message=f"文件 {file.filename} 上傳成功",
            data={
                "model_id": model_id,
                "file_type": file_type,
                "file_path": str(file_path),
                "file_size": len(content),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
