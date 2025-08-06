"""
追蹤資料收集器
負責收集、儲存和管理追蹤資料
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from .tracer import TraceContext, tracer

logger = logging.getLogger(__name__)


class TraceCollector:
    """追蹤資料收集器"""

    def __init__(
        self,
        storage_path: str = "/data/data/com.termux/files/home/myProject/traces",
        max_memory_traces: int = 10000,
        batch_size: int = 100,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.max_memory_traces = max_memory_traces
        self.batch_size = batch_size

        # 內存中的追蹤資料
        self.memory_traces = deque(maxlen=max_memory_traces)
        self.trace_index = {}  # trace_id -> trace_data

        # 批處理隊列
        self.pending_writes = deque()

        # 統計資訊
        self.stats = {
            "total_traces": 0,
            "total_spans": 0,
            "error_traces": 0,
            "traces_by_service": defaultdict(int),
            "traces_by_operation": defaultdict(int),
            "last_updated": datetime.utcnow(),
        }

        # 啟動後台任務
        self._background_task = None
        self.start_background_tasks()

    def start_background_tasks(self):
        """啟動後台任務"""
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(self._background_worker())

    async def collect_trace(self, trace_data: Dict[str, Any]):
        """收集追蹤資料"""
        try:
            # 驗證追蹤資料
            if not self._validate_trace_data(trace_data):
                logger.warning("無效的追蹤資料，跳過收集")
                return

            # 豐富追蹤資料
            enriched_data = self._enrich_trace_data(trace_data)

            # 添加到內存
            self.memory_traces.append(enriched_data)
            self.trace_index[enriched_data["trace_id"]] = enriched_data

            # 添加到批處理隊列
            self.pending_writes.append(enriched_data)

            # 更新統計
            self._update_stats(enriched_data)

            logger.debug(f"收集追蹤: {enriched_data['trace_id']}")

        except Exception as e:
            logger.error(f"收集追蹤資料失敗: {e}")

    async def collect_span(self, span_context: TraceContext):
        """收集 Span 資料"""
        span_data = {
            "trace_id": span_context.trace_id,
            "span_id": span_context.span_id,
            "parent_span_id": span_context.parent_span_id,
            "service_name": span_context.service_name,
            "created_at": span_context.created_at.isoformat(),
            "attributes": span_context.attributes,
            "type": "span",
        }

        # 從追蹤器獲取額外的 Span 資訊
        span_info = tracer.get_span_info(span_context.span_id)
        if span_info:
            span_data.update(
                {
                    "operation_name": span_info.get("name"),
                    "start_time": span_info.get("start_time"),
                    "end_time": span_info.get("end_time"),
                    "duration": span_info.get("duration"),
                    "status": span_info.get("status"),
                    "error": span_info.get("error"),
                }
            )

        await self.collect_trace(span_data)

    def _validate_trace_data(self, trace_data: Dict[str, Any]) -> bool:
        """驗證追蹤資料的完整性"""
        required_fields = ["trace_id", "span_id", "service_name"]
        return all(field in trace_data for field in required_fields)

    def _enrich_trace_data(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """豐富追蹤資料"""
        enriched = trace_data.copy()

        # 添加收集時間戳
        enriched["collected_at"] = datetime.utcnow().isoformat()

        # 添加元數據
        enriched["metadata"] = {"collector_version": "1.0.0", "environment": "production"}

        # 計算額外指標
        if "start_time" in enriched and "end_time" in enriched:
            enriched["duration_ms"] = round(
                (enriched["end_time"] - enriched["start_time"]) * 1000, 2
            )

        # 分類操作類型
        operation_name = enriched.get("operation_name", "")
        enriched["operation_category"] = self._categorize_operation(operation_name)

        return enriched

    def _categorize_operation(self, operation_name: str) -> str:
        """分類操作類型"""
        operation_name = operation_name.lower()

        if "http" in operation_name or operation_name.startswith(("get", "post", "put", "delete")):
            return "http"
        elif "db" in operation_name or "query" in operation_name:
            return "database"
        elif "celery" in operation_name or "task" in operation_name:
            return "async_task"
        elif "cache" in operation_name or "redis" in operation_name:
            return "cache"
        elif "file" in operation_name or "io" in operation_name:
            return "io"
        else:
            return "other"

    def _update_stats(self, trace_data: Dict[str, Any]):
        """更新統計資訊"""
        self.stats["total_traces"] += 1
        self.stats["last_updated"] = datetime.utcnow()

        if trace_data.get("type") == "span":
            self.stats["total_spans"] += 1

        if trace_data.get("status") == "error" or trace_data.get("error"):
            self.stats["error_traces"] += 1

        service_name = trace_data.get("service_name", "unknown")
        self.stats["traces_by_service"][service_name] += 1

        operation_category = trace_data.get("operation_category", "unknown")
        self.stats["traces_by_operation"][operation_category] += 1

    async def _background_worker(self):
        """後台工作任務"""
        while True:
            try:
                # 批量寫入追蹤資料
                await self._flush_pending_writes()

                # 清理過期資料
                await self._cleanup_old_traces()

                # 清理追蹤器快取
                tracer.clear_cache()

                # 等待下一次執行
                await asyncio.sleep(30)  # 每30秒執行一次

            except Exception as e:
                logger.error(f"後台工作任務錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時等待更長時間

    async def _flush_pending_writes(self):
        """批量寫入待處理的追蹤資料"""
        if not self.pending_writes:
            return

        batch = []
        batch_count = 0

        while self.pending_writes and batch_count < self.batch_size:
            batch.append(self.pending_writes.popleft())
            batch_count += 1

        if batch:
            await self._write_traces_batch(batch)
            logger.debug(f"批量寫入 {len(batch)} 條追蹤資料")

    async def _write_traces_batch(self, traces: List[Dict[str, Any]]):
        """批量寫入追蹤資料到檔案"""
        try:
            # 按日期組織檔案
            today = datetime.utcnow().strftime("%Y-%m-%d")
            file_path = self.storage_path / f"traces_{today}.jsonl"

            async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
                for trace in traces:
                    line = json.dumps(trace, ensure_ascii=False) + "\n"
                    await f.write(line)

        except Exception as e:
            logger.error(f"寫入追蹤資料失敗: {e}")
            # 將失敗的追蹤資料重新加入隊列
            self.pending_writes.extendleft(reversed(traces))

    async def _cleanup_old_traces(self):
        """清理過期的追蹤資料檔案"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)  # 保留7天

            for file_path in self.storage_path.glob("traces_*.jsonl"):
                # 從檔案名提取日期
                try:
                    date_str = file_path.stem.split("_")[1]
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        file_path.unlink()
                        logger.info(f"刪除過期追蹤檔案: {file_path}")

                except Exception as e:
                    logger.warning(f"解析追蹤檔案日期失敗: {file_path}, {e}")

        except Exception as e:
            logger.error(f"清理過期追蹤檔案失敗: {e}")

    async def get_traces(
        self,
        trace_id: Optional[str] = None,
        service_name: Optional[str] = None,
        operation_category: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """查詢追蹤資料"""
        traces = []

        # 從內存中查詢
        for trace in reversed(self.memory_traces):
            if len(traces) >= limit:
                break

            if self._match_filters(
                trace, trace_id, service_name, operation_category, start_time, end_time
            ):
                traces.append(trace)

        return traces

    def _match_filters(
        self,
        trace: Dict[str, Any],
        trace_id: Optional[str],
        service_name: Optional[str],
        operation_category: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> bool:
        """檢查追蹤是否匹配過濾條件"""
        if trace_id and trace.get("trace_id") != trace_id:
            return False

        if service_name and trace.get("service_name") != service_name:
            return False

        if operation_category and trace.get("operation_category") != operation_category:
            return False

        if start_time or end_time:
            trace_time_str = trace.get("collected_at")
            if trace_time_str:
                trace_time = datetime.fromisoformat(trace_time_str.replace("Z", "+00:00"))

                if start_time and trace_time < start_time:
                    return False

                if end_time and trace_time > end_time:
                    return False

        return True

    async def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """根據 trace_id 獲取追蹤資料"""
        return self.trace_index.get(trace_id)

    def get_stats(self) -> Dict[str, Any]:
        """獲取收集器統計資訊"""
        stats = self.stats.copy()
        stats["memory_traces_count"] = len(self.memory_traces)
        stats["pending_writes_count"] = len(self.pending_writes)
        return stats

    async def export_traces(
        self, output_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> int:
        """導出追蹤資料"""
        exported_count = 0

        try:
            # 確定要導出的檔案
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                current_dt = start_dt
                source_files = []

                while current_dt <= end_dt:
                    file_path = (
                        self.storage_path / f"traces_{current_dt.strftime('%Y-%m-%d')}.jsonl"
                    )
                    if file_path.exists():
                        source_files.append(file_path)
                    current_dt += timedelta(days=1)
            else:
                source_files = list(self.storage_path.glob("traces_*.jsonl"))

            # 合併導出
            async with aiofiles.open(output_path, "w", encoding="utf-8") as output_file:
                for source_file in source_files:
                    async with aiofiles.open(source_file, "r", encoding="utf-8") as input_file:
                        async for line in input_file:
                            await output_file.write(line)
                            exported_count += 1

            logger.info(f"導出了 {exported_count} 條追蹤資料到 {output_path}")
            return exported_count

        except Exception as e:
            logger.error(f"導出追蹤資料失敗: {e}")
            return 0

    async def close(self):
        """關閉收集器"""
        # 停止後台任務
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        # 刷新所有待處理的寫入
        await self._flush_pending_writes()

        logger.info("追蹤資料收集器已關閉")


# 全域收集器實例
trace_collector = TraceCollector()
