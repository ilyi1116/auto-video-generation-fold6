#!/usr/bin/env python3
"""
報告生成器 - 統一的生成報告與成本統計功能
支援多種報告類型和格式，提供詳細的分析和可視化
"""

import asyncio
import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from jinja2 import Environment, FileSystemLoader
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設置 matplotlib 中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

@dataclass
class ReportConfig:
    """報告配置"""
    report_type: str  # daily, weekly, monthly, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_charts: bool = True
    include_cost_analysis: bool = True
    include_performance_metrics: bool = True
    output_format: str = "html"  # html, pdf, json
    output_path: Optional[str] = None

@dataclass
class GenerationMetrics:
    """生成指標"""
    total_videos: int
    successful_generations: int
    failed_generations: int
    total_cost: float
    average_cost_per_video: float
    platforms_distribution: Dict[str, int]
    quality_distribution: Dict[str, int]
    generation_time_stats: Dict[str, float]

class ReportGenerator:
    """報告生成器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # 初始化模板引擎
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # 確保模板文件存在
        self._create_default_templates()
        
        try:
            from monitoring.cost_tracker import get_cost_tracker
            self.cost_tracker = get_cost_tracker(config_manager)
        except ImportError:
            self.cost_tracker = None
            logger.warning("成本追蹤器不可用")
    
    def _create_default_templates(self):
        """創建預設模板文件"""
        template_dir = Path(__file__).parent / "templates"
        
        # HTML 報告模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 2.5rem; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .metric-value { font-size: 2rem; font-weight: bold; color: #333; margin-bottom: 5px; }
        .metric-label { color: #666; font-size: 0.9rem; }
        .chart-container { margin: 30px 0; text-align: center; }
        .chart-container img { max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .section { margin-bottom: 40px; }
        .section h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #f8f9fa; font-weight: 600; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; border-top: 1px solid #ddd; }
        .status-success { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <p>{{ report_period }} | 生成時間: {{ generation_time }}</p>
        </div>
        
        <div class="content">
            <!-- 關鍵指標 -->
            <div class="section">
                <h2>📊 關鍵指標</h2>
                <div class="metrics-grid">
                    {% for metric in key_metrics %}
                    <div class="metric-card">
                        <div class="metric-value {{ metric.status_class }}">{{ metric.value }}</div>
                        <div class="metric-label">{{ metric.label }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- 成本分析 -->
            {% if cost_analysis %}
            <div class="section">
                <h2>💰 成本分析</h2>
                {% if cost_charts %}
                    {% for chart in cost_charts %}
                    <div class="chart-container">
                        <h3>{{ chart.title }}</h3>
                        <img src="{{ chart.path }}" alt="{{ chart.title }}">
                    </div>
                    {% endfor %}
                {% endif %}
                
                <table class="table">
                    <thead>
                        <tr>
                            <th>項目</th>
                            <th>金額 (USD)</th>
                            <th>百分比</th>
                            <th>趨勢</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in cost_breakdown %}
                        <tr>
                            <td>{{ item.category }}</td>
                            <td>${{ "%.2f"|format(item.amount) }}</td>
                            <td>{{ "%.1f"|format(item.percentage) }}%</td>
                            <td class="{{ item.trend_class }}">{{ item.trend }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            <!-- 生成統計 -->
            <div class="section">
                <h2>🎬 生成統計</h2>
                {% if generation_charts %}
                    {% for chart in generation_charts %}
                    <div class="chart-container">
                        <h3>{{ chart.title }}</h3>
                        <img src="{{ chart.path }}" alt="{{ chart.title }}">
                    </div>
                    {% endfor %}
                {% endif %}
            </div>
            
            <!-- 詳細數據 -->
            {% if detailed_data %}
            <div class="section">
                <h2>📋 詳細數據</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>影片數量</th>
                            <th>成功率</th>
                            <th>總成本</th>
                            <th>平均成本</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in detailed_data %}
                        <tr>
                            <td>{{ row.date }}</td>
                            <td>{{ row.video_count }}</td>
                            <td class="{{ row.success_rate_class }}">{{ "%.1f"|format(row.success_rate) }}%</td>
                            <td>${{ "%.2f"|format(row.total_cost) }}</td>
                            <td>${{ "%.2f"|format(row.avg_cost) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Auto Video Generation System - 報告生成於 {{ generation_time }}</p>
        </div>
    </div>
</body>
</html>
"""
        
        html_template_path = template_dir / "report.html"
        if not html_template_path.exists():
            with open(html_template_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
    
    async def generate_daily_report(self, target_date: date = None) -> str:
        """生成每日報告"""
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"生成每日報告: {target_date}")
        
        config = ReportConfig(
            report_type="daily",
            start_date=target_date,
            end_date=target_date,
            include_charts=True,
            output_format="html"
        )
        
        return await self._generate_report(config)
    
    async def generate_weekly_report(self, end_date: date = None) -> str:
        """生成週報告"""
        if end_date is None:
            end_date = date.today()
        start_date = end_date - timedelta(days=6)
        
        logger.info(f"生成週報告: {start_date} 到 {end_date}")
        
        config = ReportConfig(
            report_type="weekly",
            start_date=start_date,
            end_date=end_date,
            include_charts=True,
            output_format="html"
        )
        
        return await self._generate_report(config)
    
    async def generate_monthly_report(self, year: int = None, month: int = None) -> str:
        """生成月報告"""
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        logger.info(f"生成月報告: {year}年{month}月")
        
        config = ReportConfig(
            report_type="monthly",
            start_date=start_date,
            end_date=end_date,
            include_charts=True,
            output_format="html"
        )
        
        return await self._generate_report(config)
    
    async def _generate_report(self, config: ReportConfig) -> str:
        """生成報告的核心方法"""
        # 收集數據
        data = await self._collect_report_data(config)
        
        # 生成圖表
        charts = []
        if config.include_charts:
            charts = await self._generate_charts(data, config)
        
        # 準備模板數據
        template_data = await self._prepare_template_data(data, charts, config)
        
        # 渲染報告
        if config.output_format == "html":
            return await self._render_html_report(template_data, config)
        elif config.output_format == "json":
            return await self._render_json_report(template_data, config)
        else:
            raise ValueError(f"不支援的輸出格式: {config.output_format}")
    
    async def _collect_report_data(self, config: ReportConfig) -> Dict[str, Any]:
        """收集報告數據"""
        data = {
            "period": {
                "start": config.start_date,
                "end": config.end_date,
                "type": config.report_type
            },
            "generation_metrics": await self._get_generation_metrics(config),
            "cost_metrics": await self._get_cost_metrics(config),
            "performance_metrics": await self._get_performance_metrics(config),
            "daily_breakdown": await self._get_daily_breakdown(config)
        }
        
        return data
    
    async def _get_generation_metrics(self, config: ReportConfig) -> GenerationMetrics:
        """獲取生成指標"""
        # 模擬數據 - 在實際實作中應該從資料庫查詢
        total_videos = 45
        successful = 42
        failed = 3
        
        return GenerationMetrics(
            total_videos=total_videos,
            successful_generations=successful,
            failed_generations=failed,
            total_cost=67.50,
            average_cost_per_video=1.50,
            platforms_distribution={"tiktok": 20, "instagram": 15, "youtube": 10},
            quality_distribution={"high": 15, "medium": 25, "low": 5},
            generation_time_stats={"avg": 180, "min": 120, "max": 300}
        )
    
    async def _get_cost_metrics(self, config: ReportConfig) -> Dict[str, Any]:
        """獲取成本指標"""
        if not self.cost_tracker:
            return self._get_mock_cost_metrics()
        
        try:
            if config.report_type == "daily":
                summary = await self.cost_tracker.get_daily_summary(config.start_date)
                return {
                    "total_cost": summary.total_cost,
                    "api_calls_count": summary.api_calls_count,
                    "providers_breakdown": summary.providers_breakdown,
                    "operations_breakdown": summary.operations_breakdown,
                    "budget_status": {
                        "limit": summary.budget_limit,
                        "remaining": summary.budget_remaining,
                        "usage_percent": (summary.total_cost / summary.budget_limit) * 100
                    }
                }
            else:
                # 週報告或月報告
                weekly_report = await self.cost_tracker.get_weekly_report()
                return {
                    "total_cost": weekly_report["total_cost"],
                    "api_calls_count": weekly_report["total_calls"],
                    "average_daily_cost": weekly_report["average_daily_cost"],
                    "daily_breakdown": weekly_report["daily_stats"]
                }
        except Exception as e:
            logger.error(f"獲取成本指標失敗: {e}")
            return self._get_mock_cost_metrics()
    
    def _get_mock_cost_metrics(self) -> Dict[str, Any]:
        """獲取模擬成本指標"""
        return {
            "total_cost": 67.50,
            "api_calls_count": 450,
            "providers_breakdown": {
                "openai": 35.20,
                "stability_ai": 22.80,
                "elevenlabs": 9.50
            },
            "operations_breakdown": {
                "text_generation": 35.20,
                "image_generation": 22.80,
                "voice_synthesis": 9.50
            },
            "budget_status": {
                "limit": 100.0,
                "remaining": 32.50,
                "usage_percent": 67.5
            }
        }
    
    async def _get_performance_metrics(self, config: ReportConfig) -> Dict[str, Any]:
        """獲取效能指標"""
        # 模擬效能數據
        return {
            "avg_generation_time": 180,  # 秒
            "success_rate": 93.3,  # 百分比
            "error_rate": 6.7,
            "throughput": 15,  # 影片/小時
            "resource_usage": {
                "cpu_avg": 65,
                "memory_avg": 78,
                "disk_usage": 45
            }
        }
    
    async def _get_daily_breakdown(self, config: ReportConfig) -> List[Dict[str, Any]]:
        """獲取每日明細"""
        breakdown = []
        current_date = config.start_date
        
        while current_date <= config.end_date:
            # 模擬每日數據
            breakdown.append({
                "date": current_date.isoformat(),
                "video_count": 15,
                "success_rate": 95.0,
                "total_cost": 22.50,
                "avg_cost": 1.50,
                "success_rate_class": "status-success" if 95.0 >= 90 else "status-warning"
            })
            current_date += timedelta(days=1)
        
        return breakdown
    
    async def _generate_charts(self, data: Dict[str, Any], config: ReportConfig) -> List[Dict[str, str]]:
        """生成圖表"""
        charts = []
        charts_dir = self.reports_dir / "charts" / f"{config.report_type}_{datetime.now().strftime('%Y%m%d')}"
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 成本分布圖
            if config.include_cost_analysis:
                cost_chart = await self._create_cost_distribution_chart(
                    data["cost_metrics"], 
                    charts_dir
                )
                charts.append(cost_chart)
                
                # 每日成本趨勢圖
                if config.report_type != "daily":
                    trend_chart = await self._create_cost_trend_chart(
                        data["daily_breakdown"],
                        charts_dir
                    )
                    charts.append(trend_chart)
            
            # 生成統計圖表
            generation_chart = await self._create_generation_stats_chart(
                data["generation_metrics"],
                charts_dir
            )
            charts.append(generation_chart)
            
            # 平台分布圖
            platform_chart = await self._create_platform_distribution_chart(
                data["generation_metrics"].platforms_distribution,
                charts_dir
            )
            charts.append(platform_chart)
            
        except Exception as e:
            logger.error(f"生成圖表失敗: {e}")
        
        return charts
    
    async def _create_cost_distribution_chart(self, cost_data: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
        """創建成本分布圖"""
        providers = cost_data.get("providers_breakdown", {})
        
        if not providers:
            return {"title": "成本分布", "path": "", "error": "無數據"}
        
        plt.figure(figsize=(10, 6))
        plt.pie(providers.values(), labels=providers.keys(), autopct='%1.1f%%', startangle=90)
        plt.title('API 供應商成本分布')
        
        chart_path = output_dir / "cost_distribution.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            "title": "API 供應商成本分布",
            "path": str(chart_path.relative_to(self.reports_dir))
        }
    
    async def _create_cost_trend_chart(self, daily_data: List[Dict[str, Any]], output_dir: Path) -> Dict[str, str]:
        """創建成本趨勢圖"""
        if not daily_data:
            return {"title": "成本趨勢", "path": "", "error": "無數據"}
        
        dates = [item["date"] for item in daily_data]
        costs = [item["total_cost"] for item in daily_data]
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, costs, marker='o', linewidth=2, markersize=6)
        plt.title('每日成本趨勢')
        plt.xlabel('日期')
        plt.ylabel('成本 (USD)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        chart_path = output_dir / "cost_trend.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            "title": "每日成本趨勢",
            "path": str(chart_path.relative_to(self.reports_dir))
        }
    
    async def _create_generation_stats_chart(self, metrics: GenerationMetrics, output_dir: Path) -> Dict[str, str]:
        """創建生成統計圖表"""
        labels = ['成功', '失敗']
        sizes = [metrics.successful_generations, metrics.failed_generations]
        colors = ['#28a745', '#dc3545']
        
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('影片生成成功率')
        
        chart_path = output_dir / "generation_success_rate.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            "title": "影片生成成功率",
            "path": str(chart_path.relative_to(self.reports_dir))
        }
    
    async def _create_platform_distribution_chart(self, platforms: Dict[str, int], output_dir: Path) -> Dict[str, str]:
        """創建平台分布圖表"""
        if not platforms:
            return {"title": "平台分布", "path": "", "error": "無數據"}
        
        plt.figure(figsize=(10, 6))
        plt.bar(platforms.keys(), platforms.values(), color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        plt.title('各平台影片數量分布')
        plt.xlabel('平台')
        plt.ylabel('影片數量')
        
        for i, v in enumerate(platforms.values()):
            plt.text(i, v + 0.5, str(v), ha='center', va='bottom')
        
        chart_path = output_dir / "platform_distribution.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            "title": "各平台影片數量分布",
            "path": str(chart_path.relative_to(self.reports_dir))
        }
    
    async def _prepare_template_data(self, data: Dict[str, Any], charts: List[Dict[str, str]], config: ReportConfig) -> Dict[str, Any]:
        """準備模板數據"""
        metrics = data["generation_metrics"]
        cost_data = data["cost_metrics"]
        
        # 關鍵指標
        key_metrics = [
            {
                "value": str(metrics.total_videos),
                "label": "總影片數",
                "status_class": "status-success"
            },
            {
                "value": f"{(metrics.successful_generations/metrics.total_videos)*100:.1f}%",
                "label": "成功率",
                "status_class": "status-success" if metrics.successful_generations/metrics.total_videos > 0.9 else "status-warning"
            },
            {
                "value": f"${cost_data['total_cost']:.2f}",
                "label": "總成本",
                "status_class": "status-success"
            },
            {
                "value": f"${metrics.average_cost_per_video:.2f}",
                "label": "平均成本/影片",
                "status_class": "status-success"
            }
        ]
        
        # 成本分析
        cost_breakdown = []
        if "providers_breakdown" in cost_data:
            total_cost = cost_data["total_cost"]
            for provider, amount in cost_data["providers_breakdown"].items():
                cost_breakdown.append({
                    "category": provider,
                    "amount": amount,
                    "percentage": (amount / total_cost) * 100 if total_cost > 0 else 0,
                    "trend": "↗️",
                    "trend_class": "status-success"
                })
        
        return {
            "report_title": f"{config.report_type.title()} 報告",
            "report_period": f"{config.start_date} 至 {config.end_date}",
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "key_metrics": key_metrics,
            "cost_analysis": config.include_cost_analysis,
            "cost_charts": [chart for chart in charts if "cost" in chart.get("title", "").lower()],
            "generation_charts": [chart for chart in charts if "generation" in chart.get("title", "").lower() or "platform" in chart.get("title", "").lower()],
            "cost_breakdown": cost_breakdown,
            "detailed_data": data["daily_breakdown"]
        }
    
    async def _render_html_report(self, template_data: Dict[str, Any], config: ReportConfig) -> str:
        """渲染 HTML 報告"""
        template = self.jinja_env.get_template("report.html")
        html_content = template.render(**template_data)
        
        # 保存報告
        report_filename = f"{config.report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = self.reports_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML 報告已生成: {report_path}")
        return str(report_path)
    
    async def _render_json_report(self, template_data: Dict[str, Any], config: ReportConfig) -> str:
        """渲染 JSON 報告"""
        # 保存報告
        report_filename = f"{config.report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.reports_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"JSON 報告已生成: {report_path}")
        return str(report_path)


async def main():
    """主函數 - 測試報告生成器"""
    generator = ReportGenerator()
    
    print("=== 報告生成器測試 ===")
    
    # 生成每日報告
    daily_report = await generator.generate_daily_report()
    print(f"每日報告: {daily_report}")
    
    # 生成週報告
    weekly_report = await generator.generate_weekly_report()
    print(f"週報告: {weekly_report}")
    
    # 生成月報告
    monthly_report = await generator.generate_monthly_report()
    print(f"月報告: {monthly_report}")


if __name__ == "__main__":
    asyncio.run(main())