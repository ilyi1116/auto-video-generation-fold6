#!/usr/bin/env python3
"""
Docker 容器優化腳本
Phase 6: 性能優化 - 分析和優化容器大小
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class DockerOptimizer:
    """Docker 容器優化工具"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_dir = project_root / "services"

    def get_image_size(self, image_name: str) -> int:
        """獲取 Docker 映像大小 (bytes)"""
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "json", image_name],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                image_info = json.loads(result.stdout.strip().split("\n")[0])
                size_str = image_info.get("Size", "0B")
                return self._parse_size(size_str)
            return 0
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return 0

    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串為 bytes"""
        size_str = size_str.replace("B", "").strip()
        if size_str == "0":
            return 0

        multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}

        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-1]) * multiplier)

        return int(float(size_str))

    def format_size(self, size_bytes: int) -> str:
        """格式化大小顯示"""
        if size_bytes == 0:
            return "0B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def analyze_dockerfile(self, dockerfile_path: Path) -> Dict:
        """分析 Dockerfile 並提供優化建議"""
        if not dockerfile_path.exists():
            return {"error": "Dockerfile not found"}

        with open(dockerfile_path, "r") as f:
            content = f.read()

        analysis = {
            "size_issues": [],
            "security_issues": [],
            "performance_issues": [],
            "recommendations": [],
        }

        lines = content.split("\n")

        # 檢查基礎映像
        for line in lines:
            line = line.strip()
            if line.startswith("FROM "):
                image = line.split()[1]
                if ":" not in image or image.endswith(":latest"):
                    analysis["security_issues"].append(
                        "使用具體版本標籤而非 latest"
                    )
                if "ubuntu" in image or "debian" in image:
                    analysis["size_issues"].append(
                        f"考慮使用更小的基礎映像，當前: {image}"
                    )
                    analysis["recommendations"].append(
                        "建議使用 alpine 或 distroless 映像"
                    )

        # 檢查 RUN 指令
        consecutive_runs = 0
        for line in lines:
            line = line.strip()
            if line.startswith("RUN "):
                consecutive_runs += 1
                if (
                    "apt-get update" in line
                    and "&& rm -rf /var/lib/apt/lists/*" not in line
                ):
                    analysis["size_issues"].append(
                        "RUN apt-get update 後應清理快取"
                    )
            else:
                if consecutive_runs > 1:
                    analysis["performance_issues"].append(
                        f"發現 {consecutive_runs} 個連續的 RUN 指令，建議合併"
                    )
                consecutive_runs = 0

        # 檢查複製操作
        for line in lines:
            line = line.strip()
            if line.startswith("COPY ") and ". " in line:
                analysis["size_issues"].append(
                    "避免 COPY . 複製不必要的文件，使用 .dockerignore"
                )

        # 檢查用戶配置
        has_user = any(line.strip().startswith("USER ") for line in lines)
        if not has_user:
            analysis["security_issues"].append("應該設置非 root 用戶運行容器")

        return analysis

    def build_and_analyze(
        self, service_name: str, dockerfile_path: str = "Dockerfile"
    ) -> Dict:
        """建構映像並分析大小"""
        service_dir = self.services_dir / service_name
        dockerfile = service_dir / dockerfile_path

        if not dockerfile.exists():
            return {"error": f"Dockerfile not found: {dockerfile}"}

        image_name = f"auto-video-{service_name}:analysis"

        print(f"🔨 建構映像: {image_name}")
        try:
            # 建構映像
            result = subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    image_name,
                    "-f",
                    str(dockerfile),
                    str(service_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # 獲取映像大小
            size = self.get_image_size(image_name)

            # 分析層次
            layers = self._analyze_layers(image_name)

            # 分析 Dockerfile
            dockerfile_analysis = self.analyze_dockerfile(dockerfile)

            return {
                "service": service_name,
                "image_name": image_name,
                "size_bytes": size,
                "size_formatted": self.format_size(size),
                "layers": layers,
                "dockerfile_analysis": dockerfile_analysis,
                "build_success": True,
            }

        except subprocess.CalledProcessError as e:
            return {
                "service": service_name,
                "error": f"Build failed: {e.stderr}",
                "build_success": False,
            }

    def _analyze_layers(self, image_name: str) -> List[Dict]:
        """分析映像層次"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "history",
                    "--no-trunc",
                    "--format",
                    "json",
                    image_name,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            layers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    layer_info = json.loads(line)
                    layers.append(
                        {
                            "size": layer_info.get("Size", "0B"),
                            "created_by": layer_info.get("CreatedBy", "")[:100]
                            + "...",
                            "comment": layer_info.get("Comment", ""),
                        }
                    )

            return layers
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def optimize_all_services(self) -> Dict:
        """優化所有服務的 Docker 映像"""
        results = {}

        # 查找所有服務目錄
        if self.services_dir.exists():
            for service_dir in self.services_dir.iterdir():
                if (
                    service_dir.is_dir()
                    and (service_dir / "Dockerfile").exists()
                ):
                    service_name = service_dir.name
                    print(f"\n📊 分析服務: {service_name}")
                    results[service_name] = self.build_and_analyze(
                        service_name
                    )

        return results

    def generate_report(self, results: Dict) -> str:
        """生成優化報告"""
        report = ["# Docker 容器優化報告", ""]

        total_size = 0
        successful_builds = 0

        for service_name, result in results.items():
            report.append(f"## {service_name}")

            if result.get("build_success"):
                successful_builds += 1
                size = result["size_bytes"]
                total_size += size

                report.append(f"- **映像大小**: {result['size_formatted']}")
                report.append(f"- **映像名稱**: {result['image_name']}")

                # Dockerfile 分析
                analysis = result["dockerfile_analysis"]
                if analysis.get("size_issues"):
                    report.append("- **大小優化建議**:")
                    for issue in analysis["size_issues"]:
                        report.append(f"  - {issue}")

                if analysis.get("security_issues"):
                    report.append("- **安全性建議**:")
                    for issue in analysis["security_issues"]:
                        report.append(f"  - {issue}")

                if analysis.get("performance_issues"):
                    report.append("- **性能優化建議**:")
                    for issue in analysis["performance_issues"]:
                        report.append(f"  - {issue}")

                if analysis.get("recommendations"):
                    report.append("- **通用建議**:")
                    for rec in analysis["recommendations"]:
                        report.append(f"  - {rec}")
            else:
                report.append(
                    f"- **建構失敗**: {result.get('error', 'Unknown error')}"
                )

            report.append("")

        # 總結
        report.extend(
            [
                "## 總結",
                f"- **成功建構服務數**: {successful_builds}/{len(results)}",
                f"- **映像總大小**: {self.format_size(total_size)}",
                f"- **平均映像大小**: {self.format_size(total_size // max(successful_builds, 1))}",
                "",
            ]
        )

        # 優化建議
        report.extend(
            [
                "## 整體優化建議",
                "1. 使用 Alpine Linux 作為基礎映像",
                "2. 使用多階段建構減少最終映像大小",
                "3. 合併 RUN 指令減少層次數量",
                "4. 設置適當的 .dockerignore 文件",
                "5. 定期清理未使用的映像和容器",
                "6. 使用 distroless 映像提高安全性",
                "",
            ]
        )

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Docker 容器優化工具")
    parser.add_argument("--service", help="指定要分析的服務名稱")
    parser.add_argument(
        "--output",
        help="輸出報告文件路徑",
        default="docker-optimization-report.md",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="詳細輸出"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    optimizer = DockerOptimizer(project_root)

    print("🐳 Docker 容器優化分析工具")
    print("=" * 50)

    if args.service:
        # 分析單個服務
        print(f"分析服務: {args.service}")
        results = {args.service: optimizer.build_and_analyze(args.service)}
    else:
        # 分析所有服務
        print("分析所有服務...")
        results = optimizer.optimize_all_services()

    # 生成報告
    report = optimizer.generate_report(results)

    # 輸出報告
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📊 報告已生成: {output_path}")

    if args.verbose:
        print("\n" + "=" * 50)
        print(report)

    # 檢查是否有建構失敗
    failed_services = [
        name
        for name, result in results.items()
        if not result.get("build_success")
    ]

    if failed_services:
        print(f"\n⚠️  建構失敗的服務: {', '.join(failed_services)}")
        return 1

    print("\n✅ 所有服務分析完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
