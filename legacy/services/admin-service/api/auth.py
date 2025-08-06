"""
認證與授權 API 端點

提供用戶認證、授權、用戶管理和會話管理的 RESTful API。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from ..auth import (
    auth_manager,
    init_auth_system,
    jwt_handler,
    password_manager,
    permission_manager,
    role_manager,
    session_manager,
)
from ..auth.middleware import (
    get_current_user,
    require_permission,
    require_superuser,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# 確保認證系統已初始化
init_auth_system()


# Pydantic 模型
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=200)
    role: str = Field("user", max_length=50)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirmRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None


class AssignRoleRequest(BaseModel):
    user_id: str
    role_id: str


class CreatePermissionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    resource_type: str
    permission_type: str
    description: Optional[str] = Field(None, max_length=500)


# 認證端點
@router.post("/login")
async def login(request: LoginRequest, http_request: Request):
    """用戶登入"""
    try:
        # 獲取客戶端信息
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")

        # 執行認證
        status, result = auth_manager.authenticate_user(
            username=request.username,
            password=request.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if status.value == "success":
            return {"status": "success", "message": "登入成功", "data": result}
        else:
            raise HTTPException(
                status_code=401 if status.value == "failed" else 403,
                detail=result.get("message", "認證失敗"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登入失敗: {e}")
        raise HTTPException(status_code=500, detail="登入過程中發生錯誤")


@router.post("/logout")
async def logout(
    revoke_all_sessions: bool = Body(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """用戶登出"""
    try:
        # 從 JWT payload 獲取會話信息
        payload = current_user.get("payload", {})
        session_id = payload.get("session_id")  # 如果 JWT 中包含會話ID

        if not session_id:
            # 如果沒有會話ID，撤銷用戶所有令牌
            jwt_handler.revoke_user_tokens(current_user["id"])
            session_manager.revoke_user_sessions(current_user["id"])
        else:
            success = auth_manager.logout_user(session_id, revoke_all_sessions)
            if not success:
                raise HTTPException(status_code=400, detail="登出失敗")

        return {"status": "success", "message": "登出成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登出失敗: {e}")
        raise HTTPException(status_code=500, detail="登出過程中發生錯誤")


@router.post("/register")
async def register(
    request: RegisterRequest,
    current_user: Dict[str, Any] = Depends(require_permission("user:create")),
):
    """用戶註冊"""
    try:
        success, result = auth_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role,
        )

        if success:
            return {"status": "success", "message": "用戶創建成功", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "用戶創建失敗"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用戶註冊失敗: {e}")
        raise HTTPException(status_code=500, detail="註冊過程中發生錯誤")


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """刷新訪問令牌"""
    try:
        result = auth_manager.refresh_token(request.refresh_token)

        if result:
            return {"status": "success", "message": "令牌刷新成功", "data": result}
        else:
            raise HTTPException(status_code=401, detail="刷新令牌無效或已過期")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌失敗: {e}")
        raise HTTPException(status_code=500, detail="刷新令牌過程中發生錯誤")


# 密碼管理端點
@router.put("/change-password")
async def change_password(
    request: ChangePasswordRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更改密碼"""
    try:
        success, result = auth_manager.change_password(
            user_id=current_user["id"],
            old_password=request.old_password,
            new_password=request.new_password,
        )

        if success:
            return {"status": "success", "message": result.get("message", "密碼更改成功")}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "密碼更改失敗"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更改密碼失敗: {e}")
        raise HTTPException(status_code=500, detail="更改密碼過程中發生錯誤")


@router.post("/reset-password")
async def reset_password_request(request: ResetPasswordRequest):
    """請求密碼重置"""
    try:
        success, result = auth_manager.reset_password_request(request.email)

        # 無論是否成功都返回相同消息，避免信息洩露
        return {"status": "success", "message": "如果郵箱存在，重置鏈接已發送"}

    except Exception as e:
        logger.error(f"密碼重置請求失敗: {e}")
        raise HTTPException(status_code=500, detail="密碼重置請求過程中發生錯誤")


@router.post("/reset-password/confirm")
async def reset_password_confirm(request: ResetPasswordConfirmRequest):
    """確認密碼重置"""
    try:
        success, result = auth_manager.reset_password(
            reset_token=request.reset_token, new_password=request.new_password
        )

        if success:
            return {"status": "success", "message": result.get("message", "密碼重置成功")}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "密碼重置失敗"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密碼重置確認失敗: {e}")
        raise HTTPException(status_code=500, detail="密碼重置確認過程中發生錯誤")


@router.get("/password-policy")
async def get_password_policy():
    """獲取密碼策略"""
    try:
        policy = password_manager.get_password_policy()
        requirements = password_manager.get_password_requirements()

        return {
            "status": "success",
            "data": {"policy": policy.to_dict(), "requirements": requirements},
        }

    except Exception as e:
        logger.error(f"獲取密碼策略失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取密碼策略失敗")


@router.post("/check-password-strength")
async def check_password_strength(
    password: str = Body(..., embed=True), username: Optional[str] = Body(None, embed=True)
):
    """檢查密碼強度"""
    try:
        strength = password_manager.check_password_strength(password, username)

        return {"status": "success", "data": strength}

    except Exception as e:
        logger.error(f"檢查密碼強度失敗: {e}")
        raise HTTPException(status_code=500, detail="檢查密碼強度失敗")


# 用戶信息端點
@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """獲取當前用戶信息"""
    try:
        user_id = current_user["id"]

        # 獲取用戶角色和權限
        user_roles = role_manager.get_user_roles(user_id)
        user_permissions = role_manager.get_user_permissions(user_id)

        # 獲取用戶會話
        user_sessions = session_manager.get_user_sessions(user_id)

        return {
            "status": "success",
            "data": {
                "user": {
                    "id": user_id,
                    "username": current_user["username"],
                    "role": current_user["role"],
                    "permissions": list(user_permissions),
                },
                "roles": [role.to_dict() for role in user_roles],
                "active_sessions": len(user_sessions),
                "permissions_matrix": permission_manager.get_permission_matrix(user_id),
            },
        }

    except Exception as e:
        logger.error(f"獲取用戶信息失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取用戶信息失敗")


@router.get("/sessions")
async def get_user_sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """獲取用戶會話"""
    try:
        sessions = session_manager.get_user_sessions(current_user["id"])

        return {
            "status": "success",
            "data": {
                "sessions": [session.to_dict() for session in sessions],
                "count": len(sessions),
            },
        }

    except Exception as e:
        logger.error(f"獲取用戶會話失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取用戶會話失敗")


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """撤銷特定會話"""
    try:
        # 驗證會話屬於當前用戶
        session = session_manager.get_session(session_id)
        if not session or session.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="會話不存在")

        success = session_manager.revoke_session(session_id)

        if success:
            return {"status": "success", "message": "會話已撤銷"}
        else:
            raise HTTPException(status_code=400, detail="撤銷會話失敗")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"撤銷會話失敗: {e}")
        raise HTTPException(status_code=500, detail="撤銷會話失敗")


# 角色管理端點
@router.post("/roles")
async def create_role(
    request: CreateRoleRequest,
    current_user: Dict[str, Any] = Depends(require_permission("user:manage")),
):
    """創建角色"""
    try:
        role = role_manager.create_role(
            name=request.name, description=request.description, permissions=request.permissions
        )

        return {"status": "success", "message": "角色創建成功", "data": role.to_dict()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"創建角色失敗: {e}")
        raise HTTPException(status_code=500, detail="創建角色失敗")


@router.get("/roles")
async def list_roles(
    include_system: bool = Query(True),
    current_user: Dict[str, Any] = Depends(require_permission("user:read")),
):
    """列出所有角色"""
    try:
        roles = role_manager.list_roles(include_system=include_system)

        return {
            "status": "success",
            "data": {"roles": [role.to_dict() for role in roles], "count": len(roles)},
        }

    except Exception as e:
        logger.error(f"列出角色失敗: {e}")
        raise HTTPException(status_code=500, detail="列出角色失敗")


@router.get("/roles/{role_id}")
async def get_role(
    role_id: str, current_user: Dict[str, Any] = Depends(require_permission("user:read"))
):
    """獲取角色詳情"""
    try:
        role = role_manager.get_role(role_id)

        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")

        return {"status": "success", "data": role.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取角色失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取角色失敗")


@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    request: UpdateRoleRequest,
    current_user: Dict[str, Any] = Depends(require_permission("user:manage")),
):
    """更新角色"""
    try:
        success = role_manager.update_role(
            role_id=role_id,
            name=request.name,
            description=request.description,
            permissions=request.permissions,
        )

        if success:
            role = role_manager.get_role(role_id)
            return {
                "status": "success",
                "message": "角色更新成功",
                "data": role.to_dict() if role else None,
            }
        else:
            raise HTTPException(status_code=404, detail="角色不存在或無法更新")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新角色失敗: {e}")
        raise HTTPException(status_code=500, detail="更新角色失敗")


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str, current_user: Dict[str, Any] = Depends(require_permission("user:manage"))
):
    """刪除角色"""
    try:
        success = role_manager.delete_role(role_id)

        if success:
            return {"status": "success", "message": "角色刪除成功"}
        else:
            raise HTTPException(status_code=404, detail="角色不存在或無法刪除")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除角色失敗: {e}")
        raise HTTPException(status_code=500, detail="刪除角色失敗")


@router.post("/users/assign-role")
async def assign_role_to_user(
    request: AssignRoleRequest,
    current_user: Dict[str, Any] = Depends(require_permission("user:manage")),
):
    """為用戶分配角色"""
    try:
        success = role_manager.assign_role_to_user(user_id=request.user_id, role_id=request.role_id)

        if success:
            return {"status": "success", "message": "角色分配成功"}
        else:
            raise HTTPException(status_code=400, detail="角色分配失敗")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配角色失敗: {e}")
        raise HTTPException(status_code=500, detail="分配角色失敗")


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("user:manage")),
):
    """移除用戶角色"""
    try:
        success = role_manager.remove_role_from_user(user_id, role_id)

        if success:
            return {"status": "success", "message": "角色移除成功"}
        else:
            raise HTTPException(status_code=404, detail="用戶或角色不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除角色失敗: {e}")
        raise HTTPException(status_code=500, detail="移除角色失敗")


# 權限管理端點
@router.get("/permissions")
async def list_permissions(current_user: Dict[str, Any] = Depends(require_permission("user:read"))):
    """列出所有權限"""
    try:
        permissions = role_manager.list_permissions()

        return {
            "status": "success",
            "data": {
                "permissions": [perm.to_dict() for perm in permissions],
                "count": len(permissions),
            },
        }

    except Exception as e:
        logger.error(f"列出權限失敗: {e}")
        raise HTTPException(status_code=500, detail="列出權限失敗")


@router.post("/permissions")
async def create_permission(
    request: CreatePermissionRequest, current_user: Dict[str, Any] = Depends(require_superuser())
):
    """創建權限"""
    try:
        permission = role_manager.create_permission(
            name=request.name,
            resource_type=request.resource_type,
            permission_type=request.permission_type,
            description=request.description,
        )

        return {"status": "success", "message": "權限創建成功", "data": permission.to_dict()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"創建權限失敗: {e}")
        raise HTTPException(status_code=500, detail="創建權限失敗")


# 系統管理端點
@router.get("/stats")
async def get_auth_stats(current_user: Dict[str, Any] = Depends(require_permission("system:read"))):
    """獲取認證系統統計"""
    try:
        auth_stats = auth_manager.get_auth_stats()
        session_stats = session_manager.get_stats()
        role_stats = role_manager.get_stats()
        jwt_stats = jwt_handler.get_stats()
        password_stats = password_manager.get_stats()
        permission_stats = permission_manager.get_stats()

        return {
            "status": "success",
            "data": {
                "auth": auth_stats,
                "sessions": session_stats,
                "roles": role_stats,
                "jwt": jwt_stats,
                "passwords": password_stats,
                "permissions": permission_stats,
            },
        }

    except Exception as e:
        logger.error(f"獲取認證統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取認證統計失敗")


@router.get("/active-users")
async def get_active_users(current_user: Dict[str, Any] = Depends(require_permission("user:read"))):
    """獲取活躍用戶"""
    try:
        active_users = session_manager.get_active_users()

        return {
            "status": "success",
            "data": {"active_users": active_users, "count": len(active_users)},
        }

    except Exception as e:
        logger.error(f"獲取活躍用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取活躍用戶失敗")


@router.get("/security-alerts")
async def get_security_alerts(
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(require_permission("security:read")),
):
    """獲取安全警報"""
    try:
        alerts = session_manager.get_security_alerts(severity=severity, limit=limit)

        return {
            "status": "success",
            "data": {"alerts": [alert.to_dict() for alert in alerts], "count": len(alerts)},
        }

    except Exception as e:
        logger.error(f"獲取安全警報失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取安全警報失敗")


@router.post("/security-alerts/{alert_id}/resolve")
async def resolve_security_alert(
    alert_id: str, current_user: Dict[str, Any] = Depends(require_permission("security:manage"))
):
    """解決安全警報"""
    try:
        success = session_manager.resolve_security_alert(alert_id)

        if success:
            return {"status": "success", "message": "安全警報已解決"}
        else:
            raise HTTPException(status_code=404, detail="安全警報不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解決安全警報失敗: {e}")
        raise HTTPException(status_code=500, detail="解決安全警報失敗")


@router.post("/cleanup")
async def cleanup_auth_system(current_user: Dict[str, Any] = Depends(require_superuser())):
    """清理認證系統"""
    try:
        # 清理過期會話
        session_manager.cleanup_expired_sessions()

        # 清理過期令牌
        jwt_handler.cleanup_expired_tokens()
        auth_manager.cleanup_expired_tokens()

        # 清理孤立角色
        role_manager.cleanup_orphaned_roles()

        return {"status": "success", "message": "認證系統清理完成"}

    except Exception as e:
        logger.error(f"清理認證系統失敗: {e}")
        raise HTTPException(status_code=500, detail="清理認證系統失敗")


@router.get("/health")
async def auth_health_check():
    """認證系統健康檢查"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "auth_manager": {"status": "healthy"},
                "jwt_handler": {"status": "healthy"},
                "password_manager": {"status": "healthy"},
                "role_manager": {"status": "healthy"},
                "session_manager": {"status": "healthy"},
                "permission_manager": {"status": "healthy"},
            },
        }

        return health_status

    except Exception as e:
        logger.error(f"認證系統健康檢查失敗: {e}")
        return {"status": "unhealthy", "timestamp": datetime.utcnow().isoformat(), "error": str(e)}
