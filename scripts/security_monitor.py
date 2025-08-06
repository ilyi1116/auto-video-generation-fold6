#!/usr/bin/env python3
"""
安全監控腳本 - 持續監控系統安全狀態
執行定期安全檢查，報告安全問題並生成建議
"""

import datetime
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("security_monitor.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class SecurityMonitor:
    """安全監控器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "critical_issues": [],
            "high_issues": [],
            "medium_issues": [],
            "low_issues": [],
            "recommendations": [],
            "summary": {},
        }

    def run_full_security_scan(self) -> Dict[str, Any]:
        """執行完整安全掃描"""
        logger.info("🔍 開始執行安全掃描...")

        # 1. 依賴安全檢查
        self.check_python_dependencies()
        self.check_npm_dependencies()

        # 2. 容器安全檢查
        self.check_docker_security()

        # 3. 代碼安全檢查
        self.check_code_security()

        # 4. 配置安全檢查
        self.check_security_configurations()

        # 5. 密鑰洩漏檢查
        self.check_secret_leaks()

        # 6. 生成報告
        self.generate_report()

        return self.report

    def check_python_dependencies(self):
        """檢查 Python 依賴安全性"""
        logger.info("🐍 檢查 Python 依賴安全性...")

        # 查找所有 requirements.txt 文件
        req_files = list(self.project_root.rglob("requirements*.txt"))

        for req_file in req_files:
            try:
                result = subprocess.run(
                    ["safety", "check", "-r", str(req_file), "--json"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0 and result.stdout:
                    issues = json.loads(result.stdout)
                    for issue in issues:
                        self.add_issue(
                            (
                                "high"
                                if "critical" in issue.get("advisory", "").lower()
                                else "medium"
                            ),
                            f"Python 依賴漏洞: {issue.get('package')} - {issue.get('advisory')}",
                            f"文件: {req_file}",
                            f"升級到 {issue.get('safe_version', 'latest')}",
                        )

            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                FileNotFoundError,
            ) as e:
                logger.warning(f"無法檢查 {req_file}: {e}")

    def check_npm_dependencies(self):
        """檢查 NPM 依賴安全性"""
        logger.info("📦 檢查 NPM 依賴安全性...")

        package_files = list(self.project_root.rglob("package.json"))

        for package_file in package_files:
            package_dir = package_file.parent
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=package_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.stdout:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = audit_data.get("vulnerabilities", {})

                    for pkg, vuln in vulnerabilities.items():
                        severity = vuln.get("severity", "low")
                        self.add_issue(
                            severity,
                            f"NPM 依賴漏洞: {pkg}",
                            f"文件: {package_file}",
                            "執行 npm audit fix",
                        )

            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                FileNotFoundError,
            ) as e:
                logger.warning(f"無法檢查 {package_file}: {e}")

    def check_docker_security(self):
        """檢查 Docker 安全性"""
        logger.info("🐳 檢查 Docker 安全性...")

        dockerfiles = list(self.project_root.rglob("Dockerfile*"))

        for dockerfile in dockerfiles:
            self.analyze_dockerfile(dockerfile)

    def analyze_dockerfile(self, dockerfile: Path):
        """分析 Dockerfile 安全性"""
        try:
            content = dockerfile.read_text()
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                line = line.strip().upper()

                # 檢查不安全的實踐
                if line.startswith("USER ROOT") or line.startswith("USER 0"):
                    self.add_issue(
                        "high",
                        "Docker 安全風險: 使用 root 用戶",
                        f"{dockerfile}:{i}",
                        "改用非特權用戶",
                    )

                if "ADD HTTP" in line or "ADD HTTPS" in line:
                    self.add_issue(
                        "medium",
                        "Docker 安全風險: 使用 ADD 下載遠程文件",
                        f"{dockerfile}:{i}",
                        "使用 RUN wget/curl 替代",
                    )

                if "--NO-INSTALL-RECOMMENDS" not in line and "APT-GET INSTALL" in line:
                    self.add_issue(
                        "low",
                        "Docker 優化建議: 缺少 --no-install-recommends",
                        f"{dockerfile}:{i}",
                        "添加 --no-install-recommends 標誌",
                    )
        except Exception as e:
            logger.warning(f"無法分析 {dockerfile}: {e}")

    def check_code_security(self):
        """檢查代碼安全性"""
        logger.info("🛡️ 檢查代碼安全性...")

        # 使用 bandit 檢查 Python 代碼
        try:
            result = subprocess.run(
                ["bandit", "-r", ".", "-", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout:
                bandit_data = json.loads(result.stdout)
                results = bandit_data.get("results", [])

                for issue in results:
                    severity_map = {
                        "HIGH": "high",
                        "MEDIUM": "medium",
                        "LOW": "low",
                    }

                    severity = severity_map.get(issue.get("issue_severity", "LOW"), "low")
                    self.add_issue(
                        severity,
                        f"代碼安全問題: {issue.get('test_name')}",
                        f"{issue.get('filename')}:{issue.get('line_number')}",
                        issue.get("issue_text", "請檢查相關代碼"),
                    )

        except (
            subprocess.TimeoutExpired,
            json.JSONDecodeError,
            FileNotFoundError,
        ) as e:
            logger.warning(f"Bandit 檢查失敗: {e}")

    def check_security_configurations(self):
        """檢查安全配置"""
        logger.info("⚙️ 檢查安全配置...")

        # 檢查 JWT 配置
        self.check_jwt_configuration()

        # 檢查 CORS 配置
        self.check_cors_configuration()

        # 檢查環境變量配置
        self.check_env_configuration()

    def check_jwt_configuration(self):
        """檢查 JWT 配置"""
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            try:
                content = py_file.read_text()

                if "JWT_ALGORITHM" in content and '"HS256"' in content:
                    self.add_issue(
                        "medium",
                        "JWT 安全風險: 使用對稱加密算法",
                        str(py_file),
                        "改用 RS256 非對稱加密",
                    )

                if "ACCESS_TOKEN_EXPIRE" in content:
                    # 檢查是否有過長的過期時間
                    if any(word in content for word in ["1440", "24*60", "86400"]):
                        self.add_issue(
                            "low",
                            "JWT 配置建議: Token 過期時間過長",
                            str(py_file),
                            "建議縮短到 15 分鐘",
                        )

            except Exception as e:
                logger.warning(f"無法檢查 {py_file}: {e}")

    def check_cors_configuration(self):
        """檢查 CORS 配置"""
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            try:
                content = py_file.read_text()

                if "allow_origins" in content and '"*"' in content:
                    self.add_issue(
                        "high",
                        "CORS 安全風險: 允許所有來源",
                        str(py_file),
                        "改為明確的域名列表",
                    )

            except Exception as e:
                logger.warning(f"無法檢查 {py_file}: {e}")

    def check_env_configuration(self):
        """檢查環境變量配置"""
        env_files = list(self.project_root.rglob(".env*"))

        for env_file in env_files:
            try:
                content = env_file.read_text()
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    line = line.strip()

                    # 檢查硬編碼密鑰
                    if any(keyword in line.lower() for keyword in ["password=", "secret=", "key="]):
                        if not line.endswith("=${RANDOM}") and "=" in line:
                            value = line.split("=", 1)[1]
                            if value and not value.startswith("$"):
                                self.add_issue(
                                    "critical",
                                    "安全風險: 硬編碼密鑰",
                                    f"{env_file}:{i}",
                                    "使用環境變量或密鑰管理服務",
                                )

            except Exception as e:
                logger.warning(f"無法檢查 {env_file}: {e}")

    def check_secret_leaks(self):
        """檢查密鑰洩漏"""
        logger.info("🔐 檢查密鑰洩漏...")

        # 簡單的密鑰模式檢查
        patterns = [
            (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Key"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
            (r"xox[baprs]-[0-9a-zA-Z\-]{8,}", "Slack Token"),
        ]

        # 排除的目錄
        exclude_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache"}

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not any(exc in str(file_path) for exc in exclude_dirs):
                try:
                    if file_path.suffix in [
                        ".py",
                        ".js",
                        ".yml",
                        ".yaml",
                        ".json",
                        ".env",
                    ]:
                        content = file_path.read_text()

                        for pattern, desc in patterns:
                            import re

                            matches = re.findall(pattern, content)
                            if matches:
                                self.add_issue(
                                    "critical",
                                    f"密鑰洩漏風險: {desc}",
                                    str(file_path),
                                    "立即移除並輪換密鑰",
                                )

                except Exception:
                    continue  # 跳過無法讀取的文件

    def add_issue(self, severity: str, title: str, location: str, recommendation: str):
        """添加安全問題"""
        issue = {
            "title": title,
            "location": location,
            "recommendation": recommendation,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        severity_key = f"{severity}_issues"
        if severity_key in self.report:
            self.report[severity_key].append(issue)

    def generate_report(self):
        """生成安全報告"""
        logger.info("📊 生成安全報告...")

        # 統計摘要
        self.report["summary"] = {
            "total_issues": (
                len(self.report["critical_issues"])
                + len(self.report["high_issues"])
                + len(self.report["medium_issues"])
                + len(self.report["low_issues"])
            ),
            "critical_count": len(self.report["critical_issues"]),
            "high_count": len(self.report["high_issues"]),
            "medium_count": len(self.report["medium_issues"]),
            "low_count": len(self.report["low_issues"]),
        }

        # 安全建議
        if self.report["critical_issues"]:
            self.report["recommendations"].append("🚨 立即處理 Critical 級別的安全問題")

        if self.report["high_issues"]:
            self.report["recommendations"].append("⚠️ 優先處理 High 級別的安全問題")

        if self.report["summary"]["total_issues"] == 0:
            self.report["recommendations"].append("✅ 沒有發現明顯的安全問題，保持良好的安全實踐")

        # 保存報告
        report_file = f"security_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        logger.info(f"📝 安全報告已保存到: {report_file}")

        # 打印摘要
        self.print_summary()

    def print_summary(self):
        """打印安全摘要"""
        summary = self.report["summary"]

        print("\n" + "=" * 60)
        print("🔒 安全掃描摘要")
        print("=" * 60)
        print(f"📊 總問題數: {summary['total_issues']}")
        print(f"🚨 Critical: {summary['critical_count']}")
        print(f"⚠️  High: {summary['high_count']}")
        print(f"📋 Medium: {summary['medium_count']}")
        print(f"ℹ️  Low: {summary['low_count']}")

        if summary["critical_count"] > 0:
            print("\n🚨 Critical 問題:")
            for issue in self.report["critical_issues"][:3]:  # 只顯示前3個
                print(f"  • {issue['title']}")
                print(f"    位置: {issue['location']}")
                print(f"    建議: {issue['recommendation']}")

        print("\n💡 建議:")
        for rec in self.report["recommendations"]:
            print(f"  • {rec}")

        print("=" * 60)


def main():
    """主函數"""
    monitor = SecurityMonitor()

    try:
        report = monitor.run_full_security_scan()

        # 根據問題數量設置退出碼
        if report["summary"]["critical_count"] > 0:
            sys.exit(2)  # Critical 問題
        elif report["summary"]["high_count"] > 0:
            sys.exit(1)  # High 問題
        else:
            sys.exit(0)  # 沒有嚴重問題

    except KeyboardInterrupt:
        logger.info("安全掃描被用戶中斷")
        sys.exit(130)
    except Exception as e:
        logger.error(f"安全掃描失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
