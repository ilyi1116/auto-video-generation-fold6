"""
統一服務間通訊客戶端
提供服務間 HTTP 通訊、重試、熔斷器和監控功能
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
import logging
import aiohttp
from urllib.parse import urljoin

from .service_discovery import get_service_discovery, ServiceInstance


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """熔斷器狀態"""
    CLOSED = "closed"      # 正常狀態
    OPEN = "open"          # 熔斷狀態
    HALF_OPEN = "half_open"  # 半開狀態


@dataclass
class RetryConfig:
    """重試配置"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """熔斷器配置"""
    failure_threshold: int = 5       # 失敗閾值
    recovery_timeout: float = 60.0   # 恢復超時時間
    success_threshold: int = 3       # 半開狀態成功閾值


@dataclass
class RequestMetrics:
    """請求指標"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: float = 0.0


class CircuitBreaker:
    """熔斷器實現"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        
    async def call(self, func, *args, **kwargs):
        """通過熔斷器調用函數"""
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker state changed to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """處理成功情況"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker state changed to CLOSED")
        else:
            self.failure_count = 0
    
    async def _on_failure(self):
        """處理失敗情況"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker state changed to OPEN after {self.failure_count} failures")


class CircuitBreakerOpenError(Exception):
    """熔斷器開啟異常"""
    pass


class ServiceClient:
    """服務間通訊客戶端"""
    
    def __init__(self, 
                 service_name: str,
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                 timeout: float = 30.0):
        self.service_name = service_name
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())
        self.timeout = timeout
        self.metrics = RequestMetrics()
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取 HTTP 會話"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """關閉客戶端"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def request(self, 
                     method: str,
                     path: str,
                     headers: Optional[Dict[str, str]] = None,
                     json_data: Optional[Dict[str, Any]] = None,
                     data: Optional[Any] = None,
                     params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """發送 HTTP 請求"""
        return await self.circuit_breaker.call(
            self._request_with_retry,
            method, path, headers, json_data, data, params
        )
    
    async def _request_with_retry(self,
                                 method: str,
                                 path: str,
                                 headers: Optional[Dict[str, str]] = None,
                                 json_data: Optional[Dict[str, Any]] = None,
                                 data: Optional[Any] = None,
                                 params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """帶重試的請求"""
        last_exception = None
        delay = self.retry_config.initial_delay
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                start_time = time.time()
                
                # 獲取服務實例
                discovery = await get_service_discovery()
                instance = await discovery.get_service_instance(self.service_name)
                
                if not instance:
                    raise ServiceUnavailableError(f"No available instances for service: {self.service_name}")
                
                try:
                    result = await self._make_request(
                        instance, method, path, headers, json_data, data, params
                    )
                    
                    # 更新指標
                    response_time = time.time() - start_time
                    await self._update_metrics(True, response_time)
                    
                    return result
                    
                finally:
                    # 釋放連接
                    await discovery.release_connection(instance)
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Request attempt {attempt + 1} failed for {self.service_name}: {e}")
                
                # 更新指標
                response_time = time.time() - start_time
                await self._update_metrics(False, response_time)
                
                if attempt < self.retry_config.max_attempts - 1:
                    # 計算延遲時間
                    if self.retry_config.jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * self.retry_config.exponential_base, self.retry_config.max_delay)
        
        raise last_exception or ServiceUnavailableError(f"All retry attempts failed for service: {self.service_name}")
    
    async def _make_request(self,
                           instance: ServiceInstance,
                           method: str,
                           path: str,
                           headers: Optional[Dict[str, str]] = None,
                           json_data: Optional[Dict[str, Any]] = None,
                           data: Optional[Any] = None,
                           params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """發送實際 HTTP 請求"""
        session = await self._get_session()
        url = urljoin(instance.url, path.lstrip('/'))
        
        # 添加默認頭部
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'ServiceClient/{self.service_name}'
        }
        if headers:
            request_headers.update(headers)
        
        logger.debug(f"Making {method} request to {url}")
        
        async with session.request(
            method=method,
            url=url,
            headers=request_headers,
            json=json_data,
            data=data,
            params=params
        ) as response:
            
            if response.status >= 400:
                error_text = await response.text()
                raise HTTPError(
                    status_code=response.status,
                    message=f"HTTP {response.status}: {error_text}",
                    response_text=error_text
                )
            
            # 嘗試解析 JSON 響應
            try:
                return await response.json()
            except Exception:
                # 如果不是 JSON，返回文本
                text = await response.text()
                return {"data": text, "content_type": response.content_type}
    
    async def _update_metrics(self, success: bool, response_time: float):
        """更新請求指標"""
        self.metrics.total_requests += 1
        self.metrics.last_request_time = time.time()
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # 更新平均響應時間（使用移動平均）
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            alpha = 0.1  # 平滑因子
            self.metrics.average_response_time = (
                alpha * response_time + 
                (1 - alpha) * self.metrics.average_response_time
            )
    
    # 便捷方法
    async def get(self, path: str, headers: Optional[Dict[str, str]] = None, 
                 params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET 請求"""
        return await self.request('GET', path, headers=headers, params=params)
    
    async def post(self, path: str, json_data: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None, data: Optional[Any] = None) -> Dict[str, Any]:
        """POST 請求"""
        return await self.request('POST', path, headers=headers, json_data=json_data, data=data)
    
    async def put(self, path: str, json_data: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None, data: Optional[Any] = None) -> Dict[str, Any]:
        """PUT 請求"""
        return await self.request('PUT', path, headers=headers, json_data=json_data, data=data)
    
    async def delete(self, path: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """DELETE 請求"""
        return await self.request('DELETE', path, headers=headers)
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取客戶端指標"""
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = self.metrics.successful_requests / self.metrics.total_requests * 100
        
        return {
            "service_name": self.service_name,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": success_rate,
            "average_response_time": self.metrics.average_response_time,
            "last_request_time": self.metrics.last_request_time,
            "circuit_breaker_state": self.circuit_breaker.state.value
        }


class ServiceUnavailableError(Exception):
    """服務不可用異常"""
    pass


class HTTPError(Exception):
    """HTTP 錯誤異常"""
    
    def __init__(self, status_code: int, message: str, response_text: str = ""):
        self.status_code = status_code
        self.message = message
        self.response_text = response_text
        super().__init__(message)


# 客戶端管理器
class ServiceClientManager:
    """服務客戶端管理器"""
    
    def __init__(self):
        self._clients: Dict[str, ServiceClient] = {}
    
    def get_client(self, 
                   service_name: str,
                   retry_config: Optional[RetryConfig] = None,
                   circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                   timeout: float = 30.0) -> ServiceClient:
        """獲取或創建服務客戶端"""
        if service_name not in self._clients:
            self._clients[service_name] = ServiceClient(
                service_name=service_name,
                retry_config=retry_config,
                circuit_breaker_config=circuit_breaker_config,
                timeout=timeout
            )
        return self._clients[service_name]
    
    async def close_all(self):
        """關閉所有客戶端"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """獲取所有客戶端指標"""
        return {name: client.get_metrics() for name, client in self._clients.items()}


# 全局客戶端管理器
_client_manager: Optional[ServiceClientManager] = None


def get_client_manager() -> ServiceClientManager:
    """獲取全局客戶端管理器"""
    global _client_manager
    if _client_manager is None:
        _client_manager = ServiceClientManager()
    return _client_manager


def get_service_client(service_name: str, **kwargs) -> ServiceClient:
    """獲取服務客戶端的便捷函數"""
    manager = get_client_manager()
    return manager.get_client(service_name, **kwargs)