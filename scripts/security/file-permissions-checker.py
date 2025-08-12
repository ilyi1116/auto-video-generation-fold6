#!/usr/bin/env python3
"""
檔案權限安全檢查器
檢查敏感檔案的權限設定是否符合安全要求
"""

import json
import os
import stat
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class FilePermissionChecker:
    """檔案權限檢查器"""

    # 敏感檔案和其要求的權限
    SENSITIVE_FILES = {
        # 配置檔案 - 僅擁有者可讀寫 (600)
        "config/environments/production.env": 0o600,
        "config/environments/staging.env": 0o600,
        "config/environments/development.env": 0o644,  # 開發環境可以較寬鬆
        # 密鑰檔案 - 僅擁有者可讀寫 (600)
        "config/keys/.env.production": 0o600,
        "config/keys/.env.staging": 0o600,
        "config/keys/.env.development": 0o600,
        # SSL 證書 - 僅擁有者可讀 (400)
        "config/ssl/private.key": 0o400,
        "config/ssl/certificate.crt": 0o644,
        # 資料庫備份 - 僅擁有者可讀寫 (600)
        "data/backups/": 0o700,  # 目錄
        # 日誌檔案 - 擁有者可讀寫，群組可讀 (640)
        "logs/": 0o750,  # 目錄
        "logs/security.log": 0o640,
        "logs/application.log": 0o640,
        "logs/errors.log": 0o640,
        # 腳本檔案 - 擁有者可執行 (755)
        "scripts/": 0o755,  # 目錄
        "scripts/security/": 0o755,  # 目錄
        # Docker 相關檔案
        "docker-compose.yml": 0o644,
        "docker-compose.prod.yml": 0o600,
        ".dockerignore": 0o644,
        # Git 相關 (安全考量)
        ".gitignore": 0o644,
        ".env.example": 0o644,
    }

    # 密鑰檔案模式
    KEY_FILE_PATTERNS = [
        "keyset_*.json",
        "*.pem",
        "*.key",
        "*_key",
        "*_secret*",
    ]

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.issues: List[Dict] = []

    def check_all_permissions(self) -> Dict[str, any]:
        """檢查所有敏感檔案的權限"""
        self.issues = []

        print("🔒 檢查檔案權限安全性...")
        print(f"專案根目錄: {self.project_root}")
        print("-" * 50)

        # 檢查預定義的敏感檔案
        for file_path, expected_mode in self.SENSITIVE_FILES.items():
            self._check_file_permission(file_path, expected_mode)

        # 檢查密鑰檔案模式
        self._check_key_files()

        # 檢查目錄權限
        self._check_directory_permissions()

        # 檢查環境檔案
        self._check_env_files()

        return self._generate_report()

    def _check_file_permission(self, file_path: str, expected_mode: int):
        """檢查單個檔案權限"""
        full_path = self.project_root / file_path

        if not full_path.exists():
            # 如果是必要的敏感檔案，記錄缺失
            if "production" in file_path or "staging" in file_path:
                self.issues.append(
                    {
                        "type": "missing_file",
                        "path": str(full_path),
                        "severity": "high",
                        "message": f"敏感檔案不存在: {file_path}",
                    }
                )
            return

        try:
            current_mode = stat.S_IMODE(full_path.stat().st_mode)

            if current_mode != expected_mode:
                severity = self._determine_severity(file_path, current_mode, expected_mode)
                self.issues.append(
                    {
                        "type": "permission_mismatch",
                        "path": str(full_path),
                        "current_mode": oct(current_mode),
                        "expected_mode": oct(expected_mode),
                        "severity": severity,
                        "message": f"權限不正確: {file_path} (當前: {oct(current_mode)}, 期望: {oct(expected_mode)})",
                    }
                )
                print(f"❌ {file_path}: {oct(current_mode)} -> 應為 {oct(expected_mode)}")
            else:
                print(f"✅ {file_path}: {oct(current_mode)}")

        except PermissionError:
            self.issues.append(
                {
                    "type": "access_denied",
                    "path": str(full_path),
                    "severity": "medium",
                    "message": f"無法讀取檔案權限: {file_path}",
                }
            )

    def _check_key_files(self):
        """檢查密鑰檔案"""
        print("\n🔑 檢查密鑰檔案...")

        # 檢查 config/keys 目錄下的所有檔案
        keys_dir = self.project_root / "config" / "keys"
        if keys_dir.exists():
            for key_file in keys_dir.rglob("*"):
                if key_file.is_file():
                    current_mode = stat.S_IMODE(key_file.stat().st_mode)
                    expected_mode = 0o600

                    if current_mode != expected_mode:
                        self.issues.append(
                            {
                                "type": "key_file_permission",
                                "path": str(key_file),
                                "current_mode": oct(current_mode),
                                "expected_mode": oct(expected_mode),
                                "severity": "critical",
                                "message": f"密鑰檔案權限不安全: {key_file.relative_to(self.project_root)}",
                            }
                        )
                        print(
                            f"❌ {key_file.relative_to(self.project_root)}: {oct(current_mode)} -> 應為 {oct(expected_mode)}"
                        )
                    else:
                        print(f"✅ {key_file.relative_to(self.project_root)}: {oct(current_mode)}")

    def _check_directory_permissions(self):
        """檢查目錄權限"""
        print("\n📁 檢查目錄權限...")

        important_dirs = [
            ("config", 0o755),
            ("config/keys", 0o700),
            ("config/environments", 0o755),
            ("logs", 0o750),
            ("data", 0o755),
            ("scripts/security", 0o755),
        ]

        for dir_path, expected_mode in important_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                current_mode = stat.S_IMODE(full_path.stat().st_mode)

                if current_mode != expected_mode:
                    self.issues.append(
                        {
                            "type": "directory_permission",
                            "path": str(full_path),
                            "current_mode": oct(current_mode),
                            "expected_mode": oct(expected_mode),
                            "severity": "medium",
                            "message": f"目錄權限不正確: {dir_path}",
                        }
                    )
                    print(f"❌ {dir_path}/: {oct(current_mode)} -> 應為 {oct(expected_mode)}")
                else:
                    print(f"✅ {dir_path}/: {oct(current_mode)}")

    def _check_env_files(self):
        """檢查所有 .env 檔案"""
        print("\n🌍 檢查環境檔案...")

        env_files = list(self.project_root.rglob(".env*"))
        env_files.extend(list(self.project_root.rglob("*.env")))

        for env_file in env_files:
            if env_file.is_file() and not env_file.name.endswith(".example"):
                current_mode = stat.S_IMODE(env_file.stat().st_mode)
                expected_mode = 0o600

                if current_mode != expected_mode:
                    self.issues.append(
                        {
                            "type": "env_file_permission",
                            "path": str(env_file),
                            "current_mode": oct(current_mode),
                            "expected_mode": oct(expected_mode),
                            "severity": "high",
                            "message": f"環境檔案權限不安全: {env_file.relative_to(self.project_root)}",
                        }
                    )
                    print(
                        f"❌ {env_file.relative_to(self.project_root)}: {oct(current_mode)} -> 應為 {oct(expected_mode)}"
                    )
                else:
                    print(f"✅ {env_file.relative_to(self.project_root)}: {oct(current_mode)}")

    def _determine_severity(self, file_path: str, current_mode: int, expected_mode: int) -> str:
        """判斷權限問題的嚴重程度"""
        # 檢查是否過於寬鬆
        if current_mode > expected_mode:
            if "production" in file_path or "key" in file_path.lower():
                return "critical"
            elif "config" in file_path:
                return "high"
            else:
                return "medium"
        else:
            # 權限過於嚴格通常不是安全問題
            return "low"

    def _generate_report(self) -> Dict[str, any]:
        """生成檢查報告"""
        print("\n" + "=" * 50)
        print("📊 檔案權限檢查報告")
        print("=" * 50)

        # 統計問題數量
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in self.issues:
            severity_counts[issue["severity"]] += 1

        print(f"總問題數: {len(self.issues)}")
        print(f"嚴重: {severity_counts['critical']}")
        print(f"高: {severity_counts['high']}")
        print(f"中: {severity_counts['medium']}")
        print(f"低: {severity_counts['low']}")

        if self.issues:
            print("\n⚠️  發現的問題:")
            for issue in sorted(
                self.issues,
                key=lambda x: ["critical", "high", "medium", "low"].index(x["severity"]),
            ):
                icon = {"critical": "🚨", "high": "⚠️", "medium": "🔸", "low": "💡"}[
                    issue["severity"]
                ]
                print(f"{icon} [{issue['severity'].upper()}] {issue['message']}")

        else:
            print("\n✅ 所有檔案權限設定正確！")

        return {
            "total_issues": len(self.issues),
            "severity_counts": severity_counts,
            "issues": self.issues,
            "status": "pass" if len(self.issues) == 0 else "fail",
        }

    def fix_permissions(self, dry_run: bool = True) -> List[str]:
        """修復檔案權限問題"""
        commands = []

        print(f"\n🔧 {'模擬' if dry_run else '執行'}權限修復...")

        for issue in self.issues:
            if issue["type"] in [
                "permission_mismatch",
                "key_file_permission",
                "env_file_permission",
                "directory_permission",
            ]:
                path = issue["path"]
                expected_mode = issue["expected_mode"]

                if isinstance(expected_mode, str):
                    expected_mode = int(expected_mode, 8)

                command = f"chmod {oct(expected_mode)[2:]} {path}"
                commands.append(command)

                if dry_run:
                    print(f"📝 {command}")
                else:
                    try:
                        os.chmod(path, expected_mode)
                        print(f"✅ {command}")
                    except Exception as e:
                        print(f"❌ 修復失敗 {path}: {e}")

        return commands


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="檔案權限安全檢查器")
    parser.add_argument("--fix", action="store_true", help="自動修復權限問題")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="僅顯示修復命令，不實際執行"
    )
    parser.add_argument("--output", help="輸出報告到 JSON 檔案")

    args = parser.parse_args()

    checker = FilePermissionChecker()
    report = checker.check_all_permissions()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 報告已儲存到: {args.output}")

    if args.fix and report["total_issues"] > 0:
        checker.fix_permissions(dry_run=args.dry_run)

    # 返回適當的退出碼
    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
