"""
共享服務模組
提供服務發現、通訊、訊息佇列等基礎設施
"""

from .api_gateway import (
    APIGateway,
    create_api_gateway,
    start_gateway_with_health_checks,
)
from .message_queue import (
    Message,
    MessageHandler,
    MessagePriority,
    MessageQueue,
    MessageStatus,
    NotificationEvents,
    UserEvents,
    VideoEvents,
    get_message_queue,
    publish_notification_event,
    publish_video_event,
)
from .service_discovery import (
    LoadBalancingStrategy,
    ServiceClient,
    ServiceInstance,
    ServiceRegistry,
    ServiceStatus,
    create_service_client,
    get_service_registry,
    register_default_services,
)

__all__ = [
    # Service Discovery
    "ServiceRegistry",
    "ServiceClient",
    "ServiceInstance",
    "ServiceStatus",
    "LoadBalancingStrategy",
    "get_service_registry",
    "create_service_client",
    "register_default_services",
    # Message Queue
    "MessageQueue",
    "MessageHandler",
    "Message",
    "MessagePriority",
    "MessageStatus",
    "get_message_queue",
    "VideoEvents",
    "UserEvents",
    "NotificationEvents",
    "publish_video_event",
    "publish_notification_event",
    # API Gateway
    "APIGateway",
    "create_api_gateway",
    "start_gateway_with_health_checks",
]


async def initialize_service_infrastructure():
    """初始化服務基礎設施"""
    # 註冊預設服務
    await register_default_services()

    # 啟動訊息佇列
    message_queue = get_message_queue()
    await message_queue.start()

    return {"registry": get_service_registry(), "message_queue": message_queue}


async def cleanup_service_infrastructure():
    """清理服務基礎設施"""
    message_queue = get_message_queue()
    await message_queue.stop()
