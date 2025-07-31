#!/usr/bin/env python3
"""
業務指標收集器
收集和記錄業務相關的關鍵效能指標 (KPIs)
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import threading
from enum import Enum

# Prometheus metrics (optional dependency)
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from ..logging.structured_logger import get_logger

logger = get_logger(__name__)

class MetricType(Enum):
    """指標類型枚舉"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class BusinessMetricDefinition:
    """業務指標定義"""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    unit: str = ""
    business_impact: str = "medium"  # low, medium, high, critical
    sla_target: str = ""
    
    def __post_init__(self):
        # 確保標籤是清單
        if isinstance(self.labels, str):
            self.labels = [self.labels]

@dataclass
class MetricRecord:
    """指標記錄"""
    name: str
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str = ""

class BusinessMetricsCollector:
    """業務指標收集器"""
    
    def __init__(self, metrics_definitions_path: Optional[str] = None):
        self.metrics_definitions: Dict[str, BusinessMetricDefinition] = {}
        self.prometheus_metrics: Dict[str, Any] = {}
        self.fallback_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.metrics_lock = threading.Lock()
        
        # 載入指標定義
        if metrics_definitions_path:
            self.load_metrics_definitions(metrics_definitions_path)
        else:
            self._create_default_metrics()
        
        # 初始化 Prometheus 指標
        self._initialize_prometheus_metrics()
    
    def load_metrics_definitions(self, file_path: str):
        """從 JSON 文件載入指標定義"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                definitions_data = json.load(f)
            
            for name, definition in definitions_data.items():
                self.metrics_definitions[name] = BusinessMetricDefinition(
                    name=name,
                    type=MetricType(definition['type']),
                    description=definition['description'],
                    labels=definition.get('labels', []),
                    unit=definition.get('unit', ''),
                    business_impact=definition.get('business_impact', 'medium'),
                    sla_target=definition.get('sla_target', '')
                )
            
            logger.info(f"Loaded {len(self.metrics_definitions)} business metrics definitions")
            
        except Exception as e:
            logger.error(f"Failed to load metrics definitions: {e}")
            self._create_default_metrics()
    
    def _create_default_metrics(self):
        """建立預設業務指標定義"""
        default_metrics = {
            "video_generation_count": BusinessMetricDefinition(
                name="video_generation_count",
                type=MetricType.COUNTER,
                description="Total number of videos generated",
                labels=["status", "video_type", "platform", "user_tier"],
                unit="count",
                business_impact="high",
                sla_target="> 1000 per day"
            ),
            "user_engagement_rate": BusinessMetricDefinition(
                name="user_engagement_rate",
                type=MetricType.GAUGE,
                description="User engagement rate across all platforms",
                labels=["platform", "content_type", "user_segment"],
                unit="percentage",
                business_impact="high",
                sla_target="> 5%"
            ),
            "content_generation_time": BusinessMetricDefinition(
                name="content_generation_time",
                type=MetricType.HISTOGRAM,
                description="Time taken to generate content",
                labels=["content_type", "quality_level"],
                unit="seconds",
                business_impact="medium",
                sla_target="< 300 seconds (95th percentile)"
            ),
            "revenue_per_user": BusinessMetricDefinition(
                name="revenue_per_user",
                type=MetricType.GAUGE,
                description="Average revenue per user",
                labels=["user_tier", "billing_period"],
                unit="currency",
                business_impact="critical",
                sla_target="> $10 per month"
            )
        }
        
        self.metrics_definitions.update(default_metrics)
    
    def _initialize_prometheus_metrics(self):
        """初始化 Prometheus 指標"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, using fallback metrics storage")
            return
        
        for name, definition in self.metrics_definitions.items():
            try:
                if definition.type == MetricType.COUNTER:
                    self.prometheus_metrics[name] = Counter(
                        name=name,
                        documentation=definition.description,
                        labelnames=definition.labels
                    )
                elif definition.type == MetricType.GAUGE:
                    self.prometheus_metrics[name] = Gauge(
                        name=name,
                        documentation=definition.description,
                        labelnames=definition.labels
                    )
                elif definition.type == MetricType.HISTOGRAM:
                    self.prometheus_metrics[name] = Histogram(
                        name=name,
                        documentation=definition.description,
                        labelnames=definition.labels
                    )
                elif definition.type == MetricType.SUMMARY:
                    self.prometheus_metrics[name] = Summary(
                        name=name,
                        documentation=definition.description,
                        labelnames=definition.labels
                    )
                
                logger.debug(f"Initialized Prometheus metric: {name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Prometheus metric {name}: {e}")
    
    def record_metric(self, name: str, value: Union[int, float], 
                     labels: Optional[Dict[str, str]] = None):
        """記錄業務指標"""
        if name not in self.metrics_definitions:
            logger.warning(f"Unknown metric: {name}")
            return
        
        if labels is None:
            labels = {}
        
        definition = self.metrics_definitions[name]
        
        # 記錄到 Prometheus
        if PROMETHEUS_AVAILABLE and name in self.prometheus_metrics:
            try:
                prometheus_metric = self.prometheus_metrics[name]
                
                if definition.type == MetricType.COUNTER:
                    if labels:
                        prometheus_metric.labels(**labels).inc(value)
                    else:
                        prometheus_metric.inc(value)
                        
                elif definition.type == MetricType.GAUGE:
                    if labels:
                        prometheus_metric.labels(**labels).set(value)
                    else:
                        prometheus_metric.set(value)
                        
                elif definition.type in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
                    if labels:
                        prometheus_metric.labels(**labels).observe(value)
                    else:
                        prometheus_metric.observe(value)
                        
            except Exception as e:
                logger.error(f"Failed to record Prometheus metric {name}: {e}")
        
        # 後備儲存
        with self.metrics_lock:
            record = MetricRecord(
                name=name,
                value=value,
                labels=labels,
                timestamp=datetime.utcnow(),
                unit=definition.unit
            )
            
            self.fallback_metrics[name].append(record)
        
        # 記錄日誌
        logger.info(
            f"Business metric recorded: {name} = {value}",
            metric_name=name,
            metric_value=value,
            metric_labels=labels,
            business_impact=definition.business_impact,
            sla_target=definition.sla_target
        )
    
    def increment_counter(self, name: str, amount: Union[int, float] = 1, 
                         labels: Optional[Dict[str, str]] = None):
        """增加計數器指標"""
        self.record_metric(name, amount, labels)
    
    def set_gauge(self, name: str, value: Union[int, float], 
                  labels: Optional[Dict[str, str]] = None):
        """設定儀表指標"""
        self.record_metric(name, value, labels)
    
    def observe_histogram(self, name: str, value: Union[int, float], 
                         labels: Optional[Dict[str, str]] = None):
        """觀察直方圖指標"""
        self.record_metric(name, value, labels)
    
    def get_metric_summary(self, name: str, 
                          time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """獲取指標摘要"""
        if name not in self.metrics_definitions:
            return {}
        
        cutoff_time = datetime.utcnow() - time_window
        
        with self.metrics_lock:
            records = [
                record for record in self.fallback_metrics[name]
                if record.timestamp > cutoff_time
            ]
        
        if not records:
            return {"name": name, "records_count": 0}
        
        values = [record.value for record in records]
        definition = self.metrics_definitions[name]
        
        summary = {
            "name": name,
            "type": definition.type.value,
            "description": definition.description,
            "business_impact": definition.business_impact,
            "sla_target": definition.sla_target,
            "records_count": len(records),
            "time_window_hours": time_window.total_seconds() / 3600,
            "latest_value": values[-1] if values else None,
            "unit": definition.unit
        }
        
        if definition.type == MetricType.COUNTER:
            summary["total"] = sum(values)
            summary["rate_per_hour"] = sum(values) / (time_window.total_seconds() / 3600)
        
        elif definition.type == MetricType.GAUGE:
            summary["current_value"] = values[-1] if values else None
            summary["min_value"] = min(values)
            summary["max_value"] = max(values)
            summary["avg_value"] = sum(values) / len(values)
        
        elif definition.type in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            summary["min"] = sorted_values[0]
            summary["max"] = sorted_values[-1]
            summary["avg"] = sum(values) / count
            summary["p50"] = sorted_values[count // 2]
            summary["p90"] = sorted_values[int(count * 0.9)]
            summary["p95"] = sorted_values[int(count * 0.95)]
            summary["p99"] = sorted_values[int(count * 0.99)]
        
        return summary
    
    def get_all_metrics_summary(self, 
                               time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """獲取所有指標摘要"""
        summaries = {}
        
        for name in self.metrics_definitions.keys():
            summaries[name] = self.get_metric_summary(name, time_window)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_window_hours": time_window.total_seconds() / 3600,
            "metrics": summaries,
            "total_metrics": len(summaries)
        }
    
    def get_critical_metrics_status(self) -> Dict[str, Any]:
        """獲取關鍵指標狀態"""
        critical_metrics = {
            name: definition for name, definition in self.metrics_definitions.items()
            if definition.business_impact in ["high", "critical"]
        }
        
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "critical_metrics_count": len(critical_metrics),
            "metrics_status": {}
        }
        
        for name, definition in critical_metrics.items():
            summary = self.get_metric_summary(name, timedelta(hours=1))
            
            metric_status = {
                "name": name,
                "business_impact": definition.business_impact,
                "sla_target": definition.sla_target,
                "records_count": summary.get("records_count", 0),
                "latest_value": summary.get("latest_value"),
                "status": "unknown"
            }
            
            # 簡單的 SLA 狀態判斷（可以根據實際需求擴展）
            if summary.get("records_count", 0) > 0:
                if definition.business_impact == "critical":
                    metric_status["status"] = "active"
                else:
                    metric_status["status"] = "active"
            else:
                metric_status["status"] = "no_data"
            
            status["metrics_status"][name] = metric_status
        
        return status

# 全域業務指標收集器實例
business_metrics = BusinessMetricsCollector(
    "/data/data/com.termux/files/home/myProject/auto_generate_video_fold6/monitoring/business_metrics/metrics_definition.json"
)

# 便捷函數
def record_video_generation(status: str, video_type: str, platform: str, user_tier: str = "free"):
    """記錄影片生成指標"""
    business_metrics.increment_counter(
        "video_generation_count",
        labels={
            "status": status,
            "video_type": video_type,
            "platform": platform,
            "user_tier": user_tier
        }
    )

def record_user_engagement(platform: str, engagement_rate: float, 
                          content_type: str = "video", user_segment: str = "general"):
    """記錄用戶參與度"""
    business_metrics.set_gauge(
        "user_engagement_rate",
        engagement_rate,
        labels={
            "platform": platform,
            "content_type": content_type,
            "user_segment": user_segment
        }
    )

def record_content_generation_time(duration_seconds: float, content_type: str, 
                                  quality_level: str = "standard"):
    """記錄內容生成時間"""
    business_metrics.observe_histogram(
        "content_generation_time",
        duration_seconds,
        labels={
            "content_type": content_type,
            "quality_level": quality_level
        }
    )

def record_revenue_per_user(revenue: float, user_tier: str, billing_period: str = "monthly"):
    """記錄每用戶收入"""
    business_metrics.set_gauge(
        "revenue_per_user",
        revenue,
        labels={
            "user_tier": user_tier,
            "billing_period": billing_period
        }
    )

async def collect_system_metrics():
    """收集系統層級的業務指標"""
    try:
        # 這個函數可以定期執行以收集系統指標
        # 例如：用戶數量、存儲使用量、處理任務數等
        
        logger.info("Collecting system-level business metrics")
        
        # 示例：記錄系統可用性（這裡使用模擬數據）
        import random
        system_availability = random.uniform(99.0, 100.0)
        business_metrics.set_gauge(
            "system_availability",
            system_availability,
            labels={"service": "overall", "region": "default"}
        )
        
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")

class MetricsReporter:
    """指標報告器"""
    
    def __init__(self, collector: BusinessMetricsCollector):
        self.collector = collector
        self.logger = get_logger("metrics_reporter")
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日指標報告"""
        report = {
            "report_type": "daily",
            "timestamp": datetime.utcnow().isoformat(),
            "date": datetime.utcnow().date().isoformat(),
            "summary": self.collector.get_all_metrics_summary(timedelta(days=1)),
            "critical_status": self.collector.get_critical_metrics_status()
        }
        
        self.logger.info("Generated daily metrics report")
        return report
    
    async def generate_hourly_report(self) -> Dict[str, Any]:
        """生成每小時指標報告"""
        report = {
            "report_type": "hourly",
            "timestamp": datetime.utcnow().isoformat(),
            "hour": datetime.utcnow().strftime("%Y-%m-%d %H:00"),
            "summary": self.collector.get_all_metrics_summary(timedelta(hours=1)),
            "critical_status": self.collector.get_critical_metrics_status()
        }
        
        self.logger.info("Generated hourly metrics report")
        return report

# 全域指標報告器
metrics_reporter = MetricsReporter(business_metrics)