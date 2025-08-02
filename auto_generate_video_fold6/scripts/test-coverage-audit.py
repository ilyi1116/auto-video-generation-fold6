#!/usr/bin/env python3
"""
測試覆蓋率審查工具
自動識別需要測試的模組並生成測試模板
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class TestCoverageAuditor:
    """測試覆蓋率審查器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.services_dir = self.project_root / "services"
        self.existing_tests = set()
        self.source_files = []
        self.coverage_report = {}

    def scan_existing_tests(self):
        """掃描現有測試文件"""
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "tests/*.py",
            "**/*test*.py",
        ]

        for pattern in test_patterns:
            for test_file in self.project_root.rglob(pattern):
                if test_file.is_file():
                    # 提取被測試的模組名稱
                    test_name = test_file.stem
                    if test_name.startswith("test_"):
                        module_name = test_name[5:]
                    elif test_name.endswith("_test"):
                        module_name = test_name[:-5]
                    else:
                        module_name = test_name

                    self.existing_tests.add(module_name)

        print(f"發現 {len(self.existing_tests)} 個現有測試文件")

    def scan_source_files(self):
        """掃描所有源碼文件"""
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            # 跳過測試文件、__pycache__、migrations 等
            if any(
                skip in str(py_file)
                for skip in [
                    "test",
                    "__pycache__",
                    "migrations",
                    "venv",
                    ".git",
                    "node_modules",
                    "dist",
                    "build",
                ]
            ):
                continue

            # 分析文件內容
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)

                file_info = self.analyze_python_file(py_file, tree)
                if file_info:
                    self.source_files.append(file_info)

            except Exception as e:
                print(f"分析文件 {py_file} 時出錯: {e}")

    def analyze_python_file(self, file_path: Path, tree: ast.AST) -> Dict:
        """分析 Python 文件結構"""
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(
                            {
                                "name": item.name,
                                "line": item.lineno,
                                "is_private": item.name.startswith("_"),
                                "is_async": isinstance(
                                    item, ast.AsyncFunctionDef
                                ),
                                "args": len(item.args.args),
                            }
                        )

                classes.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                    }
                )

            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                functions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "args": len(node.args.args),
                    }
                )

        relative_path = file_path.relative_to(self.project_root)
        module_name = str(relative_path).replace("/", ".").replace(".py", "")

        return {
            "file_path": str(file_path),
            "relative_path": str(relative_path),
            "module_name": module_name,
            "classes": classes,
            "functions": functions,
            "has_test": any(
                test in str(file_path) for test in self.existing_tests
            ),
            "complexity": len(classes) + len(functions),
        }

    def generate_coverage_report(self):
        """生成覆蓋率報告"""
        total_files = len(self.source_files)
        tested_files = sum(1 for f in self.source_files if f["has_test"])

        # 按服務分組
        services = {}
        unorganized = []

        for file_info in self.source_files:
            if file_info["relative_path"].startswith("services/"):
                service_name = file_info["relative_path"].split("/")[1]
                if service_name not in services:
                    services[service_name] = []
                services[service_name].append(file_info)
            else:
                unorganized.append(file_info)

        self.coverage_report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": total_files,
                "tested_files": tested_files,
                "coverage_percentage": round(
                    (tested_files / total_files) * 100, 2
                )
                if total_files > 0
                else 0,
                "untested_files": total_files - tested_files,
            },
            "services": {},
            "unorganized": unorganized,
            "priority_files": [],
        }

        # 分析各服務覆蓋率
        for service_name, files in services.items():
            service_tested = sum(1 for f in files if f["has_test"])
            service_total = len(files)

            self.coverage_report["services"][service_name] = {
                "total_files": service_total,
                "tested_files": service_tested,
                "coverage_percentage": round(
                    (service_tested / service_total) * 100, 2
                )
                if service_total > 0
                else 0,
                "files": files,
            }

        # 識別高優先級需要測試的文件 (複雜度高且無測試)
        priority_files = []
        for file_info in self.source_files:
            if not file_info["has_test"] and file_info["complexity"] >= 3:
                priority_files.append(
                    {
                        "file": file_info["relative_path"],
                        "complexity": file_info["complexity"],
                        "classes_count": len(file_info["classes"]),
                        "functions_count": len(file_info["functions"]),
                    }
                )

        # 按複雜度排序
        priority_files.sort(key=lambda x: x["complexity"], reverse=True)
        self.coverage_report["priority_files"] = priority_files[:20]  # 前20個

    def generate_test_templates(self, output_dir: str = None):
        """為優先級文件生成測試模板"""
        if output_dir is None:
            output_dir = self.project_root / "test_templates"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(exist_ok=True)

        templates_created = []

        for priority_file in self.coverage_report["priority_files"][
            :10
        ]:  # 前10個
            file_path = self.project_root / priority_file["file"]

            # 找到對應的文件信息
            file_info = next(
                (
                    f
                    for f in self.source_files
                    if f["relative_path"] == priority_file["file"]
                ),
                None,
            )

            if file_info:
                template_content = self.create_test_template(file_info)

                # 確定測試文件路径
                test_filename = (
                    f"test_{Path(file_info['relative_path']).stem}.py"
                )
                test_file_path = output_dir / test_filename

                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(template_content)

                templates_created.append(str(test_file_path))

        return templates_created

    def create_test_template(self, file_info: Dict) -> str:
        """創建測試模板"""
        module_path = file_info["module_name"]

        template = f'''#!/usr/bin/env python3
"""
{file_info["relative_path"]} 的測試文件
自動生成的測試模板 - {datetime.now().strftime("%Y-%m-%d")}
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from {module_path} import *


class TestModule:
    """模組整體測試"""

    def setup_method(self):
        """測試設置"""
        pass

    def teardown_method(self):
        """測試清理"""
        pass

'''

        # 為每個類生成測試
        for class_info in file_info["classes"]:
            template += f'''
class Test{class_info["name"]}:
    """測試 {class_info["name"]} 類"""

    def setup_method(self):
        """設置測試環境"""
        pass

'''

            # 為每個方法生成測試
            for method in class_info["methods"]:
                if not method["is_private"]:  # 只為公共方法生成測試
                    template += f'''    def test_{method["name"]}(self):
        """測試 {method["name"]} 方法"""
        # TODO: 實現測試邏輯
        assert True

'''

        # 為函數生成測試
        for func_info in file_info["functions"]:
            if not func_info["name"].startswith("_"):  # 只為公共函數生成測試
                template += f'''def test_{func_info["name"]}():
    """測試 {func_info["name"]} 函數"""
    # TODO: 實現測試邏輯
    assert True


'''

        return template

    def save_report(self, output_file: str = None):
        """保存覆蓋率報告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = (
                self.project_root / f"test_coverage_report_{timestamp}.json"
            )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.coverage_report, f, indent=2, ensure_ascii=False)

        return output_file

    def print_summary(self):
        """打印摘要報告"""
        summary = self.coverage_report["summary"]

        print("\n" + "=" * 60)
        print("🧪 測試覆蓋率審查報告")
        print("=" * 60)
        print(f"📊 總文件數: {summary['total_files']}")
        print(f"✅ 已測試文件: {summary['tested_files']}")
        print(f"❌ 未測試文件: {summary['untested_files']}")
        print(f"📈 覆蓋率: {summary['coverage_percentage']}%")

        print(f"\n🎯 各服務覆蓋率:")
        for service_name, service_info in self.coverage_report[
            "services"
        ].items():
            coverage = service_info["coverage_percentage"]
            status = (
                "🟢" if coverage >= 80 else "🟡" if coverage >= 60 else "🔴"
            )
            print(
                f"  {status} {service_name}: {coverage}% ({service_info['tested_files']}/{service_info['total_files']})"
            )

        print(f"\n🚨 高優先級需要測試的文件 (複雜度 ≥ 3):")
        for i, priority_file in enumerate(
            self.coverage_report["priority_files"][:10], 1
        ):
            print(
                f"  {i:2d}. {priority_file['file']} (複雜度: {priority_file['complexity']})"
            )

    def run_audit(self):
        """執行完整審查"""
        print("🔍 掃描現有測試文件...")
        self.scan_existing_tests()

        print("📁 掃描源碼文件...")
        self.scan_source_files()

        print("📊 生成覆蓋率報告...")
        self.generate_coverage_report()

        print("📝 生成測試模板...")
        templates = self.generate_test_templates()

        print("💾 保存報告...")
        report_file = self.save_report()

        self.print_summary()

        print(f"\n📄 詳細報告已保存至: {report_file}")
        print(f"🧪 測試模板已生成 {len(templates)} 個文件")

        return report_file, templates


if __name__ == "__main__":
    import sys

    project_root = sys.argv[1] if len(sys.argv) > 1 else "."

    auditor = TestCoverageAuditor(project_root)
    report_file, templates = auditor.run_audit()

    print(f"\n🎉 審查完成！")
    print(f"📊 報告: {report_file}")
    print(f"🧪 模板: {len(templates)} 個文件已生成")
