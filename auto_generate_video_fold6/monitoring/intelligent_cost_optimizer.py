#!/usr/bin/env python3
"""
智能成本優化引擎
達到 AWS Cost Explorer / Google Cloud Cost Management 級別的成本控制
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import redis
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class CostCategory(Enum):
    AI_INFERENCE = "ai_inference"
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    THIRD_PARTY_API = "third_party_api"


class OptimizationStrategy(Enum):
    PERFORMANCE_FIRST = "performance_first"
    COST_FIRST = "cost_first"
    BALANCED = "balanced"
    CUSTOM = "custom"


@dataclass
class CostRecord:
    """成本記錄"""

    timestamp: datetime
    service: str
    category: CostCategory
    amount: float
    currency: str
    user_id: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class CostPrediction:
    """成本預測"""

    period: str
    predicted_amount: float
    confidence_interval: Tuple[float, float]
    trend: str  # "increasing", "decreasing", "stable"
    factors: Dict[str, float]


@dataclass
class OptimizationRecommendation:
    """優化建議"""

    recommendation_id: str
    category: CostCategory
    description: str
    potential_savings: float
    implementation_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    estimated_impact_days: int
    action_items: List[str]


class CostDataCollector:
    """成本數據收集器"""

    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=7)
        self.cost_records = []

    async def record_cost(
        self,
        service: str,
        category: CostCategory,
        amount: float,
        currency: str = "USD",
        user_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        """記錄成本數據"""

        record = CostRecord(
            timestamp=datetime.utcnow(),
            service=service,
            category=category,
            amount=amount,
            currency=currency,
            user_id=user_id,
            metadata=metadata or {},
        )

        # 存儲到 Redis
        cost_key = f"cost_record:{datetime.utcnow().strftime('%Y-%m-%d')}"
        cost_data = asdict(record)
        cost_data["timestamp"] = record.timestamp.isoformat()

        self.redis_client.lpush(cost_key, json.dumps(cost_data))
        self.redis_client.expire(cost_key, timedelta(days=365))  # 保留1年

        logger.info(f"記錄成本: {service} - ${amount:.4f}")

    async def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        service: Optional[str] = None,
        category: Optional[CostCategory] = None,
    ) -> List[CostRecord]:
        """獲取成本數據"""

        records = []
        current_date = start_date

        while current_date <= end_date:
            cost_key = f"cost_record:{current_date.strftime('%Y-%m-%d')}"
            daily_records = self.redis_client.lrange(cost_key, 0, -1)

            for record_json in daily_records:
                record_data = json.loads(record_json)
                record_data["timestamp"] = datetime.fromisoformat(record_data["timestamp"])
                record_data["category"] = CostCategory(record_data["category"])

                record = CostRecord(**record_data)

                # 應用篩選條件
                if service and record.service != service:
                    continue
                if category and record.category != category:
                    continue

                records.append(record)

            current_date += timedelta(days=1)

        return sorted(records, key=lambda x: x.timestamp)


class CostPredictor:
    """成本預測器 - 使用機器學習預測未來成本"""

    def __init__(self, cost_collector: CostDataCollector):
        self.cost_collector = cost_collector
        self.models = {}
        self.feature_scalers = {}

    async def train_prediction_models(self):
        """訓練預測模型"""

        # 獲取歷史數據
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # 90天歷史數據

        cost_data = await self.cost_collector.get_cost_data(start_date, end_date)

        if len(cost_data) < 30:  # 需要至少30個數據點
            logger.warning("歷史數據不足，無法訓練預測模型")
            return

        # 為每個服務類別訓練模型
        categories = set(record.category for record in cost_data)

        for category in categories:
            await self._train_category_model(cost_data, category)

        logger.info(f"完成 {len(categories)} 個類別的預測模型訓練")

    async def _train_category_model(self, cost_data: List[CostRecord], category: CostCategory):
        """為特定類別訓練預測模型"""

        # 篩選類別數據
        category_data = [record for record in cost_data if record.category == category]

        if len(category_data) < 10:
            return

        # 準備特徵和標籤
        df = pd.DataFrame(
            [
                {
                    "timestamp": record.timestamp,
                    "amount": record.amount,
                    "hour": record.timestamp.hour,
                    "day_of_week": record.timestamp.weekday(),
                    "day_of_month": record.timestamp.day,
                    "month": record.timestamp.month,
                }
                for record in category_data
            ]
        )

        # 創建時間序列特徵
        df = df.sort_values("timestamp")
        df["days_since_start"] = (df["timestamp"] - df["timestamp"].min()).dt.days
        df["rolling_mean_7d"] = df["amount"].rolling(window=7, min_periods=1).mean()
        df["rolling_std_7d"] = df["amount"].rolling(window=7, min_periods=1).std().fillna(0)

        # 準備特徵矩陣
        features = [
            "days_since_start",
            "hour",
            "day_of_week",
            "day_of_month",
            "month",
            "rolling_mean_7d",
            "rolling_std_7d",
        ]

        X = df[features].values
        y = df["amount"].values

        # 訓練隨機森林模型
        model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, min_samples_split=5
        )

        model.fit(X, y)

        # 存儲模型
        self.models[category] = model

        # 計算特徵重要性
        feature_importance = dict(zip(features, model.feature_importances_))
        logger.info(f"{category.value} 模型訓練完成，特徵重要性: {feature_importance}")

    async def predict_future_costs(
        self, category: CostCategory, days_ahead: int = 30
    ) -> CostPrediction:
        """預測未來成本"""

        if category not in self.models:
            raise ValueError(f"未找到 {category.value} 的預測模型")

        model = self.models[category]

        # 生成未來時間點的特徵
        future_dates = [datetime.utcnow() + timedelta(days=i) for i in range(1, days_ahead + 1)]

        predictions = []

        for future_date in future_dates:
            # 構建特徵向量
            features = np.array(
                [
                    [
                        days_ahead,  # days_since_start (估算)
                        future_date.hour,
                        future_date.weekday(),
                        future_date.day,
                        future_date.month,
                        0.0,  # rolling_mean_7d (使用歷史平均)
                        0.0,  # rolling_std_7d (使用歷史平均)
                    ]
                ]
            )

            prediction = model.predict(features)[0]
            predictions.append(prediction)

        # 計算總預測成本
        total_predicted = sum(predictions)

        # 計算置信區間 (使用樹的標準差)
        # 這是簡化的置信區間計算
        std_dev = np.std(predictions)
        confidence_interval = (total_predicted - 1.96 * std_dev, total_predicted + 1.96 * std_dev)

        # 分析趋势
        trend = self._analyze_trend(predictions)

        # 分析影響因素
        factors = await self._analyze_cost_factors(category)

        return CostPrediction(
            period=f"{days_ahead} days",
            predicted_amount=total_predicted,
            confidence_interval=confidence_interval,
            trend=trend,
            factors=factors,
        )

    def _analyze_trend(self, predictions: List[float]) -> str:
        """分析成本趋势"""
        if len(predictions) < 7:
            return "stable"

        # 計算前後兩週的平均值
        first_week = np.mean(predictions[:7])
        last_week = np.mean(predictions[-7:])

        change_rate = (last_week - first_week) / first_week

        if change_rate > 0.1:
            return "increasing"
        elif change_rate < -0.1:
            return "decreasing"
        else:
            return "stable"

    async def _analyze_cost_factors(self, category: CostCategory) -> Dict[str, float]:
        """分析成本影響因素"""

        if category not in self.models:
            return {}

        model = self.models[category]

        # 獲取特徵重要性
        feature_names = [
            "days_since_start",
            "hour",
            "day_of_week",
            "day_of_month",
            "month",
            "rolling_mean_7d",
            "rolling_std_7d",
        ]

        return dict(zip(feature_names, model.feature_importances_))


class CostOptimizer:
    """成本優化器"""

    def __init__(self, cost_collector: CostDataCollector, cost_predictor: CostPredictor):
        self.cost_collector = cost_collector
        self.cost_predictor = cost_predictor
        self.optimization_rules = {}
        self._initialize_optimization_rules()

    def _initialize_optimization_rules(self):
        """初始化優化規則"""
        self.optimization_rules = {
            CostCategory.AI_INFERENCE: {
                "model_selection": {
                    "description": "選擇性價比最佳的AI模型",
                    "potential_savings_rate": 0.3,
                    "implementation_effort": "medium",
                },
                "batch_processing": {
                    "description": "批量處理AI請求以降低成本",
                    "potential_savings_rate": 0.2,
                    "implementation_effort": "low",
                },
                "caching": {
                    "description": "緩存AI推理結果",
                    "potential_savings_rate": 0.4,
                    "implementation_effort": "medium",
                },
            },
            CostCategory.COMPUTE: {
                "auto_scaling": {
                    "description": "實現智能自動擴展",
                    "potential_savings_rate": 0.25,
                    "implementation_effort": "medium",
                },
                "spot_instances": {
                    "description": "使用抢占式實例",
                    "potential_savings_rate": 0.6,
                    "implementation_effort": "high",
                },
                "resource_rightsizing": {
                    "description": "調整資源配置大小",
                    "potential_savings_rate": 0.2,
                    "implementation_effort": "low",
                },
            },
            CostCategory.STORAGE: {
                "data_lifecycle": {
                    "description": "實施數據生命週期管理",
                    "potential_savings_rate": 0.3,
                    "implementation_effort": "medium",
                },
                "compression": {
                    "description": "數據壓縮和去重",
                    "potential_savings_rate": 0.15,
                    "implementation_effort": "low",
                },
            },
        }

    async def generate_optimization_recommendations(
        self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    ) -> List[OptimizationRecommendation]:
        """生成優化建議"""

        recommendations = []

        # 獲取最近30天的成本數據
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        cost_data = await self.cost_collector.get_cost_data(start_date, end_date)

        # 按類別分析成本
        category_costs = {}
        for record in cost_data:
            if record.category not in category_costs:
                category_costs[record.category] = []
            category_costs[record.category].append(record.amount)

        # 為每個類別生成建議
        for category, costs in category_costs.items():
            total_cost = sum(costs)
            avg_daily_cost = total_cost / 30

            if category in self.optimization_rules:
                category_recommendations = await self._generate_category_recommendations(
                    category, total_cost, avg_daily_cost, strategy
                )
                recommendations.extend(category_recommendations)

        # 按潛在節省排序
        recommendations.sort(key=lambda x: x.potential_savings, reverse=True)

        return recommendations

    async def _generate_category_recommendations(
        self,
        category: CostCategory,
        total_cost: float,
        avg_daily_cost: float,
        strategy: OptimizationStrategy,
    ) -> List[OptimizationRecommendation]:
        """為特定類別生成優化建議"""

        recommendations = []
        rules = self.optimization_rules[category]

        for rule_name, rule_config in rules.items():
            # 計算潛在節省
            potential_savings = total_cost * rule_config["potential_savings_rate"]

            # 根據策略調整建議優先級
            if strategy == OptimizationStrategy.COST_FIRST:
                if potential_savings < total_cost * 0.1:  # 節省少於10%的跳過
                    continue
            elif strategy == OptimizationStrategy.PERFORMANCE_FIRST:
                if rule_config["implementation_effort"] == "high":
                    continue

            recommendation = OptimizationRecommendation(
                recommendation_id=f"{category.value}_{rule_name}_{int(datetime.utcnow().timestamp())}",
                category=category,
                description=rule_config["description"],
                potential_savings=potential_savings,
                implementation_effort=rule_config["implementation_effort"],
                risk_level=self._assess_risk_level(rule_name, category),
                estimated_impact_days=self._estimate_impact_days(
                    rule_config["implementation_effort"]
                ),
                action_items=self._generate_action_items(rule_name, category),
            )

            recommendations.append(recommendation)

        return recommendations

    def _assess_risk_level(self, rule_name: str, category: CostCategory) -> str:
        """評估風險等級"""
        high_risk_rules = ["spot_instances", "aggressive_caching"]
        medium_risk_rules = ["auto_scaling", "model_selection"]

        if rule_name in high_risk_rules:
            return "high"
        elif rule_name in medium_risk_rules:
            return "medium"
        else:
            return "low"

    def _estimate_impact_days(self, implementation_effort: str) -> int:
        """估算影響天數"""
        effort_to_days = {"low": 3, "medium": 7, "high": 14}
        return effort_to_days.get(implementation_effort, 7)

    def _generate_action_items(self, rule_name: str, category: CostCategory) -> List[str]:
        """生成行動項目"""
        action_templates = {
            "model_selection": [
                "分析各AI模型的成本效益比",
                "實施動態模型選擇邏輯",
                "設置模型性能監控",
            ],
            "batch_processing": ["設計批量處理API", "實施請求聚合邏輯", "優化批處理調度"],
            "caching": ["設計緩存策略", "實施緩存失效機制", "監控緩存命中率"],
            "auto_scaling": ["配置HPA規則", "設置性能閾值", "實施預測性擴展"],
        }

        return action_templates.get(rule_name, ["分析當前配置", "制定優化計劃", "實施並監控"])


class CostAnomalyDetector:
    """成本異常檢測器"""

    def __init__(self, cost_collector: CostDataCollector):
        self.cost_collector = cost_collector
        self.anomaly_threshold = 2.0  # 標準差倍數

    async def detect_anomalies(self, lookback_days: int = 7) -> List[Dict[str, Any]]:
        """檢測成本異常"""

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        cost_data = await self.cost_collector.get_cost_data(start_date, end_date)

        # 按服務分組
        service_costs = {}
        for record in cost_data:
            if record.service not in service_costs:
                service_costs[record.service] = []
            service_costs[record.service].append(
                {"timestamp": record.timestamp, "amount": record.amount}
            )

        anomalies = []

        for service, costs in service_costs.items():
            service_anomalies = await self._detect_service_anomalies(service, costs)
            anomalies.extend(service_anomalies)

        return anomalies

    async def _detect_service_anomalies(
        self, service: str, costs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測單個服務的成本異常"""

        if len(costs) < 5:  # 數據點太少無法檢測異常
            return []

        amounts = [cost["amount"] for cost in costs]
        mean_cost = np.mean(amounts)
        std_cost = np.std(amounts)

        if std_cost == 0:  # 標準差為0，無異常
            return []

        anomalies = []

        for cost in costs:
            z_score = abs(cost["amount"] - mean_cost) / std_cost

            if z_score > self.anomaly_threshold:
                anomaly = {
                    "service": service,
                    "timestamp": cost["timestamp"].isoformat(),
                    "amount": cost["amount"],
                    "expected_range": (
                        mean_cost - self.anomaly_threshold * std_cost,
                        mean_cost + self.anomaly_threshold * std_cost,
                    ),
                    "z_score": z_score,
                    "severity": "high" if z_score > 3.0 else "medium",
                }
                anomalies.append(anomaly)

        return anomalies


class BudgetManager:
    """預算管理器"""

    def __init__(self, cost_collector: CostDataCollector):
        self.cost_collector = cost_collector
        self.redis_client = redis.Redis(host="localhost", port=6379, db=8)

    async def set_budget(
        self,
        period: str,  # "daily", "weekly", "monthly"
        amount: float,
        category: Optional[CostCategory] = None,
        alert_thresholds: List[float] = None,
    ):
        """設置預算"""

        budget_config = {
            "period": period,
            "amount": amount,
            "category": category.value if category else "all",
            "alert_thresholds": alert_thresholds or [0.5, 0.8, 0.9],
            "created_at": datetime.utcnow().isoformat(),
        }

        budget_key = f"budget:{period}:{budget_config['category']}"
        self.redis_client.set(budget_key, json.dumps(budget_config))

        logger.info(f"設置 {period} 預算: ${amount} ({budget_config['category']})")

    async def check_budget_status(self) -> List[Dict[str, Any]]:
        """檢查預算狀態"""

        budget_keys = self.redis_client.keys("budget:*")
        budget_status = []

        for key in budget_keys:
            budget_data = json.loads(self.redis_client.get(key))

            # 計算當前期間的實際成本
            actual_cost = await self._calculate_period_cost(
                budget_data["period"],
                CostCategory(budget_data["category"]) if budget_data["category"] != "all" else None,
            )

            # 計算使用率
            usage_rate = actual_cost / budget_data["amount"]

            # 檢查警報閾值
            alerts = []
            for threshold in budget_data["alert_thresholds"]:
                if usage_rate >= threshold:
                    alerts.append(
                        {"threshold": threshold, "message": f"預算使用率達到 {threshold*100:.0f}%"}
                    )

            status = {
                "period": budget_data["period"],
                "category": budget_data["category"],
                "budget_amount": budget_data["amount"],
                "actual_cost": actual_cost,
                "usage_rate": usage_rate,
                "remaining_budget": budget_data["amount"] - actual_cost,
                "alerts": alerts,
                "status": self._determine_budget_status(usage_rate),
            }

            budget_status.append(status)

        return budget_status

    async def _calculate_period_cost(
        self, period: str, category: Optional[CostCategory] = None
    ) -> float:
        """計算期間成本"""

        end_date = datetime.utcnow()

        if period == "daily":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            days_since_monday = end_date.weekday()
            start_date = end_date - timedelta(days=days_since_monday)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"不支持的期間類型: {period}")

        cost_data = await self.cost_collector.get_cost_data(start_date, end_date, category=category)

        return sum(record.amount for record in cost_data)

    def _determine_budget_status(self, usage_rate: float) -> str:
        """確定預算狀態"""
        if usage_rate >= 1.0:
            return "exceeded"
        elif usage_rate >= 0.9:
            return "critical"
        elif usage_rate >= 0.8:
            return "warning"
        elif usage_rate >= 0.5:
            return "normal"
        else:
            return "healthy"


class IntelligentCostOptimizer:
    """智能成本優化引擎 - 主類"""

    def __init__(self):
        self.cost_collector = CostDataCollector()
        self.cost_predictor = CostPredictor(self.cost_collector)
        self.cost_optimizer = CostOptimizer(self.cost_collector, self.cost_predictor)
        self.anomaly_detector = CostAnomalyDetector(self.cost_collector)
        self.budget_manager = BudgetManager(self.cost_collector)

    async def initialize(self):
        """初始化優化引擎"""
        logger.info("正在初始化智能成本優化引擎...")

        # 訓練預測模型
        try:
            await self.cost_predictor.train_prediction_models()
            logger.info("成本預測模型訓練完成")
        except Exception as e:
            logger.warning(f"預測模型訓練失敗: {e}")

    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """運行綜合成本分析"""

        logger.info("開始綜合成本分析...")

        try:
            # 1. 預測分析
            predictions = {}
            for category in CostCategory:
                try:
                    prediction = await self.cost_predictor.predict_future_costs(category, 30)
                    predictions[category.value] = asdict(prediction)
                except Exception as e:
                    logger.warning(f"無法預測 {category.value} 的成本: {e}")

            # 2. 優化建議
            recommendations = await self.cost_optimizer.generate_optimization_recommendations()

            # 3. 異常檢測
            anomalies = await self.anomaly_detector.detect_anomalies()

            # 4. 預算狀態
            budget_status = await self.budget_manager.check_budget_status()

            # 5. 計算總體節省潛力
            total_potential_savings = sum(rec.potential_savings for rec in recommendations)

            analysis_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "predictions": predictions,
                "recommendations": [asdict(rec) for rec in recommendations],
                "anomalies": anomalies,
                "budget_status": budget_status,
                "total_potential_savings": total_potential_savings,
                "summary": {
                    "total_recommendations": len(recommendations),
                    "high_priority_recommendations": len(
                        [r for r in recommendations if r.potential_savings > 100]
                    ),
                    "anomalies_detected": len(anomalies),
                    "budgets_exceeded": len(
                        [b for b in budget_status if b["status"] == "exceeded"]
                    ),
                },
            }

            logger.info(f"綜合分析完成 - 潛在節省: ${total_potential_savings:.2f}")
            return analysis_result

        except Exception as e:
            logger.error(f"綜合分析失敗: {e}")
            raise


# 使用示例
async def main():
    """智能成本優化引擎使用示例"""

    optimizer = IntelligentCostOptimizer()
    await optimizer.initialize()

    # 模擬記錄一些成本數據
    await optimizer.cost_collector.record_cost(
        service="openai_gpt4",
        category=CostCategory.AI_INFERENCE,
        amount=25.50,
        metadata={"tokens": 10000, "model": "gpt-4"},
    )

    await optimizer.cost_collector.record_cost(
        service="stability_ai",
        category=CostCategory.AI_INFERENCE,
        amount=15.25,
        metadata={"images": 50, "resolution": "1024x1024"},
    )

    # 設置預算
    await optimizer.budget_manager.set_budget(
        period="monthly",
        amount=1000.0,
        category=CostCategory.AI_INFERENCE,
        alert_thresholds=[0.7, 0.85, 0.95],
    )

    # 運行綜合分析
    analysis = await optimizer.run_comprehensive_analysis()

    print("=== 智能成本優化分析報告 ===")
    print(f"總潛在節省: ${analysis['total_potential_savings']:.2f}")
    print(f"優化建議數量: {analysis['summary']['total_recommendations']}")
    print(f"檢測到異常: {analysis['summary']['anomalies_detected']}")
    print(f"預算超支: {analysis['summary']['budgets_exceeded']}")


if __name__ == "__main__":
    asyncio.run(main())
