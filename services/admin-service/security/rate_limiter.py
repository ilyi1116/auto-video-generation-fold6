"""
API 安全防護 - 限流器
提供基於 IP、用戶和 API Key 的多層限流功能
"""

import asyncio
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Tuple

import redis
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class LimitType(Enum):
    """限流類型"""

    IP = "ip"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


class WindowType(Enum):
    """時間窗口類型"""

    FIXED = "fixed"  # 固定窗口
    SLIDING = "sliding"  # 滑動窗口
    TOKEN_BUCKET = "token_bucket"  # 令牌桶


@dataclass
class RateLimit:
    """限流配置"""

    limit: int  # 限制次數
    window_seconds: int  # 時間窗口（秒）
    window_type: WindowType = WindowType.SLIDING
    burst_limit: Optional[int] = None  # 突發限制
    description: str = ""


@dataclass
class RateLimitResult:
    """限流結果"""

    allowed: bool  # 是否允許請求
    limit: int  # 限制次數
    remaining: int  # 剩餘次數
    reset_time: datetime  # 重置時間
    retry_after: Optional[int] = None  # 重試間隔（秒）


class RateLimiter:
    """限流器"""

    def __init__(self, redis_url: str = "redis://localhost:6379/3"):
        """
        初始化限流器

        Args:
            redis_url: Redis 連接 URL
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # 測試連接
            self.redis_client.ping()
            logger.info("Rate limiter Redis 連接成功")
        except Exception as e:
            logger.warning(f"Rate limiter Redis 連接失敗，使用內存存儲: {e}")
            self.redis_client = None
            self._memory_store = {}

        # 預設限流配置
        self.default_limits = {
            LimitType.IP: RateLimit(
                limit=1000, window_seconds=3600, description="每小時每個 IP 1000 次請求"
            ),
            LimitType.USER: RateLimit(
                limit=5000, window_seconds=3600, description="每小時每個用戶 5000 次請求"
            ),
            LimitType.API_KEY: RateLimit(
                limit=10000, window_seconds=3600, description="每小時每個 API Key 10000 次請求"
            ),
            LimitType.ENDPOINT: RateLimit(
                limit=100, window_seconds=60, description="每分鐘每個端點 100 次請求"
            ),
            LimitType.GLOBAL: RateLimit(
                limit=50000, window_seconds=3600, description="全局每小時 50000 次請求"
            ),
        }

        # 端點特定限制
        self.endpoint_limits = {
            "/admin/auth/login": RateLimit(
                limit=5, window_seconds=300, description="登錄端點每5分鐘5次嘗試"
            ),
            "/admin/ai-providers": RateLimit(
                limit=200, window_seconds=3600, description="AI Provider 管理每小時200次"
            ),
            "/admin/logs/export": RateLimit(
                limit=10, window_seconds=3600, description="日誌導出每小時10次"
            ),
            "/admin/monitoring/health/check": RateLimit(
                limit=60, window_seconds=3600, description="健康檢查每小時60次"
            ),
        }

        # 白名單 IP
        self.whitelist_ips = {"127.0.0.1", "::1", "localhost"}

        # 黑名單 IP
        self.blacklist_ips = set()

    def _get_key(self, limit_type: LimitType, identifier: str, endpoint: str = None) -> str:
        """生成 Redis 鍵"""
        if endpoint:
            return f"rate_limit:{limit_type.value}:{identifier}:{endpoint}"
        return f"rate_limit:{limit_type.value}:{identifier}"

    def _get_client_identifier(self, request: Request) -> Tuple[str, Optional[str], Optional[str]]:
        """
        獲取客戶端標識符

        Returns:
            (ip_address, user_id, api_key)
        """
        # 獲取真實 IP (考慮代理)
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip:
            ip = request.headers.get("X-Real-IP", "")
        if not ip:
            ip = request.client.host if request.client else "unknown"

        # 獲取用戶 ID
        user_id = None
        current_user = getattr(request.state, "current_user", None)
        if current_user:
            user_id = str(current_user.id) if hasattr(current_user, "id") else None

        # 獲取 API Key
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            # 從 Authorization header 中提取
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # 可以考慮使用 JWT token 作為標識

        return ip, user_id, api_key

    async def _check_limit_redis(self, key: str, limit: RateLimit) -> RateLimitResult:
        """使用 Redis 檢查限流"""
        try:
            pipe = self.redis_client.pipeline()
            now = time.time()
            window_start = now - limit.window_seconds

            if limit.window_type == WindowType.SLIDING:
                # 滑動窗口算法
                pipe.zremrangebyscore(key, 0, window_start)  # 清理過期記錄
                pipe.zcard(key)  # 獲取當前計數
                pipe.zadd(key, {str(now): now})  # 添加當前請求
                pipe.expire(key, limit.window_seconds)  # 設置過期時間

                results = pipe.execute()
                current_count = results[1] + 1  # +1 因為剛添加了當前請求

            elif limit.window_type == WindowType.FIXED:
                # 固定窗口算法
                window_key = f"{key}:{int(now // limit.window_seconds)}"
                pipe.incr(window_key)
                pipe.expire(window_key, limit.window_seconds)
                results = pipe.execute()
                current_count = results[0]

            elif limit.window_type == WindowType.TOKEN_BUCKET:
                # 令牌桶算法
                bucket_key = f"{key}:bucket"

                # 獲取當前桶狀態
                bucket_data = self.redis_client.hgetall(bucket_key)
                if bucket_data:
                    last_refill = float(bucket_data.get("last_refill", now))
                    tokens = float(bucket_data.get("tokens", limit.limit))
                else:
                    last_refill = now
                    tokens = limit.limit

                # 計算需要添加的令牌數
                time_passed = now - last_refill
                tokens_to_add = time_passed * (limit.limit / limit.window_seconds)
                tokens = min(limit.limit, tokens + tokens_to_add)

                if tokens >= 1:
                    tokens -= 1
                    pipe.hset(bucket_key, mapping={"tokens": tokens, "last_refill": now})
                    pipe.expire(bucket_key, limit.window_seconds * 2)
                    pipe.execute()
                    current_count = limit.limit - int(tokens)
                else:
                    current_count = limit.limit + 1  # 超過限制

            # 計算結果
            allowed = current_count <= limit.limit
            remaining = max(0, limit.limit - current_count)
            reset_time = datetime.fromtimestamp(now + limit.window_seconds)
            retry_after = limit.window_seconds if not allowed else None

            return RateLimitResult(
                allowed=allowed,
                limit=limit.limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
            )

        except Exception as e:
            logger.error(f"Redis 限流檢查失敗: {e}")
            # 降級到允許請求
            return RateLimitResult(
                allowed=True,
                limit=limit.limit,
                remaining=limit.limit,
                reset_time=datetime.utcnow() + timedelta(seconds=limit.window_seconds),
            )

    async def _check_limit_memory(self, key: str, limit: RateLimit) -> RateLimitResult:
        """使用內存檢查限流"""
        now = time.time()

        if key not in self._memory_store:
            self._memory_store[key] = []

        # 清理過期記錄
        window_start = now - limit.window_seconds
        self._memory_store[key] = [
            timestamp for timestamp in self._memory_store[key] if timestamp > window_start
        ]

        # 檢查限制
        current_count = len(self._memory_store[key])

        if current_count < limit.limit:
            self._memory_store[key].append(now)
            allowed = True
            remaining = limit.limit - current_count - 1
        else:
            allowed = False
            remaining = 0

        reset_time = datetime.fromtimestamp(
            min(self._memory_store[key]) + limit.window_seconds
            if self._memory_store[key]
            else now + limit.window_seconds
        )

        return RateLimitResult(
            allowed=allowed,
            limit=limit.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=limit.window_seconds if not allowed else None,
        )

    async def check_rate_limit(self, request: Request) -> Optional[RateLimitResult]:
        """
        檢查請求是否超過限流

        Returns:
            None 如果允許請求，否則返回 RateLimitResult
        """
        try:
            ip, user_id, api_key = self._get_client_identifier(request)
            endpoint = request.url.path

            # 檢查黑名單
            if ip in self.blacklist_ips:
                return RateLimitResult(
                    allowed=False,
                    limit=0,
                    remaining=0,
                    reset_time=datetime.utcnow() + timedelta(days=1),
                    retry_after=86400,
                )

            # 檢查白名單
            if ip in self.whitelist_ips:
                return None

            # 要檢查的限制列表
            checks = []

            # 1. IP 限制
            checks.append((self._get_key(LimitType.IP, ip), self.default_limits[LimitType.IP]))

            # 2. 用戶限制
            if user_id:
                checks.append(
                    (self._get_key(LimitType.USER, user_id), self.default_limits[LimitType.USER])
                )

            # 3. API Key 限制
            if api_key:
                checks.append(
                    (
                        self._get_key(LimitType.API_KEY, api_key),
                        self.default_limits[LimitType.API_KEY],
                    )
                )

            # 4. 端點特定限制
            if endpoint in self.endpoint_limits:
                checks.append(
                    (
                        self._get_key(LimitType.ENDPOINT, ip, endpoint),
                        self.endpoint_limits[endpoint],
                    )
                )

            # 5. 全局限制
            checks.append(
                (self._get_key(LimitType.GLOBAL, "all"), self.default_limits[LimitType.GLOBAL])
            )

            # 執行所有檢查
            for key, limit_config in checks:
                if self.redis_client:
                    result = await self._check_limit_redis(key, limit_config)
                else:
                    result = await self._check_limit_memory(key, limit_config)

                if not result.allowed:
                    # 記錄限流事件
                    await self._log_rate_limit_violation(request, limit_config, result)
                    return result

            return None  # 所有檢查都通過

        except Exception as e:
            logger.error(f"限流檢查失敗: {e}")
            return None  # 降級到允許請求

    async def _log_rate_limit_violation(
        self, request: Request, limit: RateLimit, result: RateLimitResult
    ):
        """記錄限流違規"""
        try:
            from ..logging_system import AuditLogger

            ip, user_id, api_key = self._get_client_identifier(request)

            await AuditLogger.log_security_event(
                action="rate_limit_exceeded",
                level="warning",
                message=f"請求超過限流: {limit.description}",
                details={
                    "ip_address": ip,
                    "user_id": user_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "limit": result.limit,
                    "retry_after": result.retry_after,
                    "user_agent": request.headers.get("User-Agent"),
                },
                ip_address=ip,
                request=request,
            )
        except Exception as e:
            logger.error(f"記錄限流事件失敗: {e}")

    def add_to_blacklist(self, ip: str, duration_hours: int = 24):
        """添加 IP 到黑名單"""
        self.blacklist_ips.add(ip)

        # 如果使用 Redis，設置過期時間
        if self.redis_client:
            try:
                key = f"blacklist_ip:{ip}"
                self.redis_client.setex(key, duration_hours * 3600, "1")
            except Exception as e:
                logger.error(f"添加黑名單到 Redis 失敗: {e}")

    def remove_from_blacklist(self, ip: str):
        """從黑名單移除 IP"""
        self.blacklist_ips.discard(ip)

        if self.redis_client:
            try:
                key = f"blacklist_ip:{ip}"
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"從 Redis 移除黑名單失敗: {e}")

    def add_to_whitelist(self, ip: str):
        """添加 IP 到白名單"""
        self.whitelist_ips.add(ip)

    def remove_from_whitelist(self, ip: str):
        """從白名單移除 IP"""
        self.whitelist_ips.discard(ip)

    def update_limit(self, limit_type: LimitType, limit_config: RateLimit):
        """更新限流配置"""
        self.default_limits[limit_type] = limit_config

    def update_endpoint_limit(self, endpoint: str, limit_config: RateLimit):
        """更新端點限流配置"""
        self.endpoint_limits[endpoint] = limit_config

    def get_stats(self) -> Dict:
        """獲取限流統計"""
        return {
            "default_limits": {k.value: asdict(v) for k, v in self.default_limits.items()},
            "endpoint_limits": {k: asdict(v) for k, v in self.endpoint_limits.items()},
            "whitelist_count": len(self.whitelist_ips),
            "blacklist_count": len(self.blacklist_ips),
            "redis_connected": self.redis_client is not None,
        }


# 全局限流器實例
rate_limiter = RateLimiter()


# FastAPI 中間件
class RateLimitMiddleware:
    """限流中間件"""

    def __init__(self, app, limiter: RateLimiter = None):
        self.app = app
        self.limiter = limiter or rate_limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # 檢查限流
            limit_result = await self.limiter.check_rate_limit(request)

            if limit_result and not limit_result.allowed:
                # 返回限流錯誤
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "message": "請求頻率過高，請稍後再試",
                        "limit": limit_result.limit,
                        "remaining": limit_result.remaining,
                        "reset_time": limit_result.reset_time.isoformat(),
                        "retry_after": limit_result.retry_after,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit_result.limit),
                        "X-RateLimit-Remaining": str(limit_result.remaining),
                        "X-RateLimit-Reset": str(int(limit_result.reset_time.timestamp())),
                        "Retry-After": str(limit_result.retry_after or 60),
                    },
                )
                await response(scope, receive, send)
                return

        # 繼續處理請求
        await self.app(scope, receive, send)


# 裝飾器
def rate_limit(limit: int, window_seconds: int, window_type: WindowType = WindowType.SLIDING):
    """限流裝飾器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 檢查是否有 request 參數
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request:
                # 創建臨時限制配置
                temp_limit = RateLimit(
                    limit=limit,
                    window_seconds=window_seconds,
                    window_type=window_type,
                    description=f"函數 {func.__name__} 限流",
                )

                # 使用函數名作為端點
                endpoint_key = f"function:{func.__name__}"
                ip, _, _ = rate_limiter._get_client_identifier(request)
                key = rate_limiter._get_key(LimitType.ENDPOINT, ip, endpoint_key)

                if rate_limiter.redis_client:
                    result = await rate_limiter._check_limit_redis(key, temp_limit)
                else:
                    result = await rate_limiter._check_limit_memory(key, temp_limit)

                if not result.allowed:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "Too Many Requests",
                            "message": f"函數 {func.__name__} 調用頻率過高",
                            "retry_after": result.retry_after,
                        },
                    )

            return (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

        return wrapper

    return decorator
