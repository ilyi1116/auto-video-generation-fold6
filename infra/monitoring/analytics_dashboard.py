#!/usr/bin/env python3
"""
分析儀表板 - 實時數據分析和可視化界面
提供互動式數據分析功能
"""

import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """分析儀表板"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.app = dash.Dash(__name__)
        self.data_cache = {}
        self.last_update = None

        try:
            from monitoring.cost_tracker import get_cost_tracker

            self.cost_tracker = get_cost_tracker(config_manager)
        except ImportError:
            self.cost_tracker = None
            logger.warning("成本追蹤器不可用")

        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self):
        """設置儀表板布局"""
        self.app.layout = html.Div(
            [
                # 標題
                html.Div(
                    [
                        html.H1(
                            "🎬 Auto Video Generation 分析儀表板",
                            className="dashboard-title",
                        ),
                        html.P(
                            "實時監控和數據分析",
                            className="dashboard-subtitle",
                        ),
                        html.Div(
                            [
                                html.Span("最後更新: ", className="update-label"),
                                html.Span(
                                    id="last-update-time",
                                    className="update-time",
                                ),
                            ],
                            className="update-info",
                        ),
                    ],
                    className="header",
                ),
                # 控制面板
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("時間範圍:", className="control-label"),
                                dcc.Dropdown(
                                    id="time-range-dropdown",
                                    options=[
                                        {"label": "今天", "value": "today"},
                                        {
                                            "label": "昨天",
                                            "value": "yesterday",
                                        },
                                        {"label": "過去7天", "value": "7days"},
                                        {
                                            "label": "過去30天",
                                            "value": "30days",
                                        },
                                        {
                                            "label": "本月",
                                            "value": "this_month",
                                        },
                                        {
                                            "label": "上月",
                                            "value": "last_month",
                                        },
                                    ],
                                    value="7days",
                                    className="control-dropdown",
                                ),
                            ],
                            className="control-group",
                        ),
                        html.Div(
                            [
                                html.Label("數據類型:", className="control-label"),
                                dcc.Dropdown(
                                    id="data-type-dropdown",
                                    options=[
                                        {"label": "成本分析", "value": "cost"},
                                        {
                                            "label": "生成統計",
                                            "value": "generation",
                                        },
                                        {
                                            "label": "效能指標",
                                            "value": "performance",
                                        },
                                        {
                                            "label": "錯誤分析",
                                            "value": "errors",
                                        },
                                    ],
                                    value="cost",
                                    className="control-dropdown",
                                ),
                            ],
                            className="control-group",
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "刷新數據",
                                    id="refresh-button",
                                    className="refresh-button",
                                ),
                                html.Button(
                                    "匯出報告",
                                    id="export-button",
                                    className="export-button",
                                ),
                            ],
                            className="button-group",
                        ),
                    ],
                    className="controls",
                ),
                # 關鍵指標卡片
                html.Div(
                    [html.Div(id="metrics-cards", className="metrics-grid")],
                    className="metrics-section",
                ),
                # 主要圖表區域
                html.Div(
                    [
                        html.Div(
                            [dcc.Graph(id="main-chart")],
                            className="chart-container",
                        ),
                        html.Div(
                            [dcc.Graph(id="secondary-chart")],
                            className="chart-container",
                        ),
                    ],
                    className="charts-section",
                ),
                # 詳細數據表格
                html.Div(
                    [
                        html.H3("詳細數據", className="section-title"),
                        html.Div(id="data-table"),
                    ],
                    className="table-section",
                ),
                # 隱藏的 div 用於存儲數據
                html.Div(id="data-store", style={"display": "none"}),
            ]
        )

        # 添加 CSS 樣式
        self.app.index_string = """
        <!DOCTYPE html>
        <html>
        <head>
            {%metas%}
            <title>Auto Video Analytics Dashboard</title>
            {%favicon%}
            {%css%}
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0; padding: 0; background: #f8f9fa;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 30px; text-align: center;
                }
                .dashboard-title { margin: 0; font-size: 2.5rem; }
                .dashboard-subtitle { margin: 10px 0; opacity: 0.9; }
                .update-info { margin-top: 15px; font-size: 0.9rem; }
                .controls {
                    background: white; padding: 20px; margin: 20px;
                    border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    display: flex; gap: 20px; align-items: end; flex-wrap: wrap;
                }
                .control-group { min-width: 200px; }
                .control-label { font-weight: 600; margin-bottom: 5px; display: block; }
                .control-dropdown { width: 100%; }
                .button-group { display: flex; gap: 10px; }
                .refresh-button, .export-button {
                    padding: 10px 20px; border: none; border-radius: 5px;
                    font-weight: 600; cursor: pointer; transition: all 0.2s;
                }
                .refresh-button { background: #28a745; color: white; }
                .refresh-button:hover { background: #218838; }
                .export-button { background: #17a2b8; color: white; }
                .export-button:hover { background: #138496; }
                .metrics-section { margin: 20px; }
                .metrics-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                }
                .metric-card {
                    background: white; padding: 20px; border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;
                }
                .metric-value { font-size: 2rem; font-weight: bold; margin-bottom: 5px; }
                .metric-label { color: #666; font-size: 0.9rem; }
                .charts-section {
                    display: grid; grid-template-columns: 1fr 1fr;
                    gap: 20px; margin: 20px;
                }
                .chart-container {
                    background: white; border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px;
                }
                .table-section {
                    background: white; margin: 20px; padding: 20px;
                    border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .section-title { margin-top: 0; color: #333; }
                @media (max-width: 768px) {
                    .charts-section { grid-template-columns: 1fr; }
                    .controls { flex-direction: column; align-items: stretch; }
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
        </html>
        """

    def _setup_callbacks(self):
        """設置回調函數"""

        @self.app.callback(
            [
                Output("data-store", "children"),
                Output("last-update-time", "children"),
            ],
            [
                Input("time-range-dropdown", "value"),
                Input("data-type-dropdown", "value"),
                Input("refresh-button", "n_clicks"),
            ],
        )
        def update_data_store(time_range, data_type, n_clicks):
            """更新數據存儲"""
            try:
                data = asyncio.run(self._fetch_data(time_range, data_type))
                return [json.dumps(data), datetime.now().strftime("%H:%M:%S")]
            except Exception as e:
                logger.error(f"獲取數據失敗: {e}")
                return [json.dumps({}), "獲取失敗"]

        @self.app.callback(
            Output("metrics-cards", "children"),
            [Input("data-store", "children")],
        )
        def update_metrics_cards(data_json):
            """更新指標卡片"""
            try:
                data = json.loads(data_json) if data_json else {}
                return self._create_metrics_cards(data)
            except Exception as e:
                logger.error(f"更新指標卡片失敗: {e}")
                return []

        @self.app.callback(
            Output("main-chart", "figure"),
            [
                Input("data-store", "children"),
                Input("data-type-dropdown", "value"),
            ],
        )
        def update_main_chart(data_json, data_type):
            """更新主圖表"""
            try:
                data = json.loads(data_json) if data_json else {}
                return self._create_main_chart(data, data_type)
            except Exception as e:
                logger.error(f"更新主圖表失敗: {e}")
                return go.Figure()

        @self.app.callback(
            Output("secondary-chart", "figure"),
            [
                Input("data-store", "children"),
                Input("data-type-dropdown", "value"),
            ],
        )
        def update_secondary_chart(data_json, data_type):
            """更新次圖表"""
            try:
                data = json.loads(data_json) if data_json else {}
                return self._create_secondary_chart(data, data_type)
            except Exception as e:
                logger.error(f"更新次圖表失敗: {e}")
                return go.Figure()

        @self.app.callback(Output("data-table", "children"), [Input("data-store", "children")])
        def update_data_table(data_json):
            """更新數據表格"""
            try:
                data = json.loads(data_json) if data_json else {}
                return self._create_data_table(data)
            except Exception as e:
                logger.error(f"更新數據表格失敗: {e}")
                return html.P("數據載入失敗")

    async def _fetch_data(self, time_range: str, data_type: str) -> Dict[str, Any]:
        """獲取數據"""
        end_date = date.today()

        # 根據時間範圍計算開始日期
        if time_range == "today":
            start_date = end_date
        elif time_range == "yesterday":
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        elif time_range == "7days":
            start_date = end_date - timedelta(days=7)
        elif time_range == "30days":
            start_date = end_date - timedelta(days=30)
        elif time_range == "this_month":
            start_date = end_date.replace(day=1)
        elif time_range == "last_month":
            if end_date.month == 1:
                start_date = date(end_date.year - 1, 12, 1)
                end_date = date(end_date.year, 1, 1) - timedelta(days=1)
            else:
                start_date = date(end_date.year, end_date.month - 1, 1)
                end_date = date(end_date.year, end_date.month, 1) - timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=7)

        # 根據數據類型獲取相應數據
        if data_type == "cost":
            return await self._fetch_cost_data(start_date, end_date)
        elif data_type == "generation":
            return await self._fetch_generation_data(start_date, end_date)
        elif data_type == "performance":
            return await self._fetch_performance_data(start_date, end_date)
        elif data_type == "errors":
            return await self._fetch_error_data(start_date, end_date)
        else:
            return {}

    async def _fetch_cost_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """獲取成本數據"""
        if not self.cost_tracker:
            return self._get_mock_cost_data(start_date, end_date)

        try:
            if start_date == end_date:
                # 單日數據
                summary = await self.cost_tracker.get_daily_summary(start_date)
                return {
                    "type": "cost",
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "total_cost": summary.total_cost,
                    "api_calls": summary.api_calls_count,
                    "providers": summary.providers_breakdown,
                    "operations": summary.operations_breakdown,
                    "daily_data": [
                        {
                            "date": start_date.isoformat(),
                            "cost": summary.total_cost,
                            "calls": summary.api_calls_count,
                        }
                    ],
                }
            else:
                # 多日數據
                weekly_report = await self.cost_tracker.get_weekly_report()
                return {
                    "type": "cost",
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "total_cost": weekly_report["total_cost"],
                    "api_calls": weekly_report["total_calls"],
                    "average_daily": weekly_report["average_daily_cost"],
                    "daily_data": [
                        {
                            "date": date_str,
                            "cost": stats["cost"],
                            "calls": stats["calls"],
                        }
                        for date_str, stats in weekly_report["daily_stats"].items()
                    ],
                }
        except Exception as e:
            logger.error(f"獲取成本數據失敗: {e}")
            return self._get_mock_cost_data(start_date, end_date)

    def _get_mock_cost_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """獲取模擬成本數據"""
        import random

        daily_data = []
        current_date = start_date
        total_cost = 0
        total_calls = 0

        while current_date <= end_date:
            daily_cost = random.uniform(15, 35)
            daily_calls = random.randint(30, 80)

            daily_data.append(
                {
                    "date": current_date.isoformat(),
                    "cost": daily_cost,
                    "calls": daily_calls,
                }
            )

            total_cost += daily_cost
            total_calls += daily_calls
            current_date += timedelta(days=1)

        return {
            "type": "cost",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_cost": total_cost,
            "api_calls": total_calls,
            "providers": {
                "OpenAI": total_cost * 0.6,
                "Stability AI": total_cost * 0.25,
                "ElevenLabs": total_cost * 0.15,
            },
            "operations": {
                "文字生成": total_cost * 0.6,
                "圖像生成": total_cost * 0.25,
                "語音合成": total_cost * 0.15,
            },
            "daily_data": daily_data,
        }

    async def _fetch_generation_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """獲取生成數據（模擬）"""
        import random

        daily_data = []
        current_date = start_date
        total_videos = 0
        total_success = 0

        while current_date <= end_date:
            videos = random.randint(10, 25)
            success = int(videos * random.uniform(0.85, 0.98))

            daily_data.append(
                {
                    "date": current_date.isoformat(),
                    "videos": videos,
                    "success": success,
                    "success_rate": ((success / videos) * 100 if videos > 0 else 0),
                }
            )

            total_videos += videos
            total_success += success
            current_date += timedelta(days=1)

        return {
            "type": "generation",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_videos": total_videos,
            "total_success": total_success,
            "success_rate": ((total_success / total_videos) * 100 if total_videos > 0 else 0),
            "platforms": {
                "TikTok": int(total_videos * 0.45),
                "Instagram": int(total_videos * 0.35),
                "YouTube": int(total_videos * 0.20),
            },
            "daily_data": daily_data,
        }

    async def _fetch_performance_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """獲取效能數據（模擬）"""
        import random

        daily_data = []
        current_date = start_date

        while current_date <= end_date:
            daily_data.append(
                {
                    "date": current_date.isoformat(),
                    "avg_time": random.uniform(120, 300),
                    "cpu_usage": random.uniform(40, 80),
                    "memory_usage": random.uniform(50, 85),
                    "disk_usage": random.uniform(30, 70),
                }
            )
            current_date += timedelta(days=1)

        return {
            "type": "performance",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "daily_data": daily_data,
        }

    async def _fetch_error_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """獲取錯誤數據（模擬）"""
        import random

        error_types = ["API錯誤", "網路超時", "資源不足", "配置錯誤", "其他"]
        error_data = {error_type: random.randint(0, 10) for error_type in error_types}

        return {
            "type": "errors",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_errors": sum(error_data.values()),
            "error_types": error_data,
        }

    def _create_metrics_cards(self, data: Dict[str, Any]) -> List[html.Div]:
        """創建指標卡片"""
        if not data:
            return [html.P("無數據")]

        data_type = data.get("type", "")
        cards = []

        if data_type == "cost":
            cards = [
                html.Div(
                    [
                        html.Div(
                            f"${data.get('total_cost', 0):.2f}",
                            className="metric-value",
                        ),
                        html.Div("總成本", className="metric-label"),
                    ],
                    className="metric-card",
                ),
                html.Div(
                    [
                        html.Div(
                            str(data.get("api_calls", 0)),
                            className="metric-value",
                        ),
                        html.Div("API 呼叫次數", className="metric-label"),
                    ],
                    className="metric-card",
                ),
                html.Div(
                    [
                        html.Div(
                            f"${data.get('total_cost', 0) / max(data.get('api_calls', 1), 1):.4f}",
                            className="metric-value",
                        ),
                        html.Div("平均成本/呼叫", className="metric-label"),
                    ],
                    className="metric-card",
                ),
            ]

        elif data_type == "generation":
            cards = [
                html.Div(
                    [
                        html.Div(
                            str(data.get("total_videos", 0)),
                            className="metric-value",
                        ),
                        html.Div("總影片數", className="metric-label"),
                    ],
                    className="metric-card",
                ),
                html.Div(
                    [
                        html.Div(
                            f"{data.get('success_rate', 0):.1f}%",
                            className="metric-value",
                        ),
                        html.Div("成功率", className="metric-label"),
                    ],
                    className="metric-card",
                ),
                html.Div(
                    [
                        html.Div(
                            str(data.get("total_success", 0)),
                            className="metric-value",
                        ),
                        html.Div("成功生成", className="metric-label"),
                    ],
                    className="metric-card",
                ),
            ]

        return cards

    def _create_main_chart(self, data: Dict[str, Any], data_type: str) -> go.Figure:
        """創建主圖表"""
        if not data:
            return go.Figure().add_annotation(text="無數據", x=0.5, y=0.5, showarrow=False)

        if data_type == "cost":
            # 成本趨勢圖
            daily_data = data.get("daily_data", [])
            if daily_data:
                df = pd.DataFrame(daily_data)
                fig = px.line(
                    df,
                    x="date",
                    y="cost",
                    title="每日成本趨勢",
                    labels={"cost": "成本 (USD)", "date": "日期"},
                )
                fig.update_layout(hovermode="x unified")
                return fig

        elif data_type == "generation":
            # 生成統計圖
            daily_data = data.get("daily_data", [])
            if daily_data:
                df = pd.DataFrame(daily_data)
                fig = px.bar(
                    df,
                    x="date",
                    y="videos",
                    title="每日影片生成數量",
                    labels={"videos": "影片數量", "date": "日期"},
                )
                return fig

        elif data_type == "performance":
            # 效能趨勢圖
            daily_data = data.get("daily_data", [])
            if daily_data:
                df = pd.DataFrame(daily_data)
                fig = px.line(
                    df,
                    x="date",
                    y="avg_time",
                    title="平均生成時間趨勢",
                    labels={"avg_time": "平均時間 (秒)", "date": "日期"},
                )
                return fig

        return go.Figure()

    def _create_secondary_chart(self, data: Dict[str, Any], data_type: str) -> go.Figure:
        """創建次圖表"""
        if not data:
            return go.Figure().add_annotation(text="無數據", x=0.5, y=0.5, showarrow=False)

        if data_type == "cost":
            # 供應商分布圖
            providers = data.get("providers", {})
            if providers:
                fig = px.pie(
                    values=list(providers.values()),
                    names=list(providers.keys()),
                    title="API 供應商成本分布",
                )
                return fig

        elif data_type == "generation":
            # 平台分布圖
            platforms = data.get("platforms", {})
            if platforms:
                fig = px.pie(
                    values=list(platforms.values()),
                    names=list(platforms.keys()),
                    title="平台影片分布",
                )
                return fig

        elif data_type == "errors":
            # 錯誤類型分布
            error_types = data.get("error_types", {})
            if error_types:
                fig = px.bar(
                    x=list(error_types.keys()),
                    y=list(error_types.values()),
                    title="錯誤類型分布",
                )
                return fig

        return go.Figure()

    def _create_data_table(self, data: Dict[str, Any]) -> html.Div:
        """創建數據表格"""
        if not data:
            return html.P("無數據")

        daily_data = data.get("daily_data", [])
        if not daily_data:
            return html.P("無詳細數據")

        # 創建表格標題
        headers = list(daily_data[0].keys()) if daily_data else []

        # 創建表格
        table_header = [html.Thead([html.Tr([html.Th(h) for h in headers])])]
        table_body = [
            html.Tbody([html.Tr([html.Td(row.get(h, "")) for h in headers]) for row in daily_data])
        ]

        return html.Table(table_header + table_body, className="table")

    def run(self, host: str = "127.0.0.1", port: int = 8050, debug: bool = False):
        """運行儀表板"""
        logger.info(f"啟動分析儀表板: http://{host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)


async def main():
    """主函數"""
    dashboard = AnalyticsDashboard()
    dashboard.run(debug=True)


if __name__ == "__main__":
    try:
        dashboard = AnalyticsDashboard()
        dashboard.run(host="127.0.0.1", port=8050, debug=False)
    except Exception as e:
        logger.error(f"啟動儀表板失敗: {e}")
        print("請安裝必要的依賴: pip install dash plotly pandas")
