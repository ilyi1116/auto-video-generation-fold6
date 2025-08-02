#!/usr/bin/env python3
"""
系統性能分析和成本控制工具
Phase 6: 系統調優與成本控制分析
"""

import json
import psutil
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import argparse


class SystemPerformanceAnalyzer:
    """系統性能分析器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metrics_history = []

    def collect_system_metrics(self) -> Dict:
        """收集系統指標"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "usage_percent": psutil.virtual_memory().percent,
                "swap_total": psutil.swap_memory().total,
                "swap_used": psutil.swap_memory().used,
                "swap_percent": psutil.swap_memory().percent
            },
            "disk": {
                path: {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "usage_percent": usage.percent
                }
                for path in ["/", "/tmp"] if Path(path).exists()
                for usage in [psutil.disk_usage(path)]
            },
            "network": self._get_network_io(),
            "processes": self._get_process_info()
        }

    def _get_network_io(self) -> Dict:
        """獲取網路 I/O 統計"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout
        }

    def _get_process_info(self) -> Dict:
        """獲取進程資訊"""
        processes = []
        docker_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
            try:
                pinfo = proc.info
                if pinfo['name'] and pinfo['cpu_percent'] is not None:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": pinfo['cpu_percent'],
                        "memory_percent": pinfo['memory_percent'],
                        "cmdline": ' '.join(pinfo['cmdline'][:3]) if pinfo['cmdline'] else ""
                    })

                    # 識別 Docker 相關進程
                    if any(keyword in pinfo['name'].lower()
                          for keyword in ['docker', 'containerd', 'dockerd']):
                        docker_processes.append(pinfo)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 按 CPU 使用率排序
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

        return {
            "total_processes": len(processes),
            "top_cpu_processes": processes[:10],
            "docker_processes": len(docker_processes)
        }

    def analyze_docker_containers(self) -> Dict:
        """分析 Docker 容器性能"""
        try:
            # 獲取容器統計
            result = subprocess.run([
                "docker", "stats", "--no-stream", "--format",
                "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
            ], capture_output=True, text=True, check=True)

            containers = []
            lines = result.stdout.strip().split('\n')[1:]  # 跳過標題行

            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 6:
                        containers.append({
                            "name": parts[0],
                            "cpu_percent": parts[1],
                            "memory_usage": parts[2],
                            "memory_percent": parts[3],
                            "network_io": parts[4],
                            "block_io": parts[5]
                        })

            return {
                "containers": containers,
                "total_containers": len(containers)
            }

        except subprocess.CalledProcessError:
            return {"error": "Failed to get container stats"}

    def analyze_database_performance(self) -> Dict:
        """分析資料庫性能 (如果可用)"""
        analysis = {
            "postgresql": {"available": False},
            "redis": {"available": False}
        }

        # 檢查 PostgreSQL
        try:
            result = subprocess.run([
                "psql", "-h", "localhost", "-U", "postgres", "-c",
                "SELECT version(), current_database(), current_user;"
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                analysis["postgresql"] = {
                    "available": True,
                    "version_info": result.stdout.strip()
                }
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # 檢查 Redis
        try:
            result = subprocess.run([
                "redis-cli", "ping"
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0 and "PONG" in result.stdout:
                # 獲取 Redis 資訊
                info_result = subprocess.run([
                    "redis-cli", "info", "memory"
                ], capture_output=True, text=True, timeout=5)

                analysis["redis"] = {
                    "available": True,
                    "ping_response": result.stdout.strip(),
                    "memory_info": info_result.stdout.strip() if info_result.returncode == 0 else None
                }
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        return analysis

    def calculate_cost_metrics(self, metrics: Dict) -> Dict:
        """計算成本指標"""
        # 基於資源使用率的成本估算 (假設值)
        cpu_cost_per_hour = 0.05  # 每 CPU 核心每小時成本
        memory_cost_per_gb_hour = 0.01  # 每 GB 記憶體每小時成本
        storage_cost_per_gb_month = 0.10  # 每 GB 存儲每月成本

        cpu_cores = metrics["cpu"]["count"]
        memory_gb = metrics["memory"]["total"] / (1024**3)

        # 計算磁碟使用量
        total_disk_gb = 0
        for disk_info in metrics["disk"].values():
            total_disk_gb += disk_info["used"] / (1024**3)

        hourly_cost = (
            cpu_cores * cpu_cost_per_hour +
            memory_gb * memory_cost_per_gb_hour
        )

        monthly_cost = (
            hourly_cost * 24 * 30 +
            total_disk_gb * storage_cost_per_gb_month
        )

        return {
            "hourly_cost_usd": round(hourly_cost, 4),
            "daily_cost_usd": round(hourly_cost * 24, 2),
            "monthly_cost_usd": round(monthly_cost, 2),
            "resource_breakdown": {
                "cpu_cores": cpu_cores,
                "memory_gb": round(memory_gb, 2),
                "storage_gb": round(total_disk_gb, 2)
            }
        }

    def generate_optimization_recommendations(self, metrics: Dict) -> List[str]:
        """生成優化建議"""
        recommendations = []

        # CPU 優化建議
        cpu_usage = metrics["cpu"]["usage_percent"]
        if cpu_usage > 80:
            recommendations.append("🔥 CPU 使用率過高 (>80%)，考慮垂直擴展或優化應用程式")
        elif cpu_usage < 20:
            recommendations.append("💡 CPU 使用率較低 (<20%)，可能可以減少資源配置")

        # 記憶體優化建議
        memory_usage = metrics["memory"]["usage_percent"]
        if memory_usage > 85:
            recommendations.append("🔥 記憶體使用率過高 (>85%)，考慮增加記憶體或優化記憶體使用")
        elif memory_usage < 30:
            recommendations.append("💡 記憶體使用率較低 (<30%)，可以考慮減少記憶體配置")

        # 磁碟優化建議
        for path, disk_info in metrics["disk"].items():
            if disk_info["usage_percent"] > 90:
                recommendations.append(f"🔥 磁碟空間不足 {path} (>{disk_info['usage_percent']:.1f}%)，需要清理或擴容")
            elif disk_info["usage_percent"] > 80:
                recommendations.append(f"⚠️ 磁碟使用率較高 {path} ({disk_info['usage_percent']:.1f}%)，建議監控")

        # 進程優化建議
        top_processes = metrics["processes"]["top_cpu_processes"][:5]
        high_cpu_processes = [p for p in top_processes if p["cpu_percent"] > 50]

        if high_cpu_processes:
            process_names = [p["name"] for p in high_cpu_processes]
            recommendations.append(f"🔍 發現高 CPU 使用進程: {', '.join(process_names)}，建議檢查")

        # 通用建議
        recommendations.extend([
            "📊 定期監控系統資源使用率",
            "🔄 實施自動化資源擴展策略",
            "📈 使用 Prometheus + Grafana 進行持續監控",
            "💰 定期檢查成本效益並調整資源配置"
        ])

        return recommendations

    def run_performance_test(self, duration_seconds: int = 60) -> Dict:
        """運行性能測試"""
        print(f"🏃 開始 {duration_seconds} 秒性能測試...")

        start_time = time.time()
        samples = []

        while time.time() - start_time < duration_seconds:
            sample = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_io": psutil.disk_io_counters()._asdict(),
                "network_io": psutil.net_io_counters()._asdict()
            }
            samples.append(sample)
            time.sleep(5)  # 每 5 秒收集一次

        # 計算統計資訊
        cpu_values = [s["cpu_percent"] for s in samples]
        memory_values = [s["memory_percent"] for s in samples]

        return {
            "duration_seconds": duration_seconds,
            "samples_count": len(samples),
            "cpu_stats": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory_stats": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "samples": samples
        }

    def generate_report(self, metrics: Dict, docker_stats: Dict,
                       db_analysis: Dict, cost_metrics: Dict,
                       recommendations: List[str]) -> str:
        """生成性能分析報告"""
        report = [
            "# 系統性能分析報告",
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 系統資源概況",
            f"- **CPU**: {metrics['cpu']['count']} 核心, 使用率 {metrics['cpu']['usage_percent']:.1f}%",
            f"- **記憶體**: {metrics['memory']['usage_percent']:.1f}% 使用 "
            f"({self._format_bytes(metrics['memory']['used'])}/{self._format_bytes(metrics['memory']['total'])})",
            ""
        ]

        # 磁碟使用情況
        report.append("### 磁碟使用情況")
        for path, disk_info in metrics["disk"].items():
            report.append(
                f"- **{path}**: {disk_info['usage_percent']:.1f}% 使用 "
                f"({self._format_bytes(disk_info['used'])}/{self._format_bytes(disk_info['total'])})"
            )
        report.append("")

        # 前 5 個 CPU 使用最高的進程
        report.extend([
            "### Top 5 CPU 使用進程",
            "| 進程名 | PID | CPU% | 記憶體% |",
            "|--------|-----|------|---------|"
        ])

        for proc in metrics["processes"]["top_cpu_processes"][:5]:
            report.append(
                f"| {proc['name']} | {proc['pid']} | {proc['cpu_percent']:.1f}% | {proc['memory_percent']:.1f}% |"
            )
        report.append("")

        # Docker 容器統計
        if docker_stats.get("containers"):
            report.extend([
                "## Docker 容器性能",
                f"運行中的容器: {docker_stats['total_containers']}",
                "",
                "| 容器名 | CPU% | 記憶體使用 | 記憶體% |",
                "|--------|------|------------|---------|"
            ])

            for container in docker_stats["containers"][:10]:
                report.append(
                    f"| {container['name']} | {container['cpu_percent']} | "
                    f"{container['memory_usage']} | {container['memory_percent']} |"
                )
            report.append("")

        # 資料庫狀態
        report.extend([
            "## 資料庫狀態",
            f"- **PostgreSQL**: {'✅ 可用' if db_analysis['postgresql']['available'] else '❌ 不可用'}",
            f"- **Redis**: {'✅ 可用' if db_analysis['redis']['available'] else '❌ 不可用'}",
            ""
        ])

        # 成本分析
        report.extend([
            "## 成本分析 (估算)",
            f"- **每小時成本**: ${cost_metrics['hourly_cost_usd']}",
            f"- **每日成本**: ${cost_metrics['daily_cost_usd']}",
            f"- **每月成本**: ${cost_metrics['monthly_cost_usd']}",
            "",
            "### 資源配置",
            f"- **CPU 核心**: {cost_metrics['resource_breakdown']['cpu_cores']}",
            f"- **記憶體**: {cost_metrics['resource_breakdown']['memory_gb']} GB",
            f"- **存儲**: {cost_metrics['resource_breakdown']['storage_gb']} GB",
            ""
        ])

        # 優化建議
        report.extend([
            "## 優化建議",
            ""
        ])

        for i, recommendation in enumerate(recommendations, 1):
            report.append(f"{i}. {recommendation}")

        report.extend([
            "",
            "## 監控建議",
            "- 設置資源使用率告警 (CPU > 80%, 記憶體 > 85%, 磁碟 > 90%)",
            "- 實施自動化性能監控",
            "- 定期執行性能基準測試",
            "- 建立資源使用趨勢分析"
        ])

        return "\n".join(report)

    def _format_bytes(self, bytes_value: int) -> str:
        """格式化位元組顯示"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"


def main():
    parser = argparse.ArgumentParser(description="系統性能分析工具")
    parser.add_argument("--output", help="輸出報告文件路徑", default="performance-report.md")
    parser.add_argument("--test", help="執行性能測試 (秒)", type=int, default=0)
    parser.add_argument("--json", help="同時輸出 JSON 格式", action="store_true")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    analyzer = SystemPerformanceAnalyzer(project_root)

    print("📊 系統性能分析工具")
    print("=" * 50)

    # 收集基本指標
    print("🔍 收集系統指標...")
    metrics = analyzer.collect_system_metrics()

    print("🐳 分析 Docker 容器...")
    docker_stats = analyzer.analyze_docker_containers()

    print("🗄️ 檢查資料庫狀態...")
    db_analysis = analyzer.analyze_database_performance()

    print("💰 計算成本指標...")
    cost_metrics = analyzer.calculate_cost_metrics(metrics)

    print("💡 生成優化建議...")
    recommendations = analyzer.generate_optimization_recommendations(metrics)

    # 執行性能測試 (如果指定)
    performance_test = None
    if args.test > 0:
        performance_test = analyzer.run_performance_test(args.test)

    # 生成報告
    print("📝 生成報告...")
    report = analyzer.generate_report(
        metrics, docker_stats, db_analysis, cost_metrics, recommendations
    )

    # 輸出報告
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📊 報告已生成: {output_path}")

    # 輸出 JSON 格式 (如果請求)
    if args.json:
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "docker_stats": docker_stats,
            "database_analysis": db_analysis,
            "cost_metrics": cost_metrics,
            "recommendations": recommendations,
            "performance_test": performance_test
        }

        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"📄 JSON 數據已輸出: {json_path}")

    print("\n✅ 分析完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
