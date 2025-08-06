"""
訊息佇列系統
支援服務間異步通訊、事件發布/訂閱和任務佇列
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """訊息優先級"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageStatus(Enum):
    """訊息狀態"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Message:
    """訊息模型"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5分鐘
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "topic": self.topic,
            "payload": self.payload,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """從字典創建訊息"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            topic=data.get("topic", ""),
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", MessagePriority.NORMAL.value)),
            created_at=data.get("created_at", time.time()),
            scheduled_at=data.get("scheduled_at"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 300),
            metadata=data.get("metadata", {}),
        )


class MessageHandler:
    """訊息處理器基類"""

    async def handle(self, message: Message) -> bool:
        """處理訊息，返回是否成功"""
        raise NotImplementedError


class MessageQueue:
    """訊息佇列管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_pool: Optional[redis.Redis] = None
        self.handlers: Dict[str, MessageHandler] = {}
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []

    async def start(self):
        """啟動訊息佇列"""
        self.redis_pool = redis.Redis.from_url(self.redis_url)

        # 測試Redis連接
        try:
            await self.redis_pool.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        self.running = True

        # 啟動工作者
        for i in range(3):  # 3個工作者
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)

        # 啟動調度器
        scheduler_task = asyncio.create_task(self._scheduler())
        self.worker_tasks.append(scheduler_task)

        logger.info("Message queue started")

    async def stop(self):
        """停止訊息佇列"""
        self.running = False

        # 取消所有工作者任務
        for task in self.worker_tasks:
            task.cancel()

        # 等待任務完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        # 關閉Redis連接
        if self.redis_pool:
            await self.redis_pool.close()

        logger.info("Message queue stopped")

    def register_handler(self, topic: str, handler: MessageHandler):
        """註冊訊息處理器"""
        self.handlers[topic] = handler
        logger.info(f"Registered handler for topic: {topic}")

    async def add_task(self, queue_name: str, task_data: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """添加任務到佇列"""
        message = Message(
            topic=queue_name,
            payload=task_data,
            priority=priority
        )
        return await self.publish(message)



    async def publish(self, message: Message) -> str:
        """發布訊息"""
        if not self.redis_pool:
            raise RuntimeError("Message queue not started")

        # 根據優先級決定佇列名稱
        queue_name = f"queue:{message.topic}:{message.priority.value}"

        # 如果有調度時間，則放入延遲佇列
        if message.scheduled_at and message.scheduled_at > time.time():
            await self.redis_pool.zadd(
                "scheduled_messages", {json.dumps(message.to_dict()): message.scheduled_at}
            )
        else:
            # 立即放入處理佇列
            await self.redis_pool.lpush(queue_name, json.dumps(message.to_dict()))

        logger.debug(f"Published message: {message.id} to topic: {message.topic}")
        return message.id

    async def publish_event(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        **metadata,
    ) -> str:
        """發布事件（便利方法）"""
        message = Message(
            topic=topic,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at.timestamp() if scheduled_at else None,
            metadata=metadata,
        )
        return await self.publish(message)

    async def _worker(self, worker_id: str):
        """工作者協程"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # 嘗試從各優先級佇列獲取訊息
                message = await self._get_next_message()

                if message:
                    await self._process_message(message, worker_id)
                else:
                    # 沒有訊息，等待一下
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)

        logger.info(f"Worker {worker_id} stopped")

    async def _get_next_message(self) -> Optional[Message]:
        """獲取下一個要處理的訊息"""
        if not self.redis_pool:
            return None

        # 按優先級順序檢查佇列
        for priority in [
            MessagePriority.CRITICAL,
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.LOW,
        ]:
            # 檢查所有topic的該優先級佇列
            for topic in self.handlers.keys():
                queue_name = f"queue:{topic}:{priority.value}"

                # 非阻塞獲取訊息
                message_data = await self.redis_pool.rpop(queue_name)
                if message_data:
                    try:
                        data = json.loads(message_data)
                        return Message.from_dict(data)
                    except Exception as e:
                        logger.error(f"Failed to parse message: {e}")
                        continue

        return None

    async def _process_message(self, message: Message, worker_id: str):
        """處理訊息"""
        handler = self.handlers.get(message.topic)
        if not handler:
            logger.warning(f"No handler found for topic: {message.topic}")
            return

        logger.info(
            f"Worker {worker_id} processing message {message.id} from topic {message.topic}"
        )

        try:
            # 設置處理超時
            success = await asyncio.wait_for(handler.handle(message), timeout=message.timeout)

            if success:
                logger.info(f"Message {message.id} processed successfully")
                await self._mark_message_completed(message)
            else:
                logger.warning(f"Message {message.id} processing failed")
                await self._handle_message_failure(message)

        except asyncio.TimeoutError:
            logger.error(f"Message {message.id} processing timeout")
            await self._handle_message_failure(message, "timeout")
        except Exception as e:
            logger.error(f"Message {message.id} processing error: {e}")
            await self._handle_message_failure(message, str(e))

    async def _handle_message_failure(self, message: Message, error: str = ""):
        """處理訊息失敗"""
        message.retry_count += 1

        if message.retry_count <= message.max_retries:
            # 重試，使用指數退避
            delay = min(300, 2**message.retry_count)  # 最大延遲5分鐘
            message.scheduled_at = time.time() + delay

            logger.info(
                f"Scheduling message {message.id} for retry {message.retry_count} in {delay}s"
            )

            if self.redis_pool:
                await self.redis_pool.zadd(
                    "scheduled_messages", {json.dumps(message.to_dict()): message.scheduled_at}
                )
        else:
            # 超過最大重試次數，放入失敗佇列
            logger.error(f"Message {message.id} failed after {message.max_retries} retries")
            await self._mark_message_failed(message, error)

    async def _mark_message_completed(self, message: Message):
        """標記訊息為已完成"""
        if self.redis_pool:
            # 可以選擇將完成的訊息保存到統計佇列
            await self.redis_pool.lpush(
                "completed_messages",
                json.dumps(
                    {
                        "id": message.id,
                        "topic": message.topic,
                        "completed_at": time.time(),
                        "processing_time": time.time() - message.created_at,
                    }
                ),
            )
            # 保持最近1000條完成記錄
            await self.redis_pool.ltrim("completed_messages", 0, 999)

    async def _mark_message_failed(self, message: Message, error: str = ""):
        """標記訊息為失敗"""
        if self.redis_pool:
            await self.redis_pool.lpush(
                "failed_messages",
                json.dumps(
                    {
                        "id": message.id,
                        "topic": message.topic,
                        "failed_at": time.time(),
                        "error": error,
                        "retry_count": message.retry_count,
                        "original_message": message.to_dict(),
                    }
                ),
            )
            # 保持最近1000條失敗記錄
            await self.redis_pool.ltrim("failed_messages", 0, 999)

    async def _scheduler(self):
        """調度器協程 - 處理延遲和重試訊息"""
        logger.info("Scheduler started")

        while self.running:
            try:
                if self.redis_pool:
                    current_time = time.time()

                    # 獲取需要執行的延遲訊息
                    scheduled_messages = await self.redis_pool.zrangebyscore(
                        "scheduled_messages", 0, current_time, withscores=True
                    )

                    for message_data, score in scheduled_messages:
                        try:
                            # 移除已調度的訊息
                            await self.redis_pool.zrem("scheduled_messages", message_data)

                            # 解析並重新放入佇列
                            data = json.loads(message_data)
                            message = Message.from_dict(data)

                            queue_name = f"queue:{message.topic}:{message.priority.value}"
                            await self.redis_pool.lpush(queue_name, message_data)

                            logger.debug(
                                f"Scheduled message {message.id} moved to processing queue"
                            )

                        except Exception as e:
                            logger.error(f"Error processing scheduled message: {e}")

                await asyncio.sleep(10)  # 每10秒檢查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(30)

        logger.info("Scheduler stopped")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """獲取佇列統計資訊"""
        if not self.redis_pool:
            return {}

        stats = {
            "topics": {},
            "scheduled_count": 0,
            "completed_count": 0,
            "failed_count": 0,
        }

        # 統計各topic的佇列長度
        for topic in self.handlers.keys():
            topic_stats = {}
            for priority in MessagePriority:
                queue_name = f"queue:{topic}:{priority.value}"
                length = await self.redis_pool.llen(queue_name)
                topic_stats[priority.name.lower()] = length
            stats["topics"][topic] = topic_stats

        # 統計延遲、完成和失敗訊息數量
        stats["scheduled_count"] = await self.redis_pool.zcard("scheduled_messages")
        stats["completed_count"] = await self.redis_pool.llen("completed_messages")
        stats["failed_count"] = await self.redis_pool.llen("failed_messages")

        return stats


# 全域訊息佇列實例
global_message_queue: Optional[MessageQueue] = None


def get_message_queue() -> MessageQueue:
    """獲取全域訊息佇列實例"""
    global global_message_queue
    if global_message_queue is None:
        global_message_queue = MessageQueue()
    return global_message_queue


# 事件類型定義
class VideoEvents:
    """影片相關事件"""

    VIDEO_CREATED = "video.created"
    VIDEO_PROCESSING_STARTED = "video.processing.started"
    VIDEO_PROCESSING_COMPLETED = "video.processing.completed"
    VIDEO_PROCESSING_FAILED = "video.processing.failed"
    VIDEO_PUBLISHED = "video.published"


class UserEvents:
    """用戶相關事件"""

    USER_REGISTERED = "user.registered"
    USER_SUBSCRIPTION_UPDATED = "user.subscription.updated"
    USER_PAYMENT_COMPLETED = "user.payment.completed"


class NotificationEvents:
    """通知相關事件"""

    SEND_EMAIL = "notification.email.send"
    SEND_SMS = "notification.sms.send"
    SEND_PUSH = "notification.push.send"


# 便利的發布函數
async def publish_video_event(event_type: str, video_id: int, user_id: int, **data):
    """發布影片事件"""
    queue = get_message_queue()
    await queue.publish_event(
        topic=event_type,
        payload={"video_id": video_id, "user_id": user_id, **data},
        service="video-service",
        timestamp=time.time(),
    )


async def publish_notification_event(event_type: str, user_id: int, **data):
    """發布通知事件"""
    queue = get_message_queue()
    await queue.publish_event(
        topic=event_type,
        payload={"user_id": user_id, **data},
        priority=MessagePriority.HIGH,
        service="notification-service",
        timestamp=time.time(),
    )
