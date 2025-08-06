import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from typing import Any, Dict, List


from ..celery_app import TaskRetryMixin, celery_app
from ..database import SessionLocal
from ..logging_system import log_analyzer

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=celery_app.Task)
class NotificationTask(TaskRetryMixin):
    """通知任務基類"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗處理"""
        logger.error(f"通知任務 {task_id} 失敗: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """任務成功處理"""
        logger.info(f"通知任務 {task_id} 成功完成")


class EmailNotifier:
    """郵件通知器"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")

    def send_email(
        self, to_emails: List[str], subject: str, html_content: str, text_content: str = None
    ):
        """發送郵件"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("郵件配置不完整，跳過發送")
                return False

            msg = MimeMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to_emails)

            # 添加文本版本
            if text_content:
                text_part = MimeText(text_content, "plain", "utf-8")
                msg.attach(text_part)

            # 添加 HTML 版本
            html_part = MimeText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # 發送郵件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"郵件發送成功: {subject}")
            return True

        except Exception as e:
            logger.error(f"發送郵件失敗: {e}")
            return False


# 全域郵件通知器
email_notifier = EmailNotifier()


@celery_app.task(bind=True, base=NotificationTask)
def daily_error_report(self):
    """每日錯誤報告"""
    try:
        # 獲取過去24小時的錯誤統計
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def get_error_data():
            return await log_analyzer.get_error_statistics(hours=24)

        error_stats = loop.run_until_complete(get_error_data())
        loop.close()

        # 生成報告內容
        report_date = datetime.utcnow().strftime("%Y-%m-%d")

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .error-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .error-table th, .error-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .error-table th {{ background-color: #f2f2f2; }}
                .warning {{ color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px; }}
                .critical {{ color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 每日錯誤報告 - {report_date}</h2>
                <p>過去24小時系統錯誤統計報告</p>
            </div>
            
            <div class="summary">
                <h3>📊 錯誤統計摘要</h3>
                <ul>
                    <li><strong>總錯誤數:</strong> {error_stats['total_errors']}</li>
                    <li><strong>統計時段:</strong> 過去 {error_stats['timeframe_hours']} 小時</li>
                </ul>
            </div>
        """

        if error_stats["total_errors"] > 0:
            html_content += """
            <div class="warning">
                <h3>⚠️ 錯誤類型分布</h3>
                <table class="error-table">
                    <tr>
                        <th>錯誤類型</th>
                        <th>次數</th>
                    </tr>
            """

            for error_type in error_stats["error_types"]:
                html_content += f"""
                    <tr>
                        <td>{error_type['type']}</td>
                        <td>{error_type['count']}</td>
                    </tr>
                """

            html_content += "</table></div>"

            html_content += """
            <div class="warning">
                <h3>🔧 資源錯誤分布</h3>
                <table class="error-table">
                    <tr>
                        <th>資源類型</th>
                        <th>錯誤次數</th>
                    </tr>
            """

            for resource_error in error_stats["resource_errors"]:
                html_content += f"""
                    <tr>
                        <td>{resource_error['resource']}</td>
                        <td>{resource_error['count']}</td>
                    </tr>
                """

            html_content += "</table></div>"
        else:
            html_content += """
            <div style="color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px;">
                <h3>✅ 系統運行正常</h3>
                <p>過去24小時內沒有記錄到錯誤。</p>
            </div>
            """

        html_content += (
            """
            <div style="margin-top: 30px; font-size: 12px; color: #666;">
                <p>此報告由後台管理系統自動生成</p>
                <p>生成時間: """
            + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            + """</p>
            </div>
        </body>
        </html>
        """
        )

        # 發送郵件
        subject = f"【系統通知】每日錯誤報告 - {report_date}"
        if error_stats["total_errors"] > 10:
            subject = f"【緊急】" + subject

        success = email_notifier.send_email(
            to_emails=email_notifier.admin_emails, subject=subject, html_content=html_content
        )

        return {
            "success": success,
            "report_date": report_date,
            "total_errors": error_stats["total_errors"],
            "email_sent": success,
        }

    except Exception as e:
        logger.error(f"生成每日錯誤報告失敗: {e}")
        raise


@celery_app.task(bind=True, base=NotificationTask)
def weekly_stats_report(self):
    """週統計報告"""
    try:
        from sqlalchemy import func

        from ..models import (
            AIProvider,
            CrawlerConfig,
            SystemLog,
            TrendingKeyword,
        )

        db = SessionLocal()

        try:
            # 過去7天的統計
            week_ago = datetime.utcnow() - timedelta(days=7)

            # 系統活動統計
            total_logs = db.query(SystemLog).filter(SystemLog.created_at >= week_ago).count()

            error_logs = (
                db.query(SystemLog)
                .filter(
                    SystemLog.created_at >= week_ago, SystemLog.level.in_(["error", "critical"])
                )
                .count()
            )

            # 爬蟲統計
            crawler_runs = (
                db.query(SystemLog)
                .filter(SystemLog.created_at >= week_ago, SystemLog.action == "crawler_executed")
                .count()
            )

            # 趨勢數據統計
            trends_collected = (
                db.query(TrendingKeyword).filter(TrendingKeyword.trend_date >= week_ago).count()
            )

            # 按平台統計趨勢
            platform_trends = (
                db.query(TrendingKeyword.platform, func.count(TrendingKeyword.id).label("count"))
                .filter(TrendingKeyword.trend_date >= week_ago)
                .group_by(TrendingKeyword.platform)
                .all()
            )

            # 系統配置統計
            total_ai_providers = db.query(AIProvider).count()
            active_ai_providers = db.query(AIProvider).filter(AIProvider.is_active == True).count()

            total_crawlers = db.query(CrawlerConfig).count()
            active_crawlers = (
                db.query(CrawlerConfig).filter(CrawlerConfig.status == "active").count()
            )

        finally:
            db.close()

        # 生成報告
        report_date = datetime.utcnow().strftime("%Y年第%W週")

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #e3f2fd; padding: 20px; border-radius: 5px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📈 週統計報告 - {report_date}</h2>
                <p>過去7天系統運行統計報告</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>系統活動</h4>
                    <div class="stat-number">{total_logs:,}</div>
                    <p>總日誌記錄</p>
                </div>
                
                <div class="stat-card">
                    <h4>錯誤記錄</h4>
                    <div class="stat-number" style="color: {'#dc3545' if error_logs > 0 else '#28a745'}">{error_logs}</div>
                    <p>錯誤/警告日誌</p>
                </div>
                
                <div class="stat-card">
                    <h4>爬蟲執行</h4>
                    <div class="stat-number">{crawler_runs}</div>
                    <p>爬蟲任務執行</p>
                </div>
                
                <div class="stat-card">
                    <h4>趨勢收集</h4>
                    <div class="stat-number">{trends_collected:,}</div>
                    <p>熱門關鍵字收集</p>
                </div>
            </div>
            
            <h3>🌟 平台趨勢統計</h3>
            <table class="table">
                <tr>
                    <th>平台</th>
                    <th>收集數量</th>
                </tr>
        """

        for platform_stat in platform_trends:
            html_content += f"""
                <tr>
                    <td>{platform_stat.platform}</td>
                    <td>{platform_stat.count:,}</td>
                </tr>
            """

        html_content += f"""
            </table>
            
            <h3>⚙️ 系統配置</h3>
            <table class="table">
                <tr>
                    <th>配置類型</th>
                    <th>總數</th>
                    <th>啟用數</th>
                    <th>啟用率</th>
                </tr>
                <tr>
                    <td>AI Providers</td>
                    <td>{total_ai_providers}</td>
                    <td>{active_ai_providers}</td>
                    <td>{(active_ai_providers/total_ai_providers*100) if total_ai_providers > 0 else 0:.1f}%</td>
                </tr>
                <tr>
                    <td>爬蟲配置</td>
                    <td>{total_crawlers}</td>
                    <td>{active_crawlers}</td>
                    <td>{(active_crawlers/total_crawlers*100) if total_crawlers > 0 else 0:.1f}%</td>
                </tr>
            </table>
            
            <div style="margin-top: 30px; font-size: 12px; color: #666;">
                <p>此報告由後台管理系統自動生成</p>
                <p>生成時間: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            </div>
        </body>
        </html>
        """

        # 發送郵件
        subject = f"【週報】系統統計報告 - {report_date}"

        success = email_notifier.send_email(
            to_emails=email_notifier.admin_emails, subject=subject, html_content=html_content
        )

        return {
            "success": success,
            "report_date": report_date,
            "stats": {
                "total_logs": total_logs,
                "error_logs": error_logs,
                "crawler_runs": crawler_runs,
                "trends_collected": trends_collected,
            },
            "email_sent": success,
        }

    except Exception as e:
        logger.error(f"生成週統計報告失敗: {e}")
        raise


@celery_app.task(bind=True, base=NotificationTask)
def send_alert_notification(
    self, alert_type: str, message: str, severity: str = "warning", details: Dict[str, Any] = None
):
    """發送警報通知"""
    try:
        severity_colors = {
            "info": "#17a2b8",
            "warning": "#ffc107",
            "error": "#dc3545",
            "critical": "#6f42c1",
        }

        severity_icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}

        color = severity_colors.get(severity, "#6c757d")
        icon = severity_icons.get(severity, "📢")

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; border-left: 4px solid {color}; }}
                .alert-header {{ font-size: 18px; font-weight: bold; color: {color}; margin-bottom: 10px; }}
                .details {{ background-color: #ffffff; padding: 15px; border-radius: 5px; margin-top: 15px; }}
                .timestamp {{ font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <div class="alert-header">{icon} 系統警報 - {alert_type}</div>
                <div class="alert-message">
                    <strong>嚴重程度:</strong> {severity.upper()}<br>
                    <strong>訊息:</strong> {message}
                </div>
                
        """

        if details:
            html_content += """
                <div class="details">
                    <strong>詳細信息:</strong>
                    <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto;">
            """

            for key, value in details.items():
                html_content += f"{key}: {value}\n"

            html_content += "</pre></div>"

        html_content += f"""
                <div class="timestamp">
                    警報時間: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                </div>
            </div>
        </body>
        </html>
        """

        # 根據嚴重程度確定主題前綴
        subject_prefix = {
            "info": "【信息】",
            "warning": "【警告】",
            "error": "【錯誤】",
            "critical": "【緊急】",
        }.get(severity, "【通知】")

        subject = f"{subject_prefix}系統警報 - {alert_type}"

        success = email_notifier.send_email(
            to_emails=email_notifier.admin_emails, subject=subject, html_content=html_content
        )

        return {
            "success": success,
            "alert_type": alert_type,
            "severity": severity,
            "email_sent": success,
        }

    except Exception as e:
        logger.error(f"發送警報通知失敗: {e}")
        raise


@celery_app.task(bind=True, base=NotificationTask)
def send_system_notification(self, title: str, message: str, recipients: List[str] = None):
    """發送系統通知"""
    try:
        if not recipients:
            recipients = email_notifier.admin_emails

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .notification {{ background-color: #e3f2fd; padding: 20px; border-radius: 5px; }}
                .title {{ font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 15px; }}
                .message {{ line-height: 1.6; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="notification">
                <div class="title">📢 {title}</div>
                <div class="message">{message}</div>
                <div class="footer">
                    發送時間: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                </div>
            </div>
        </body>
        </html>
        """

        success = email_notifier.send_email(
            to_emails=recipients, subject=f"【系統通知】{title}", html_content=html_content
        )

        return {
            "success": success,
            "title": title,
            "recipients_count": len(recipients),
            "email_sent": success,
        }

    except Exception as e:
        logger.error(f"發送系統通知失敗: {e}")
        raise


# 手動觸發通知任務的工具函數
def send_alert(
    alert_type: str, message: str, severity: str = "warning", details: Dict[str, Any] = None
):
    """發送警報"""
    return send_alert_notification.delay(alert_type, message, severity, details)


def send_notification(title: str, message: str, recipients: List[str] = None):
    """發送通知"""
    return send_system_notification.delay(title, message, recipients)


def schedule_daily_report():
    """排程每日報告"""
    return daily_error_report.delay()


def schedule_weekly_report():
    """排程週報告"""
    return weekly_stats_report.delay()
