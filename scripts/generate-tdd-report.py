#!/usr/bin/env python3
"""
TDD 測試報告自動化生成工具 (Python 版本)
遵循 TDD 原則，收集並生成詳細的測試報告
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class TDDReportGenerator:
    """TDD 測試報告生成器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.report_dir = self.project_root / "tdd-reports"
        self.coverage_dir = self.project_root / "coverage-reports"
        self.timestamp = datetime.now().isoformat()

        # 確保報告目錄存在
        self.report_dir.mkdir(exist_ok=True)

        # TDD 配置
        self.tdd_config = {
            "coverage_threshold": 90,
            "complexity_limit": 10,
            "max_line_length": 88,
            "required_test_patterns": ["test_*.py", "*_test.py", "tests/"],
        }

    def run_command(self, cmd: str, cwd: Optional[Path] = None, timeout: int = 60) -> tuple:
        """安全執行命令並返回結果"""
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"命令超時: {cmd}"
        except Exception as e:
            return False, "", str(e)

    def collect_git_info(self) -> Optional[Dict[str, Any]]:
        """收集 Git 資訊"""
        print("📊 收集 Git 資訊...")

        git_commands = {
            "commit_hash": "git rev-parse HEAD",
            "commit_message": "git log -1 --pretty=format:%s",
            "branch": "git rev-parse --abbrev-ref HEAD",
            "author": "git log -1 --pretty=format:%an",
            "date": "git log -1 --pretty=format:%ai",
        }

        git_info = {}
        for key, cmd in git_commands.items():
            success, stdout, stderr = self.run_command(cmd)
            if success:
                git_info[key] = stdout.strip()
            else:
                print(f"⚠️ 無法取得 {key}: {stderr}")
                return None

        # 檢測 TDD 階段
        commit_msg = git_info.get("commit_message", "")
        tdd_phase = "unknown"
        if commit_msg.startswith("red:"):
            tdd_phase = "red"
        elif commit_msg.startswith("green:"):
            tdd_phase = "green"
        elif commit_msg.startswith("refactor:"):
            tdd_phase = "refactor"

        git_info.update({"short_hash": git_info["commit_hash"][:8], "tdd_phase": tdd_phase})

        return git_info

    def collect_frontend_data(self) -> Dict[str, Any]:
        """收集前端測試數據"""
        print("📱 收集前端測試數據...")

        frontend_dir = self.project_root / "frontend"
        frontend_data = {
            "exists": frontend_dir.exists(),
            "tests_run": False,
            "coverage": None,
            "test_results": None,
            "lint_results": None,
        }

        if not frontend_data["exists"]:
            return frontend_data

        # 檢查 package.json
        package_json = frontend_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                frontend_data["scripts"] = package_data.get("scripts", {})
            except Exception as e:
                print(f"⚠️ 無法讀取 package.json: {e}")

        # 收集測試覆蓋率
        coverage_file = frontend_dir / "coverage" / "coverage-summary.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                frontend_data["coverage"] = {
                    "statements": coverage_data["total"]["statements"]["pct"],
                    "branches": coverage_data["total"]["branches"]["pct"],
                    "functions": coverage_data["total"]["functions"]["pct"],
                    "lines": coverage_data["total"]["lines"]["pct"],
                }
            except Exception as e:
                print(f"⚠️ 覆蓋率數據讀取失敗: {e}")

        # 嘗試執行測試
        os.chdir(frontend_dir)
        try:
            # 檢查是否有 node_modules
            if (frontend_dir / "node_modules").exists():
                # 執行測試
                success, stdout, stderr = self.run_command("npm test -- --run --reporter=json")
                if success:
                    frontend_data["tests_run"] = True
                    frontend_data["test_results"] = self.parse_test_output(stdout)
                else:
                    print(f"⚠️ 前端測試執行失敗: {stderr}")
            else:
                print("⚠️ 前端依賴未安裝，跳過測試執行")

        except Exception as e:
            print(f"前端測試執行錯誤: {e}")
        finally:
            os.chdir(self.project_root)

        return frontend_data

    def collect_backend_data(self) -> Dict[str, Any]:
        """收集後端測試數據"""
        print("🔧 收集後端測試數據...")

        services_dir = self.project_root / "services"
        backend_data = {
            "services": [],
            "total_coverage": 0,
            "total_tests": 0,
            "total_services": 0,
        }

        if not services_dir.exists():
            return backend_data

        # 收集所有服務
        for service_dir in services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith("."):
                service_data = self.collect_service_data(service_dir)
                backend_data["services"].append(service_data)

        # 計算總體統計
        valid_services = [s for s in backend_data["services"] if s["coverage"]]
        backend_data["total_services"] = len(backend_data["services"])

        if valid_services:
            backend_data["total_coverage"] = sum(
                s["coverage"]["statements"] for s in valid_services
            ) / len(valid_services)

        backend_data["total_tests"] = sum(
            s["test_results"]["total"] for s in backend_data["services"] if s["test_results"]
        )

        return backend_data

    def collect_service_data(self, service_dir: Path) -> Dict[str, Any]:
        """收集單個服務的測試數據"""
        service_name = service_dir.name
        service_data = {
            "name": service_name,
            "path": str(service_dir),
            "exists": service_dir.exists(),
            "has_tests": False,
            "coverage": None,
            "test_results": None,
            "code_quality": None,
            "requirements": None,
        }

        if not service_data["exists"]:
            return service_data

        # 檢查測試目錄
        tests_dir = service_dir / "tests"
        service_data["has_tests"] = tests_dir.exists()

        # 檢查 requirements
        for req_file in ["requirements.txt", "requirements-dev.txt"]:
            req_path = service_dir / req_file
            if req_path.exists():
                if not service_data["requirements"]:
                    service_data["requirements"] = {}
                try:
                    with open(req_path) as f:
                        service_data["requirements"][req_file] = f.read().splitlines()
                except Exception as e:
                    print(f"⚠️ 無法讀取 {req_file}: {e}")

        if not service_data["has_tests"]:
            return service_data

        # 切換到服務目錄
        original_cwd = os.getcwd()
        os.chdir(service_dir)

        try:
            # 收集測試覆蓋率
            success, stdout, stderr = self.run_command(
                "python -m pytest --cov=app --cov-report=json --cov-report=term-missing -q"
            )

            if success:
                coverage_file = service_dir / "coverage.json"
                if coverage_file.exists():
                    try:
                        with open(coverage_file) as f:
                            coverage_data = json.load(f)

                        service_data["coverage"] = {
                            "statements": round(coverage_data["totals"]["percent_covered"] or 0),
                            "missing": coverage_data["totals"]["missing_lines"] or 0,
                            "total": coverage_data["totals"]["num_statements"] or 0,
                        }
                    except Exception as e:
                        print(f"⚠️ {service_name} 覆蓋率解析失敗: {e}")

            # 收集測試結果
            success, stdout, stderr = self.run_command("python -m pytest --tb=no --quiet")
            if success or stderr:  # pytest 可能返回非零但有有效輸出
                service_data["test_results"] = self.parse_pytest_output(stdout + stderr)

            # 收集程式碼品質
            success, stdout, stderr = self.run_command(
                f"flake8 app/ --max-complexity={self.tdd_config['complexity_limit']} --statistics"
            )
            service_data["code_quality"] = self.parse_flake8_output(stdout + stderr)

        except Exception as e:
            print(f"⚠️ {service_name} 數據收集錯誤: {e}")
        finally:
            os.chdir(original_cwd)

        return service_data

    def parse_test_output(self, output: str) -> Dict[str, int]:
        """解析測試輸出"""
        results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

        # 簡化的解析邏輯
        lines = output.split("\n")
        for line in lines:
            if "passed" in line.lower():
                import re

                match = re.search(r"(\d+)\s+passed", line)
                if match:
                    results["passed"] = int(match.group(1))

            if "failed" in line.lower():
                import re

                match = re.search(r"(\d+)\s+failed", line)
                if match:
                    results["failed"] = int(match.group(1))

            if "skipped" in line.lower():
                import re

                match = re.search(r"(\d+)\s+skipped", line)
                if match:
                    results["skipped"] = int(match.group(1))

        results["total"] = results["passed"] + results["failed"] + results["skipped"]
        return results

    def parse_pytest_output(self, output: str) -> Dict[str, int]:
        """解析 pytest 輸出"""
        results = {"total": 0, "passed": 0, "failed": 0, "errors": 0}

        import re

        # 尋找測試結果摘要
        summary_patterns = [
            r"(\d+)\s+passed",
            r"(\d+)\s+failed",
            r"(\d+)\s+error",
            r"(\d+)\s+skipped",
        ]

        for pattern in summary_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                count = int(matches[-1])  # 取最後一個匹配
                if "passed" in pattern:
                    results["passed"] = count
                elif "failed" in pattern:
                    results["failed"] = count
                elif "error" in pattern:
                    results["errors"] = count

        results["total"] = results["passed"] + results["failed"] + results["errors"]
        return results

    def parse_flake8_output(self, output: str) -> Dict[str, Any]:
        """解析 flake8 輸出"""
        lines = output.strip().split("\n")
        issues = 0
        complexity_issues = 0
        error_types = {}

        for line in lines:
            if line.strip() and not line.startswith("Total"):
                issues += 1

                # 檢查複雜度問題
                if "C901" in line or "too complex" in line:
                    complexity_issues += 1

                # 統計錯誤類型
                import re

                match = re.search(r"([A-Z]\d{3})", line)
                if match:
                    error_code = match.group(1)
                    error_types[error_code] = error_types.get(error_code, 0) + 1

        return {
            "total_issues": issues,
            "complexity_issues": complexity_issues,
            "error_types": error_types,
        }

    def check_tdd_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查 TDD 合規性"""
        frontend = data["frontend"]
        backend = data["backend"]

        compliance = {
            "overall": False,
            "coverage": False,
            "test_existence": False,
            "code_quality": False,
            "tdd_workflow": False,
            "score": 0,
            "details": {},
        }

        # 檢查覆蓋率 (40分)
        avg_coverage = backend.get("total_coverage", 0)
        frontend_coverage = (
            frontend.get("coverage", {}).get("statements", 0) if frontend.get("coverage") else 0
        )

        overall_coverage = (
            (avg_coverage + frontend_coverage) / 2 if frontend_coverage else avg_coverage
        )
        compliance["coverage"] = overall_coverage >= self.tdd_config["coverage_threshold"]
        compliance["details"]["coverage_score"] = overall_coverage

        # 檢查測試存在性 (30分)
        has_backend_tests = any(s["has_tests"] for s in backend.get("services", []))
        has_frontend_tests = frontend.get("tests_run", False)
        compliance["test_existence"] = has_backend_tests or has_frontend_tests

        # 檢查程式碼品質 (20分)
        total_quality_issues = sum(
            s.get("code_quality", {}).get("total_issues", 0) for s in backend.get("services", [])
        )
        compliance["code_quality"] = total_quality_issues < 10
        compliance["details"]["quality_issues"] = total_quality_issues

        # 檢查 TDD 工作流程 (10分)
        git_info = data.get("git")
        if git_info:
            compliance["tdd_workflow"] = git_info.get("tdd_phase") != "unknown"
            compliance["details"]["tdd_phase"] = git_info.get("tdd_phase")

        # 計算總分
        score = 0
        if compliance["coverage"]:
            score += 40
        if compliance["test_existence"]:
            score += 30
        if compliance["code_quality"]:
            score += 20
        if compliance["tdd_workflow"]:
            score += 10

        compliance["score"] = score
        compliance["overall"] = score >= 80

        return compliance

    def generate_html_report(self, data: Dict[str, Any]) -> Path:
        """生成 HTML 報告"""
        print("📝 生成 HTML 報告...")

        frontend = data["frontend"]
        backend = data["backend"]
        git = data["git"]
        compliance = self.check_tdd_compliance(data)

        # 讀取 HTML 模板（這裡簡化為內嵌）
        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TDD 測試報告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333; background: #f5f7fa;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .tdd-phase {
            display: inline-block; padding: 5px 15px; border-radius: 20px;
            font-weight: bold; text-transform: uppercase; margin-top: 10px;
        }
        .phase-red { background: #e74c3c; }
        .phase-green { background: #27ae60; }
        .phase-refactor { background: #3498db; }
        .phase-unknown { background: #95a5a6; }

        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: white; border-radius: 10px; padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s;
        }
        .card:hover { transform: translateY(-2px); }
        .card h2 { color: #2c3e50; margin-bottom: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }

        .metric {
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 0; border-bottom: 1px solid #ecf0f1;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value { font-weight: bold; }
        .success { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }

        .coverage-bar {
            width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px;
            overflow: hidden; margin: 10px 0;
        }
        .coverage-fill {
            height: 100%; background: linear-gradient(90deg, #e74c3c 0%, #f39c12 70%, #27ae60 90%);
            transition: width 0.3s ease;
        }

        .compliance-score {
            font-size: 3em; font-weight: bold; text-align: center;
            color: {compliance_color}; margin: 20px 0;
        }

        .footer {
            text-align: center; padding: 30px; color: #7f8c8d;
            border-top: 1px solid #ecf0f1; margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 TDD 測試報告</h1>
            {git_info}
        </div>

        <div class="grid">
            <!-- TDD 合規性卡片 -->
            <div class="card">
                <h2>🎯 TDD 合規性</h2>
                <div class="compliance-score">{compliance_score}/100</div>
                <div class="metric">
                    <span>整體合規</span>
                    <span class="metric-value {compliance_class}">
                        {compliance_status}
                    </span>
                </div>
                <div class="metric">
                    <span>測試覆蓋率</span>
                    <span class="metric-value {coverage_class}">
                        {coverage_status}
                    </span>
                </div>
                <div class="metric">
                    <span>測試存在性</span>
                    <span class="metric-value {test_class}">
                        {test_status}
                    </span>
                </div>
                <div class="metric">
                    <span>程式碼品質</span>
                    <span class="metric-value {quality_class}">
                        {quality_status}
                    </span>
                </div>
            </div>

            <!-- 前端測試卡片 -->
            <div class="card">
                <h2>📱 前端測試</h2>
                {frontend_content}
            </div>

            <!-- 後端測試卡片 -->
            <div class="card">
                <h2>🔧 後端測試</h2>
                {backend_content}
            </div>
        </div>

        <div class="footer">
            <p>報告生成時間: {timestamp}</p>
            <p>🧬 基於 Test-Driven Development 最佳實踐</p>
        </div>
    </div>
</body>
</html>"""

        # 準備模板變數
        template_vars = {
            "timestamp": self.timestamp,
            "compliance_score": compliance["score"],
            "compliance_color": ("#27ae60" if compliance["overall"] else "#e74c3c"),
            "compliance_class": ("success" if compliance["overall"] else "error"),
            "compliance_status": ("✅ 通過" if compliance["overall"] else "❌ 需改進"),
            "coverage_class": ("success" if compliance["coverage"] else "warning"),
            "coverage_status": ("✅ 達標" if compliance["coverage"] else "⚠️ 不足"),
            "test_class": ("success" if compliance["test_existence"] else "error"),
            "test_status": ("✅ 存在" if compliance["test_existence"] else "❌ 缺失"),
            "quality_class": ("success" if compliance["code_quality"] else "warning"),
            "quality_status": ("✅ 良好" if compliance["code_quality"] else "⚠️ 有問題"),
        }

        # Git 資訊
        if git:
            template_vars[
                "git_info"
            ] = """
                <p><strong>提交:</strong> {git["short_hash"]} - {git["commit_message"]}</p>
                <p><strong>分支:</strong> {git["branch"]} | <strong>作者:</strong> {git["author"]}</p>
                <p><strong>時間:</strong> {git["date"]}</p>
                <span class="tdd-phase phase-{git["tdd_phase"]}">TDD {git["tdd_phase"].upper()} 階段</span>
            """
        else:
            template_vars["git_info"] = "<p>⚠️ 無法取得 Git 資訊</p>"

        # 前端內容
        if frontend["exists"]:
            frontend_html = []
            if frontend.get("coverage"):
                frontend["coverage"]
                frontend_html.append(
                    """
                    <div class="metric">
                        <span>語句覆蓋率</span>
                        <span class="metric-value {"success" if cov["statements"] >= 90 else "warning"}">
                            {cov["statements"]}%
                        </span>
                    </div>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: {cov["statements"]}%"></div>
                    </div>
                """
                )

            if frontend.get("test_results"):
                frontend["test_results"]
                frontend_html.append(
                    """
                    <div class="metric">
                        <span>通過測試</span>
                        <span class="metric-value success">{test["passed"]}</span>
                    </div>
                    <div class="metric">
                        <span>失敗測試</span>
                        <span class="metric-value {"error" if test["failed"] > 0 else "success"}">
                            {test["failed"]}
                        </span>
                    </div>
                """
                )

            template_vars["frontend_content"] = "".join(frontend_html) or "<p>⚠️ 未找到測試數據</p>"
        else:
            template_vars["frontend_content"] = '<p class="error">❌ 前端目錄不存在</p>'

        # 後端內容
        if backend["services"]:
            backend_html = []
            backend_html.append(
                """
                <div class="metric">
                    <span>服務總數</span>
                    <span class="metric-value">{backend["total_services"]}</span>
                </div>
                <div class="metric">
                    <span>平均覆蓋率</span>
                    <span class="metric-value {"success" if backend["total_coverage"] >= 90 else "warning"}">
                        {backend["total_coverage"]:.1f}%
                    </span>
                </div>
                <div class="metric">
                    <span>總測試數</span>
                    <span class="metric-value">{backend["total_tests"]}</span>
                </div>
            """
            )

            template_vars["backend_content"] = "".join(backend_html)
        else:
            template_vars["backend_content"] = "<p>⚠️ 未找到後端服務</p>"

        # 生成 HTML
        html_content = html_template.format(**template_vars)

        report_path = self.report_dir / "index.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return report_path

    def generate_json_report(self, data: Dict[str, Any]) -> Path:
        """生成 JSON 報告"""
        print("📄 生成 JSON 報告...")

        report_data = {
            "timestamp": self.timestamp,
            "version": "1.0.0",
            "tdd_config": self.tdd_config,
            "compliance": self.check_tdd_compliance(data),
            **data,
        }

        report_path = self.report_dir / "report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return report_path

    def generate(self):
        """主要執行函數"""
        print("🧬 開始生成 TDD 測試報告...")
        print("=" * 50)

        try:
            # 收集所有數據
            data = {
                "git": self.collect_git_info(),
                "frontend": self.collect_frontend_data(),
                "backend": self.collect_backend_data(),
            }

            # 生成報告
            html_path = self.generate_html_report(data)
            json_path = self.generate_json_report(data)

            print("=" * 50)
            print("✅ TDD 測試報告生成完成！")
            print(f"📄 HTML 報告: {html_path}")
            print(f"🔧 JSON 報告: {json_path}")

            # 顯示摘要
            compliance = self.check_tdd_compliance(data)
            print(f"📊 TDD 合規性評分: {compliance['score']}/100")
            print(f"🎯 整體合規: {'✅ 通過' if compliance['overall'] else '❌ 需改進'}")

            return True

        except Exception as e:
            print(f"❌ 報告生成失敗: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """主函數"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(
            """
TDD 測試報告生成工具

使用方法:
    python generate-tdd-report.py

功能:
    - 收集前端和後端測試數據
    - 分析測試覆蓋率和程式碼品質
    - 檢查 TDD 合規性
    - 生成 HTML 和 JSON 格式報告

輸出:
    - tdd-reports/index.html - HTML 格式報告
    - tdd-reports/report.json - JSON 格式數據
        """
        )
        return

    generator = TDDReportGenerator()
    success = generator.generate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
