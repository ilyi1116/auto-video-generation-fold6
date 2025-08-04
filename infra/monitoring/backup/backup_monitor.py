#!/usr/bin/env python3
"""
備份監控模組
監控備份任務的執行狀態和結果
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class BackupMonitor:
    """備份監控器"""

    def __init__(self, log_dir: str = "/var/log/backups"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def log_backup_start(
        self, backup_id: str, backup_type: str, source: str
    ) -> None:
        """記錄備份開始"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "backup_started",
            "backup_id": backup_id,
            "backup_type": backup_type,
            "source": source,
        }
        self._write_log(log_entry)

    def log_backup_complete(
        self,
        backup_id: str,
        success: bool,
        size_bytes: int = 0,
        message: str = "",
    ) -> None:
        """記錄備份完成"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "backup_completed",
            "backup_id": backup_id,
            "success": success,
            "size_bytes": size_bytes,
            "message": message,
        }
        self._write_log(log_entry)

    def log_restore_start(
        self, restore_id: str, backup_id: str, target: str
    ) -> None:
        """記錄恢復開始"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "restore_started",
            "restore_id": restore_id,
            "backup_id": backup_id,
            "target": target,
        }
        self._write_log(log_entry)

    def log_restore_complete(
        self, restore_id: str, success: bool, message: str = ""
    ) -> None:
        """記錄恢復完成"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "restore_completed",
            "restore_id": restore_id,
            "success": success,
            "message": message,
        }
        self._write_log(log_entry)

    def _write_log(self, log_entry: Dict) -> None:
        """寫入日誌"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"backup_{today}.log"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def get_recent_backups(self, days: int = 7) -> List[Dict]:
        """獲取最近的備份記錄"""
        records = []
        start_date = datetime.now() - timedelta(days=days)

        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            log_file = self.log_dir / f"backup_{date.strftime('%Y-%m-%d')}.log"

            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            records.append(record)
                        except json.JSONDecodeError:
                            continue

        return sorted(records, key=lambda x: x.get("timestamp", ""))

    def generate_backup_report(self, days: int = 7) -> Dict:
        """生成備份報告"""
        records = self.get_recent_backups(days)

        # 統計資訊
        backup_starts = [
            r for r in records if r.get("event") == "backup_started"
        ]
        backup_completes = [
            r for r in records if r.get("event") == "backup_completed"
        ]
        successful_backups = [
            r for r in backup_completes if r.get("success", False)
        ]
        failed_backups = [
            r for r in backup_completes if not r.get("success", True)
        ]

        restore_starts = [
            r for r in records if r.get("event") == "restore_started"
        ]
        restore_completes = [
            r for r in records if r.get("event") == "restore_completed"
        ]
        successful_restores = [
            r for r in restore_completes if r.get("success", False)
        ]
        failed_restores = [
            r for r in restore_completes if not r.get("success", True)
        ]

        # 計算總備份大小
        total_backup_size = sum(
            r.get("size_bytes", 0) for r in successful_backups
        )

        report = {
            "period": f"最近 {days} 天",
            "generated_at": datetime.now().isoformat(),
            "backup_statistics": {
                "total_started": len(backup_starts),
                "total_completed": len(backup_completes),
                "successful": len(successful_backups),
                "failed": len(failed_backups),
                "success_rate": (
                    (len(successful_backups) / len(backup_completes) * 100)
                    if backup_completes
                    else 0
                ),
                "total_size_bytes": total_backup_size,
                "total_size_mb": round(total_backup_size / (1024 * 1024), 2),
            },
            "restore_statistics": {
                "total_started": len(restore_starts),
                "total_completed": len(restore_completes),
                "successful": len(successful_restores),
                "failed": len(failed_restores),
                "success_rate": (
                    (len(successful_restores) / len(restore_completes) * 100)
                    if restore_completes
                    else 0
                ),
            },
            "recent_failures": failed_backups + failed_restores,
        }

        return report


if __name__ == "__main__":
    # 示例用法
    monitor = BackupMonitor()
    report = monitor.generate_backup_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
