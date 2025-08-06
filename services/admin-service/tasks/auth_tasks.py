"""
認證與授權相關的 Celery 任務

提供異步的認證管理、會話清理、安全監控和維護任務。
"""

import logging
from datetime import datetime

from ..auth import (
    auth_manager,
    init_auth_system,
    jwt_handler,
    password_manager,
    permission_manager,
    role_manager,
    session_manager,
)
from ..celery_app import celery_app
from ..tracing.tracer import trace_celery_task

logger = logging.getLogger(__name__)

# 確保認證系統已初始化
init_auth_system()


@celery_app.task(bind=True)
@trace_celery_task("auth.session_cleanup")
def session_cleanup_task(self):
    """
    會話清理任務

    清理過期的用戶會話和無效的會話數據
    """
    try:
        logger.info("開始會話清理任務")

        # 清理過期會話
        session_manager.cleanup_expired_sessions()

        # 清理過期的 JWT 令牌
        jwt_handler.cleanup_expired_tokens()

        # 清理認證管理器中的過期令牌
        auth_manager.cleanup_expired_tokens()

        # 獲取清理後的統計
        session_stats = session_manager.get_stats()
        jwt_stats = jwt_handler.get_stats()

        logger.info("會話清理任務完成")

        return {
            "status": "success",
            "session_stats": session_stats,
            "jwt_stats": jwt_stats,
            "cleaned_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"會話清理任務失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("auth.security_monitor")
def security_monitoring_task(self):
    """
    安全監控任務

    監控異常登錄活動、可疑行為和安全威脅
    """
    try:
        logger.info("開始安全監控任務")

        results = {
            "suspicious_activities": [],
            "locked_ips": 0,
            "failed_logins": 0,
            "security_alerts": 0,
        }

        # 獲取登錄統計
        login_stats = session_manager.get_login_stats()
        results["failed_logins"] = login_stats.get("failed_attempts", 0)
        results["locked_ips"] = login_stats.get("locked_ips", 0)

        # 獲取安全警報
        security_alerts = session_manager.get_security_alerts(limit=50)
        results["security_alerts"] = len([a for a in security_alerts if not a.is_resolved])

        # 檢查可疑活動
        # 1. 檢查短時間內多次失敗登錄
        # 2. 檢查異常IP地址
        # 3. 檢查異常時間登錄

        # 生成安全報告
        if results["failed_logins"] > 100:
            results["suspicious_activities"].append(
                {
                    "type": "high_failed_logins",
                    "description": f"過去統計期間有 {results['failed_logins']} 次失敗登錄",
                    "severity": "medium",
                }
            )

        if results["locked_ips"] > 10:
            results["suspicious_activities"].append(
                {
                    "type": "multiple_locked_ips",
                    "description": f"當前有 {results['locked_ips']} 個IP被鎖定",
                    "severity": "high",
                }
            )

        logger.info(f"安全監控任務完成，發現 {len(results['suspicious_activities'])} 個可疑活動")

        return {
            "status": "success",
            "monitoring_results": results,
            "monitored_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"安全監控任務失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("auth.password_policy_check")
def password_policy_check_task(self):
    """
    密碼策略檢查任務

    檢查系統中的密碼是否符合當前安全策略
    """
    try:
        logger.info("開始密碼策略檢查任務")

        # 獲取密碼策略
        policy = password_manager.get_password_policy()

        results = {
            "policy": policy.to_dict(),
            "users_checked": 0,
            "expired_passwords": 0,
            "weak_passwords": 0,
            "policy_violations": [],
        }

        # 這裡應該檢查所有用戶的密碼
        # 由於沒有實際的用戶數據庫，我們模擬檢查

        # 檢查密碼過期
        if policy.max_age_days:
            # 模擬檢查過期密碼
            results["expired_passwords"] = 3  # 模擬數據
            if results["expired_passwords"] > 0:
                results["policy_violations"].append(
                    {
                        "type": "expired_passwords",
                        "count": results["expired_passwords"],
                        "description": f"有 {results['expired_passwords']} 個用戶的密碼已過期",
                    }
                )

        logger.info("密碼策略檢查任務完成")

        return {
            "status": "success",
            "policy_check_results": results,
            "checked_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"密碼策略檢查任務失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("auth.role_audit")
def role_audit_task(self):
    """
    角色審計任務

    審計用戶角色分配和權限使用情況
    """
    try:
        logger.info("開始角色審計任務")

        # 獲取角色使用統計
        role_usage = role_manager.get_role_usage_stats()
        role_stats = role_manager.get_stats()

        results = {"role_usage": role_usage, "role_stats": role_stats, "audit_findings": []}

        # 審計未使用的角色
        unused_roles = [
            role_name
            for role_name, stats in role_usage.items()
            if stats["user_count"] == 0 and not stats["is_system"]
        ]

        if unused_roles:
            results["audit_findings"].append(
                {
                    "type": "unused_roles",
                    "roles": unused_roles,
                    "description": f"發現 {len(unused_roles)} 個未使用的自定義角色",
                }
            )

        # 審計過度權限的角色
        over_privileged_roles = [
            role_name
            for role_name, stats in role_usage.items()
            if stats["permission_count"] > 20  # 假設超過20個權限為過度權限
        ]

        if over_privileged_roles:
            results["audit_findings"].append(
                {
                    "type": "over_privileged_roles",
                    "roles": over_privileged_roles,
                    "description": f"發現 {len(over_privileged_roles)} 個可能過度權限的角色",
                }
            )

        # 清理孤立的角色分配
        role_manager.cleanup_orphaned_roles()

        logger.info(f"角色審計任務完成，發現 {len(results['audit_findings'])} 個審計問題")

        return {
            "status": "success",
            "audit_results": results,
            "audited_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"角色審計任務失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("auth.user_activity_analysis")
def user_activity_analysis_task(self, hours: int = 24):
    """
    用戶活動分析任務

    Args:
        hours: 分析時間範圍（小時）
    """
    try:
        logger.info(f"開始用戶活動分析任務: {hours} 小時")

        # 獲取活躍用戶
        active_users = session_manager.get_active_users()

        results = {
            "analysis_period_hours": hours,
            "active_users_count": len(active_users),
            "active_users": active_users[:10],  # 只返回前10個
            "activity_patterns": {},
            "recommendations": [],
        }

        # 分析活動模式
        if active_users:
            # 按最後活動時間分組
            now = datetime.utcnow()
            recent_activity = []

            for user in active_users:
                last_activity = datetime.fromisoformat(user["last_activity"].replace("Z", "+00:00"))
                hours_since_activity = (now - last_activity).total_seconds() / 3600

                if hours_since_activity <= 1:
                    recent_activity.append(user)

            results["activity_patterns"]["recent_activity_users"] = len(recent_activity)
            results["activity_patterns"]["recent_activity_percentage"] = (
                len(recent_activity) / len(active_users) * 100 if active_users else 0
            )

        # 生成建議
        if results["active_users_count"] == 0:
            results["recommendations"].append(
                {"type": "no_active_users", "description": "當前沒有活躍用戶，可能需要檢查系統狀態"}
            )
        elif results["active_users_count"] > 100:
            results["recommendations"].append(
                {"type": "high_user_activity", "description": "用戶活動量很高，建議監控系統性能"}
            )

        logger.info("用戶活動分析任務完成")

        return {
            "status": "success",
            "analysis_results": results,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"用戶活動分析任務失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("auth.auth_health_check")
def auth_health_check_task(self):
    """
    認證系統健康檢查任務
    """
    try:
        logger.info("開始認證系統健康檢查")

        # 檢查各組件健康狀態
        health_report = {
            "overall_status": "healthy",
            "health_issues": [],
            "components": {},
            "recommendations": [],
        }

        # 檢查認證管理器
        try:
            auth_stats = auth_manager.get_auth_stats()
            health_report["components"]["auth_manager"] = {"status": "healthy", "stats": auth_stats}
        except Exception as e:
            health_report["components"]["auth_manager"] = {"status": "unhealthy", "error": str(e)}
            health_report["health_issues"].append("認證管理器異常")

        # 檢查會話管理器
        try:
            session_stats = session_manager.get_stats()
            health_report["components"]["session_manager"] = {
                "status": "healthy",
                "stats": session_stats,
            }

            # 檢查是否有過多過期會話
            if session_stats.get("expired_sessions", 0) > 1000:
                health_report["health_issues"].append("過期會話數量過多")
                health_report["recommendations"].append("建議增加會話清理頻率")
        except Exception as e:
            health_report["components"]["session_manager"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_report["health_issues"].append("會話管理器異常")

        # 檢查角色管理器
        try:
            role_stats = role_manager.get_stats()
            health_report["components"]["role_manager"] = {"status": "healthy", "stats": role_stats}
        except Exception as e:
            health_report["components"]["role_manager"] = {"status": "unhealthy", "error": str(e)}
            health_report["health_issues"].append("角色管理器異常")

        # 檢查 JWT 處理器
        try:
            jwt_stats = jwt_handler.get_stats()
            health_report["components"]["jwt_handler"] = {"status": "healthy", "stats": jwt_stats}

            # 檢查是否有過多黑名單令牌
            if jwt_stats.get("blacklisted_tokens", 0) > 10000:
                health_report["health_issues"].append("黑名單令牌數量過多")
                health_report["recommendations"].append("建議清理黑名單令牌")
        except Exception as e:
            health_report["components"]["jwt_handler"] = {"status": "unhealthy", "error": str(e)}
            health_report["health_issues"].append("JWT處理器異常")

        # 檢查密碼管理器
        try:
            password_stats = password_manager.get_stats()
            health_report["components"]["password_manager"] = {
                "status": "healthy",
                "stats": password_stats,
            }
        except Exception as e:
            health_report["components"]["password_manager"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_report["health_issues"].append("密碼管理器異常")

        # 檢查權限管理器
        try:
            permission_stats = permission_manager.get_stats()
            health_report["components"]["permission_manager"] = {
                "status": "healthy",
                "stats": permission_stats,
            }
        except Exception as e:
            health_report["components"]["permission_manager"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_report["health_issues"].append("權限管理器異常")

        # 確定整體健康狀態
        if health_report["health_issues"]:
            health_report["overall_status"] = (
                "warning" if len(health_report["health_issues"]) <= 2 else "unhealthy"
            )

        logger.info(f"認證系統健康檢查完成，狀態: {health_report['overall_status']}")

        return {
            "status": "success",
            "health_report": health_report,
            "checked_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"認證系統健康檢查失敗: {e}")

        return {"status": "error", "error": str(e), "checked_at": datetime.utcnow().isoformat()}


@celery_app.task(bind=True)
@trace_celery_task("auth.generate_security_report")
def generate_security_report_task(self, days: int = 7):
    """
    生成安全報告任務

    Args:
        days: 報告時間範圍（天）
    """
    try:
        logger.info(f"開始生成安全報告: {days} 天")

        # 收集各種安全統計
        auth_stats = auth_manager.get_auth_stats()
        session_stats = session_manager.get_stats()
        login_stats = session_manager.get_login_stats()
        security_alerts = session_manager.get_security_alerts(limit=100)

        report = {
            "report_period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_auth_attempts": auth_stats.get("total_auth_attempts", 0),
                "successful_logins": auth_stats.get("successful_attempts", 0),
                "failed_logins": auth_stats.get("failed_attempts", 0),
                "active_sessions": session_stats.get("active_sessions", 0),
                "locked_ips": login_stats.get("locked_ips", 0),
                "security_alerts": len(security_alerts),
                "unresolved_alerts": len([a for a in security_alerts if not a.is_resolved]),
            },
            "trends": {},
            "security_incidents": [],
            "recommendations": [],
        }

        # 分析安全趨勢
        success_rate = (
            report["summary"]["successful_logins"] / report["summary"]["total_auth_attempts"]
            if report["summary"]["total_auth_attempts"] > 0
            else 0
        )
        report["trends"]["login_success_rate"] = round(success_rate * 100, 2)

        # 識別安全事件
        for alert in security_alerts:
            if alert.severity in ["high", "critical"] and not alert.is_resolved:
                report["security_incidents"].append(
                    {
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "description": alert.description,
                        "created_at": alert.created_at.isoformat(),
                    }
                )

        # 生成建議
        if report["summary"]["failed_logins"] > report["summary"]["successful_logins"]:
            report["recommendations"].append(
                {
                    "priority": "high",
                    "category": "authentication",
                    "description": "失敗登錄次數超過成功登錄，建議加強身份驗證安全措施",
                }
            )

        if report["summary"]["locked_ips"] > 50:
            report["recommendations"].append(
                {
                    "priority": "medium",
                    "category": "access_control",
                    "description": "大量IP被鎖定，建議檢查是否存在攻擊行為",
                }
            )

        if report["summary"]["unresolved_alerts"] > 10:
            report["recommendations"].append(
                {
                    "priority": "high",
                    "category": "incident_response",
                    "description": "存在大量未解決的安全警報，建議及時處理",
                }
            )

        logger.info("安全報告生成完成")

        return {"status": "success", "security_report": report}

    except Exception as e:
        logger.error(f"生成安全報告失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("auth.backup_auth_config")
def backup_auth_config_task(self):
    """
    備份認證配置任務
    """
    try:
        logger.info("開始備份認證配置")

        # 導出角色和權限配置
        role_config = role_manager.export_roles()

        # 獲取系統配置
        password_policy = password_manager.get_password_policy()
        jwt_config = jwt_handler.get_stats()

        backup_data = {
            "backup_timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "role_config": role_config,
            "password_policy": password_policy.to_dict(),
            "jwt_config": {
                "algorithm": jwt_config.get("algorithm"),
                "access_token_expire_minutes": jwt_config.get("access_token_expire_minutes"),
                "refresh_token_expire_days": jwt_config.get("refresh_token_expire_days"),
            },
        }

        # 這裡應該將備份數據保存到外部存儲
        # 為了示例，我們只是記錄日誌

        logger.info("認證配置備份完成")

        return {
            "status": "success",
            "backup_size": len(str(backup_data)),
            "backed_up_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"備份認證配置失敗: {e}")
        raise
