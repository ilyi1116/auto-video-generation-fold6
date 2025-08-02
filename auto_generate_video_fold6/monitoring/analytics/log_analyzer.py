"""
日誌分析與告警系統
實時分析日誌數據，生成洞察和告警
"""

import asyncio
import json
import logging
import os
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import redis
from elasticsearch import AsyncElasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """告警數據結構"""

    id: str
    type: str
    severity: str
    title: str
    message: str
    service: str
    timestamp: datetime
    data: Dict[str, Any]
    resolved: bool = False


class LogAnalyzer:
    """日誌分析器"""

    def __init__(
        self,
        elasticsearch_url: str = "http://elasticsearch:9200",
        redis_url: str = "redis://redis:6379",
    ):
        self.es = AsyncElasticsearch([elasticsearch_url])
        self.redis = redis.from_url(redis_url)

        # 告警閾值設定
        self.thresholds = {
            "error_rate": 0.05,  # 5% 錯誤率
            "response_time_p95": 2000,  # 95th percentile 回應時間
            "failed_login_attempts": 10,  # 10 次失敗登入
            "memory_usage": 0.85,  # 85% 記憶體使用率
            "cpu_usage": 0.80,  # 80% CPU 使用率
            "disk_usage": 0.90,  # 90% 磁碟使用率
        }

        # 分析間隔
        self.analysis_interval = 60  # 60 秒

        # 告警歷史
        self.alert_history = []

    async def start_analysis(self):
        """開始日誌分析"""
        logger.info("Starting log analysis...")

        while True:
            try:
                # 執行各種分析
                await self.analyze_error_patterns()
                await self.analyze_performance_metrics()
                await self.analyze_security_events()
                await self.analyze_business_metrics()
                await self.analyze_system_health()

                # 生成洞察報告
                await self.generate_insights()

                # 清理舊數據
                await self.cleanup_old_data()

                logger.info("Analysis cycle completed")
                await asyncio.sleep(self.analysis_interval)

            except Exception as e:
                logger.error(f"Analysis error: {e}")
                await asyncio.sleep(30)

    async def analyze_error_patterns(self):
        """分析錯誤模式"""
        now = datetime.utcnow()
        since = now - timedelta(minutes=5)

        # 查詢錯誤日誌
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"level": "ERROR"}},
                        {"range": {"@timestamp": {"gte": since.isoformat()}}},
                    ]
                }
            },
            "aggs": {
                "error_by_service": {"terms": {"field": "service.keyword"}},
                "error_by_type": {"terms": {"field": "error_type.keyword"}},
            },
        }

        try:
            result = await self.es.search(
                index="auto-video-logs-*", body=query, size=0
            )

            total_errors = result["hits"]["total"]["value"]

            # 檢查錯誤率
            if total_errors > 50:  # 5分鐘內超過50個錯誤
                alert = Alert(
                    id=f"error_spike_{int(time.time())}",
                    type="error_spike",
                    severity="high",
                    title="High Error Rate Detected",
                    message=f"Detected {total_errors} errors in the last 5 minutes",
                    service="system",
                    timestamp=now,
                    data={"error_count": total_errors},
                )
                await self.send_alert(alert)

            # 分析錯誤分佈
            services_with_errors = result["aggregations"]["error_by_service"][
                "buckets"
            ]
            for service_bucket in services_with_errors:
                service = service_bucket["key"]
                error_count = service_bucket["doc_count"]

                if error_count > 20:  # 單一服務錯誤過多
                    alert = Alert(
                        id=f"service_errors_{service}_{int(time.time())}",
                        type="service_errors",
                        severity="medium",
                        title=f"High Error Count in {service}",
                        message=f"Service {service} has {error_count} errors in 5 minutes",
                        service=service,
                        timestamp=now,
                        data={"error_count": error_count},
                    )
                    await self.send_alert(alert)

        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")

    async def analyze_performance_metrics(self):
        """分析效能指標"""
        now = datetime.utcnow()
        since = now - timedelta(minutes=10)

        # 查詢效能日誌
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "duration_ms"}},
                        {"range": {"@timestamp": {"gte": since.isoformat()}}},
                    ]
                }
            },
            "aggs": {
                "avg_response_time": {"avg": {"field": "duration_ms"}},
                "p95_response_time": {
                    "percentiles": {"field": "duration_ms", "percents": [95]}
                },
                "slow_requests": {
                    "filter": {"range": {"duration_ms": {"gte": 5000}}}
                },
            },
        }

        try:
            result = await self.es.search(
                index="auto-video-logs-*", body=query, size=0
            )

            p95_time = result["aggregations"]["p95_response_time"]["values"][
                "95.0"
            ]
            slow_requests = result["aggregations"]["slow_requests"][
                "doc_count"
            ]

            # 檢查回應時間
            if p95_time > self.thresholds["response_time_p95"]:
                alert = Alert(
                    id=f"slow_response_{int(time.time())}",
                    type="performance",
                    severity="medium",
                    title="Slow Response Time",
                    message=f"95th percentile response time is {p95_time:.2f}ms",
                    service="system",
                    timestamp=now,
                    data={"p95_response_time": p95_time},
                )
                await self.send_alert(alert)

            # 檢查慢請求
            if slow_requests > 10:
                alert = Alert(
                    id=f"slow_requests_{int(time.time())}",
                    type="performance",
                    severity="medium",
                    title="High Number of Slow Requests",
                    message=f"Found {slow_requests} requests taking >5 seconds",
                    service="system",
                    timestamp=now,
                    data={"slow_requests_count": slow_requests},
                )
                await self.send_alert(alert)

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")

    async def analyze_security_events(self):
        """分析安全事件"""
        now = datetime.utcnow()
        since = now - timedelta(minutes=15)

        # 查詢安全事件
        security_queries = [
            # 失敗登入
            {
                "name": "failed_logins",
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"message": "failed login"}},
                            {
                                "range": {
                                    "@timestamp": {"gte": since.isoformat()}
                                }
                            },
                        ]
                    }
                },
            },
            # 未授權訪問
            {
                "name": "unauthorized_access",
                "query": {
                    "bool": {
                        "must": [
                            {"terms": {"status_code": [401, 403]}},
                            {
                                "range": {
                                    "@timestamp": {"gte": since.isoformat()}
                                }
                            },
                        ]
                    }
                },
            },
            # 可疑活動
            {
                "name": "suspicious_activity",
                "query": {
                    "bool": {
                        "must": [
                            {
                                "regexp": {
                                    "message": ".*(attack|breach|injection|xss).*"
                                }
                            },
                            {
                                "range": {
                                    "@timestamp": {"gte": since.isoformat()}
                                }
                            },
                        ]
                    }
                },
            },
        ]

        for sec_query in security_queries:
            try:
                result = await self.es.search(
                    index="auto-video-logs-*",
                    body={"query": sec_query["query"]},
                    size=100,
                )

                event_count = result["hits"]["total"]["value"]
                events = result["hits"]["hits"]

                if event_count > 0:
                    # 分析 IP 地址模式
                    ip_counter = Counter()
                    for event in events:
                        source = event["_source"]
                        ip = source.get("ip_address") or source.get(
                            "source_ip"
                        )
                        if ip:
                            ip_counter[ip] += 1

                    # 檢查是否有來自同一 IP 的大量事件
                    for ip, count in ip_counter.items():
                        if count >= self.thresholds.get(
                            "failed_login_attempts", 10
                        ):
                            alert = Alert(
                                id=f"security_{sec_query['name']}_{ip}_{int(time.time())}",
                                type="security",
                                severity="high",
                                title=f"Suspicious Activity from {ip}",
                                message=f"Detected {count} {sec_query['name']} from IP {ip}",
                                service="security",
                                timestamp=now,
                                data={
                                    "source_ip": ip,
                                    "event_type": sec_query["name"],
                                    "event_count": count,
                                },
                            )
                            await self.send_alert(alert)

            except Exception as e:
                logger.error(
                    f"Security analysis failed for {sec_query['name']}: {e}"
                )

    async def analyze_business_metrics(self):
        """分析業務指標"""
        now = datetime.utcnow()
        since = now - timedelta(hours=1)

        # 分析用戶註冊
        user_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"event_type": "business"}},
                        {"match": {"message": "user_registration"}},
                        {"range": {"@timestamp": {"gte": since.isoformat()}}},
                    ]
                }
            }
        }

        # 分析影片生成
        video_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"event_type": "business"}},
                        {"match": {"message": "video_generation"}},
                        {"range": {"@timestamp": {"gte": since.isoformat()}}},
                    ]
                }
            },
            "aggs": {
                "status_breakdown": {"terms": {"field": "status.keyword"}}
            },
        }

        try:
            # 用戶註冊分析
            user_result = await self.es.search(
                index="auto-video-logs-*", body=user_query, size=0
            )
            user_registrations = user_result["hits"]["total"]["value"]

            # 影片生成分析
            video_result = await self.es.search(
                index="auto-video-logs-*", body=video_query, size=0
            )
            total_generations = video_result["hits"]["total"]["value"]

            # 計算成功率
            status_buckets = video_result["aggregations"]["status_breakdown"][
                "buckets"
            ]
            success_count = 0
            for bucket in status_buckets:
                if bucket["key"] == "success":
                    success_count = bucket["doc_count"]

            success_rate = (
                success_count / total_generations
                if total_generations > 0
                else 1.0
            )

            # 儲存業務指標到 Redis
            metrics = {
                "user_registrations_1h": user_registrations,
                "video_generations_1h": total_generations,
                "video_success_rate_1h": success_rate,
                "timestamp": now.isoformat(),
            }

            self.redis.setex(
                "business_metrics", 3600, json.dumps(metrics)
            )  # 1小時過期

            # 檢查業務異常
            if success_rate < 0.8 and total_generations > 10:
                alert = Alert(
                    id=f"low_video_success_rate_{int(time.time())}",
                    type="business",
                    severity="medium",
                    title="Low Video Generation Success Rate",
                    message=f"Video generation success rate is {success_rate:.2%}",
                    service="video-service",
                    timestamp=now,
                    data={
                        "success_rate": success_rate,
                        "total_generations": total_generations,
                    },
                )
                await self.send_alert(alert)

        except Exception as e:
            logger.error(f"Business metrics analysis failed: {e}")

    async def analyze_system_health(self):
        """分析系統健康狀況"""
        now = datetime.utcnow()
        since = now - timedelta(minutes=5)

        # 查詢系統指標
        system_query = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "memory_usage"}},
                        {"range": {"@timestamp": {"gte": since.isoformat()}}},
                    ]
                }
            },
            "aggs": {
                "avg_memory": {"avg": {"field": "memory_usage"}},
                "avg_cpu": {"avg": {"field": "cpu_usage"}},
                "services": {
                    "terms": {"field": "service.keyword"},
                    "aggs": {
                        "avg_memory": {"avg": {"field": "memory_usage"}},
                        "avg_cpu": {"avg": {"field": "cpu_usage"}},
                    },
                },
            },
        }

        try:
            result = await self.es.search(
                index="auto-video-logs-*", body=system_query, size=0
            )

            if "aggregations" in result:
                avg_memory = result["aggregations"]["avg_memory"]["value"]
                avg_cpu = result["aggregations"]["avg_cpu"]["value"]

                # 檢查系統資源使用率
                if avg_memory and avg_memory > self.thresholds["memory_usage"]:
                    alert = Alert(
                        id=f"high_memory_{int(time.time())}",
                        type="system",
                        severity="medium",
                        title="High Memory Usage",
                        message=f"Average memory usage is {avg_memory:.2%}",
                        service="system",
                        timestamp=now,
                        data={"memory_usage": avg_memory},
                    )
                    await self.send_alert(alert)

                if avg_cpu and avg_cpu > self.thresholds["cpu_usage"]:
                    alert = Alert(
                        id=f"high_cpu_{int(time.time())}",
                        type="system",
                        severity="medium",
                        title="High CPU Usage",
                        message=f"Average CPU usage is {avg_cpu:.2%}",
                        service="system",
                        timestamp=now,
                        data={"cpu_usage": avg_cpu},
                    )
                    await self.send_alert(alert)

        except Exception as e:
            logger.error(f"System health analysis failed: {e}")

    async def generate_insights(self):
        """生成洞察報告"""
        now = datetime.utcnow()

        # 生成每日洞察
        if now.hour == 9 and now.minute < 5:  # 每天早上9點
            await self.generate_daily_insights()

        # 生成每周洞察
        if now.weekday() == 0 and now.hour == 9:  # 每周一早上9點
            await self.generate_weekly_insights()

    async def generate_daily_insights(self):
        """生成每日洞察報告"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_of_yesterday = yesterday.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_yesterday = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        insights = {
            "date": yesterday.date().isoformat(),
            "summary": {},
            "top_errors": [],
            "performance_trends": {},
            "security_summary": {},
            "business_metrics": {},
        }

        # 儲存洞察到 Redis
        self.redis.setex(
            f"daily_insights_{yesterday.date().isoformat()}",
            7 * 24 * 3600,  # 保存7天
            json.dumps(insights),
        )

        logger.info(f"Generated daily insights for {yesterday.date()}")

    async def send_alert(self, alert: Alert):
        """發送告警"""
        # 檢查是否為重複告警
        alert_key = f"alert_{alert.type}_{alert.service}"
        if self.redis.exists(alert_key):
            return  # 跳過重複告警

        # 設定告警冷卻時間
        self.redis.setex(alert_key, 300, "1")  # 5分鐘冷卻

        # 儲存告警
        alert_data = {
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "service": alert.service,
            "timestamp": alert.timestamp.isoformat(),
            "data": alert.data,
            "resolved": alert.resolved,
        }

        # 儲存到 Redis
        self.redis.lpush("alerts", json.dumps(alert_data))
        self.redis.ltrim("alerts", 0, 999)  # 保留最近1000個告警

        # 儲存到 Elasticsearch
        try:
            await self.es.index(
                index=f"alerts-{datetime.utcnow().strftime('%Y.%m.%d')}",
                body=alert_data,
            )
        except Exception as e:
            logger.error(f"Failed to index alert: {e}")

        # 發送到告警管理器 (這裡可以整合到 Alertmanager)
        logger.warning(f"ALERT: {alert.title} - {alert.message}")

        self.alert_history.append(alert)

    async def cleanup_old_data(self):
        """清理舊數據"""
        # 清理7天前的日誌索引
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_index = f"auto-video-logs-{cutoff_date.strftime('%Y.%m.%d')}"

        try:
            await self.es.indices.delete(index=old_index, ignore=[404])
        except Exception as e:
            logger.debug(f"Failed to delete old index {old_index}: {e}")

    async def close(self):
        """關閉連接"""
        await self.es.close()
        self.redis.close()


class AlertManager:
    """告警管理器"""

    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis = redis.from_url(redis_url)

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """獲取活躍告警"""
        alerts = self.redis.lrange("alerts", 0, 99)
        return [json.loads(alert) for alert in alerts]

    def resolve_alert(self, alert_id: str):
        """解決告警"""
        alerts = self.redis.lrange("alerts", 0, -1)
        for i, alert_data in enumerate(alerts):
            alert = json.loads(alert_data)
            if alert["id"] == alert_id:
                alert["resolved"] = True
                self.redis.lset("alerts", i, json.dumps(alert))
                break


async def main():
    """主函數"""
    analyzer = LogAnalyzer()

    try:
        await analyzer.start_analysis()
    except KeyboardInterrupt:
        logger.info("Shutting down log analyzer...")
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
