"""
配置管理 API 端點
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from ..config.config_manager import config_manager, ConfigScope, ConfigFormat
from ..security import require_permission, audit_log
from ..models import AdminUser
from ..schemas import APIResponse

router = APIRouter(prefix="/config", tags=["config"])


class ConfigCreateRequest(BaseModel):
    """創建配置請求模型"""
    name: str
    config: Dict[str, Any]
    scope: str = "global"
    format: str = "json"
    encrypt: bool = False
    description: str = ""


class ConfigUpdateRequest(BaseModel):
    """更新配置請求模型"""
    config: Dict[str, Any]
    description: str = ""


class ConfigValueRequest(BaseModel):
    """配置值請求模型"""
    key_path: str
    value: Any


@router.get("/")
@require_permission("system:dashboard")
async def get_all_configs(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取所有配置"""
    try:
        configs = config_manager.get_all_configs()
        metadata = config_manager.get_all_metadata()
        
        result = {}
        for name, config_data in configs.items():
            meta = metadata.get(name)
            result[name] = {
                "config": config_data,
                "metadata": {
                    "scope": meta.scope.value if meta else "unknown",
                    "format": meta.format.value if meta else "json",
                    "version": meta.version if meta else "1.0.0",
                    "last_modified": meta.last_modified.isoformat() if meta and meta.last_modified else None,
                    "encrypted": meta.encrypted if meta else False,
                    "description": meta.description if meta else ""
                }
            }
        
        return APIResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_name}")
@require_permission("system:dashboard")
async def get_config(
    config_name: str,
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取特定配置"""
    try:
        config = await config_manager.get_config(config_name)
        if config is None:
            raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
        
        metadata = config_manager.get_config_metadata(config_name)
        
        return APIResponse(
            data={
                "config": config,
                "metadata": {
                    "scope": metadata.scope.value if metadata else "unknown",
                    "format": metadata.format.value if metadata else "json",
                    "version": metadata.version if metadata else "1.0.0",
                    "last_modified": metadata.last_modified.isoformat() if metadata and metadata.last_modified else None,
                    "encrypted": metadata.encrypted if metadata else False,
                    "description": metadata.description if metadata else ""
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
@require_permission("system:settings")
@audit_log("create_config", "config")
async def create_config(
    request: ConfigCreateRequest,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """創建新配置"""
    try:
        # 驗證作用域和格式
        try:
            scope = ConfigScope(request.scope)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的配置作用域: {request.scope}")
        
        try:
            format = ConfigFormat(request.format)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的配置格式: {request.format}")
        
        # 檢查配置是否已存在
        existing_config = await config_manager.get_config(request.name)
        if existing_config is not None:
            raise HTTPException(status_code=409, detail=f"配置 {request.name} 已存在")
        
        # 創建配置
        success = await config_manager.set_config(
            name=request.name,
            config=request.config,
            scope=scope,
            format=format,
            encrypt=request.encrypt,
            changed_by=current_user.username
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="創建配置失敗")
        
        return APIResponse(
            message=f"配置 {request.name} 創建成功",
            data={"name": request.name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{config_name}")
@require_permission("system:settings")
@audit_log("update_config", "config")
async def update_config(
    config_name: str,
    request: ConfigUpdateRequest,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """更新配置"""
    try:
        # 檢查配置是否存在
        existing_config = await config_manager.get_config(config_name)
        if existing_config is None:
            raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
        
        # 獲取現有元數據
        metadata = config_manager.get_config_metadata(config_name)
        
        # 更新配置
        success = await config_manager.set_config(
            name=config_name,
            config=request.config,
            scope=metadata.scope if metadata else ConfigScope.GLOBAL,
            format=metadata.format if metadata else ConfigFormat.JSON,
            encrypt=metadata.encrypted if metadata else False,
            changed_by=current_user.username
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="更新配置失敗")
        
        return APIResponse(
            message=f"配置 {config_name} 更新成功",
            data={"name": config_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{config_name}")
@require_permission("system:settings")
@audit_log("delete_config", "config")
async def delete_config(
    config_name: str,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """刪除配置"""
    try:
        success = await config_manager.delete_config(
            name=config_name,
            changed_by=current_user.username
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
        
        return APIResponse(
            message=f"配置 {config_name} 刪除成功",
            data={"name": config_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_name}/value")
@require_permission("system:dashboard")
async def get_config_value(
    config_name: str,
    key_path: str,
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取配置中的特定值"""
    try:
        value = await config_manager.get_config_value(config_name, key_path)
        if value is None:
            raise HTTPException(
                status_code=404, 
                detail=f"配置 {config_name} 中不存在鍵路徑 {key_path}"
            )
        
        return APIResponse(
            data={
                "config_name": config_name,
                "key_path": key_path,
                "value": value
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_name}/reload")
@require_permission("system:settings")
@audit_log("reload_config", "config")
async def reload_config(
    config_name: str,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """重新載入配置"""
    try:
        success = await config_manager.reload_config(config_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在或重載失敗")
        
        return APIResponse(
            message=f"配置 {config_name} 重載成功",
            data={"name": config_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_name}/history")
@require_permission("system:dashboard")
async def get_config_history(
    config_name: str,
    limit: int = 50,
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取配置變更歷史"""
    try:
        history = config_manager.get_change_history(config_name, limit)
        
        result = []
        for change in history:
            result.append({
                "config_name": change.config_name,
                "change_type": change.change_type,
                "changed_by": change.changed_by,
                "timestamp": change.timestamp.isoformat(),
                "old_value": change.old_value,
                "new_value": change.new_value
            })
        
        return APIResponse(
            data={
                "config_name": config_name,
                "history": result,
                "total_changes": len(result)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/all")
@require_permission("system:dashboard")
async def get_all_config_history(
    limit: int = 100,
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取所有配置變更歷史"""
    try:
        history = config_manager.get_change_history(None, limit)
        
        result = []
        for change in history:
            result.append({
                "config_name": change.config_name,
                "change_type": change.change_type,
                "changed_by": change.changed_by,
                "timestamp": change.timestamp.isoformat(),
                "has_changes": change.old_value != change.new_value
            })
        
        return APIResponse(
            data={
                "history": result,
                "total_changes": len(result)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_name}/validate")
@require_permission("system:dashboard")
async def validate_config(
    config_name: str,
    schema: Dict[str, Any],
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """驗證配置"""
    try:
        errors = await config_manager.validate_config(config_name, schema)
        
        return APIResponse(
            data={
                "config_name": config_name,
                "valid": len(errors) == 0,
                "errors": errors
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata/summary")
@require_permission("system:dashboard")
async def get_config_summary(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取配置摘要統計"""
    try:
        metadata = config_manager.get_all_metadata()
        
        # 統計各種類型的配置
        scope_counts = {}
        format_counts = {}
        encrypted_count = 0
        
        for meta in metadata.values():
            # 統計作用域
            scope = meta.scope.value
            scope_counts[scope] = scope_counts.get(scope, 0) + 1
            
            # 統計格式
            format = meta.format.value
            format_counts[format] = format_counts.get(format, 0) + 1
            
            # 統計加密配置
            if meta.encrypted:
                encrypted_count += 1
        
        return APIResponse(
            data={
                "total_configs": len(metadata),
                "scope_distribution": scope_counts,
                "format_distribution": format_counts,
                "encrypted_configs": encrypted_count,
                "scopes_available": [scope.value for scope in ConfigScope],
                "formats_available": [format.value for format in ConfigFormat]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))