#!/usr/bin/env python3
"""
測試執行器 - 統一的測試執行和報告工具
支援不同類型的測試和多種報告格式
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRunner:
    """測試執行器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or Path(__file__).parent.parent)
        self.results = {}

    def run_python_tests(
        self,
        test_type: str = "all",
        coverage: bool = True,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """執行 Python 測試"""
        logger.info(f"執行 Python 測試: {test_type}")

        cmd = ["python", "-m", "pytest"]

        # 測試類型選擇
        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "slow":
            cmd.extend(["--runslow"])
        elif test_type == "fast":
            cmd.extend(["-m", "not slow"])

        # 覆蓋率選項
        if coverage:
            cmd.extend(
                [
                    "--cov=.",
                    "--cov-report=html",
                    "--cov-report=xml",
                    "--cov-report=term",
                ]
            )

        # 詳細輸出
        if verbose:
            cmd.append("-v")

        # 輸出格式
        cmd.extend(["--junit-xml=test-results/pytest-results.xml"])

        # 確保測試結果目錄存在
        results_dir = self.project_root / "test-results"
        results_dir.mkdir(exist_ok=True)

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5分鐘超時
            )

            duration = time.time() - start_time

            return {
                "type": "python",
                "test_type": test_type,
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "coverage_enabled": coverage,
            }

        except subprocess.TimeoutExpired:
            return {
                "type": "python",
                "test_type": test_type,
                "success": False,
                "error": "測試執行超時",
                "duration": time.time() - start_time,
            }
        except Exception as e:
            return {
                "type": "python",
                "test_type": test_type,
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
            }

    def run_frontend_tests(self, test_type: str = "all") -> Dict[str, Any]:
        """執行前端測試"""
        logger.info(f"執行前端測試: {test_type}")

        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            return {
                "type": "frontend",
                "test_type": test_type,
                "success": False,
                "error": "前端目錄不存在",
            }

        # 檢查 package.json
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            return {
                "type": "frontend",
                "test_type": test_type,
                "success": False,
                "error": "package.json 不存在",
            }

        # 確保依賴已安裝
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            logger.info("安裝前端依賴...")
            npm_install = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
            )
            if npm_install.returncode != 0:
                return {
                    "type": "frontend",
                    "test_type": test_type,
                    "success": False,
                    "error": "npm install 失敗",
                    "stderr": npm_install.stderr,
                }

        # 根據測試類型選擇命令
        if test_type == "unit":
            cmd = ["npm", "run", "test:unit", "--", "--run"]
        elif test_type == "component":
            cmd = ["npm", "run", "test:component", "--", "--run"]
        elif test_type == "e2e":
            cmd = ["npm", "run", "test:e2e"]
        elif test_type == "coverage":
            cmd = ["npm", "run", "test:coverage", "--", "--run"]
        else:
            cmd = ["npm", "run", "test", "--", "--run"]

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=600,  # 10分鐘超時 (E2E 測試可能較長)
            )

            duration = time.time() - start_time

            return {
                "type": "frontend",
                "test_type": test_type,
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "type": "frontend",
                "test_type": test_type,
                "success": False,
                "error": "前端測試執行超時",
                "duration": time.time() - start_time,
            }
        except Exception as e:
            return {
                "type": "frontend",
                "test_type": test_type,
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
            }

    def run_linting(self, target: str = "all") -> Dict[str, Any]:
        """執行程式碼檢查"""
        logger.info(f"執行程式碼檢查: {target}")

        results = {}

        if target in ["all", "python"]:
            # Python 程式碼檢查
            python_results = {}

            # Black 格式檢查
            black_result = subprocess.run(
                ["black", "--check", "--dif", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            python_results["black"] = {
                "success": black_result.returncode == 0,
                "output": black_result.stdout,
                "errors": black_result.stderr,
            }

            # isort 導入排序檢查
            isort_result = subprocess.run(
                ["isort", "--check-only", "--dif", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            python_results["isort"] = {
                "success": isort_result.returncode == 0,
                "output": isort_result.stdout,
                "errors": isort_result.stderr,
            }

            # Ruff 檢查
            ruff_result = subprocess.run(
                ["ruf", "check", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            python_results["ruff"] = {
                "success": ruff_result.returncode == 0,
                "output": ruff_result.stdout,
                "errors": ruff_result.stderr,
            }

            results["python"] = python_results

        if target in ["all", "frontend"]:
            # 前端程式碼檢查
            frontend_dir = self.project_root / "frontend"
            if frontend_dir.exists():
                eslint_result = subprocess.run(
                    ["npm", "run", "lint"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                )
                results["frontend"] = {
                    "eslint": {
                        "success": eslint_result.returncode == 0,
                        "output": eslint_result.stdout,
                        "errors": eslint_result.stderr,
                    }
                }

        return {
            "type": "linting",
            "target": target,
            "success": all(
                tool_result.get("success", False)
                for lang_results in results.values()
                for tool_result in lang_results.values()
            ),
            "results": results,
        }

    def run_security_scan(self) -> Dict[str, Any]:
        """執行安全掃描"""
        logger.info("執行安全掃描")

        results = {}

        # Bandit 安全掃描
        bandit_result = subprocess.run(
            [
                "bandit",
                "-r",
                ".",
                "-",
                "json",
                "-o",
                "test-results/bandit-report.json",
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        results["bandit"] = {
            "success": bandit_result.returncode == 0,
            "output": bandit_result.stdout,
            "errors": bandit_result.stderr,
        }

        # Safety 依賴檢查
        safety_result = subprocess.run(
            ["safety", "check", "--json"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        results["safety"] = {
            "success": safety_result.returncode == 0,
            "output": safety_result.stdout,
            "errors": safety_result.stderr,
        }

        return {
            "type": "security",
            "success": all(
                result.get("success", False) for result in results.values()
            ),
            "results": results,
        }

    def run_health_checks(self) -> Dict[str, Any]:
        """執行健康檢查"""
        logger.info("執行系統健康檢查")

        try:
            # 執行健康監控
            health_result = subprocess.run(
                ["python", "monitoring/health_monitor.py", "once"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if health_result.returncode == 0:
                try:
                    health_data = json.loads(health_result.stdout)
                    return {
                        "type": "health_check",
                        "success": True,
                        "data": health_data,
                    }
                except json.JSONDecodeError:
                    return {
                        "type": "health_check",
                        "success": True,
                        "output": health_result.stdout,
                    }
            else:
                return {
                    "type": "health_check",
                    "success": False,
                    "error": health_result.stderr,
                    "output": health_result.stdout,
                }

        except Exception as e:
            return {"type": "health_check", "success": False, "error": str(e)}

    def generate_report(
        self, results: List[Dict[str, Any]], format: str = "json"
    ) -> str:
        """生成測試報告"""
        logger.info(f"生成測試報告: {format}")

        # 統計摘要
        summary = {
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "duration": sum(r.get("duration", 0) for r in results),
            "timestamp": time.time(),
        }

        report = {"summary": summary, "results": results}

        # 保存報告
        reports_dir = self.project_root / "test-results"
        reports_dir.mkdir(exist_ok=True)

        if format == "json":
            report_file = reports_dir / "test-report.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        elif format == "html":
            report_file = reports_dir / "test-report.html"
            html_content = self._generate_html_report(report)
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(html_content)

        return str(report_file)

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """生成 HTML 報告"""
        summary = report["summary"]
        results = report["results"]

        html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>測試報告 - Auto Video Generation</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 2rem; font-weight: bold; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .test-result {{ background: white; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-header {{ padding: 15px; border-bottom: 1px solid #eee; }}
        .test-details {{ padding: 15px; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.8rem; }}
        .status-success {{ background: #28a745; }}
        .status-failure {{ background: #dc3545; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 測試報告</h1>
        <p>Auto Video Generation System - 測試執行結果</p>
        <p>生成時間: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="summary">
        <div class="stat">
            <div class="stat-value">{summary["total_tests"]}</div>
            <div>總測試數</div>
        </div>
        <div class="stat">
            <div class="stat-value success">{summary["passed"]}</div>
            <div>通過</div>
        </div>
        <div class="stat">
            <div class="stat-value failure">{summary["failed"]}</div>
            <div>失敗</div>
        </div>
        <div class="stat">
            <div class="stat-value">{summary["duration"]:.1f}s</div>
            <div>總耗時</div>
        </div>
    </div>

    <h2>詳細結果</h2>
"""

        for result in results:
            status_class = (
                "success" if result.get("success", False) else "failure"
            )
            badge_class = (
                "status-success"
                if result.get("success", False)
                else "status-failure"
            )
            status_text = "通過" if result.get("success", False) else "失敗"

            html += """
    <div class="test-result">
        <div class="test-header">
            <span class="status-badge {badge_class}">{status_text}</span>
            <strong>{result.get("type", "Unknown")} - {result.get("test_type", "General")}</strong>
            <span style="float: right;">耗時: {result.get("duration", 0):.1f}s</span>
        </div>
        <div class="test-details">
"""

            if result.get("error"):
                html += f"<p><strong>錯誤:</strong> {result['error']}</p>"

            if result.get("stdout"):
                html += f"<details><summary>標準輸出</summary><pre>{result['stdout'][:1000]}</pre></details>"

            if result.get("stderr"):
                html += f"<details><summary>錯誤輸出</summary><pre>{result['stderr'][:1000]}</pre></details>"

            html += """
        </div>
    </div>
"""

        html += """
</body>
</html>
"""
        return html


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="測試執行器")
    parser.add_argument(
        "--type",
        choices=["all", "python", "frontend", "lint", "security", "health"],
        default="all",
        help="測試類型",
    )
    parser.add_argument(
        "--python-test-type",
        choices=["all", "unit", "integration", "slow", "fast"],
        default="all",
        help="Python 測試類型",
    )
    parser.add_argument(
        "--frontend-test-type",
        choices=["all", "unit", "component", "e2e", "coverage"],
        default="all",
        help="前端測試類型",
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="跳過覆蓋率收集"
    )
    parser.add_argument(
        "--report-format",
        choices=["json", "html"],
        default="json",
        help="報告格式",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="詳細輸出"
    )

    args = parser.parse_args()

    runner = TestRunner()
    results = []

    try:
        if args.type in ["all", "python"]:
            logger.info("執行 Python 測試...")
            python_result = runner.run_python_tests(
                test_type=args.python_test_type,
                coverage=not args.no_coverage,
                verbose=args.verbose,
            )
            results.append(python_result)

        if args.type in ["all", "frontend"]:
            logger.info("執行前端測試...")
            frontend_result = runner.run_frontend_tests(
                test_type=args.frontend_test_type
            )
            results.append(frontend_result)

        if args.type in ["all", "lint"]:
            logger.info("執行程式碼檢查...")
            lint_result = runner.run_linting()
            results.append(lint_result)

        if args.type in ["all", "security"]:
            logger.info("執行安全掃描...")
            security_result = runner.run_security_scan()
            results.append(security_result)

        if args.type in ["all", "health"]:
            logger.info("執行健康檢查...")
            health_result = runner.run_health_checks()
            results.append(health_result)

        # 生成報告
        report_file = runner.generate_report(
            results, format=args.report_format
        )
        logger.info(f"測試報告已生成: {report_file}")

        # 輸出摘要
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("success", False))
        failed_tests = total_tests - passed_tests

        print("\n📊 測試摘要:")
        print(f"   總計: {total_tests}")
        print(f"   通過: {passed_tests}")
        print(f"   失敗: {failed_tests}")
        print(
            f"   成功率: {(passed_tests / total_tests) * 100:.1f}%"
            if total_tests > 0
            else "   成功率: N/A"
        )

        # 如果有失敗的測試，返回非零退出代碼
        if failed_tests > 0:
            print(f"\n❌ {failed_tests} 個測試失敗")
            sys.exit(1)
        else:
            print("\n✅ 所有測試通過!")

    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"測試執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
