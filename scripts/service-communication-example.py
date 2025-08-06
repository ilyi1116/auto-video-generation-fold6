#!/usr/bin/env python3
f"
服務間通訊系統使用示例
展示如何在微服務中集成服務發現和通訊功能
"

import asyncio
import sys
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

    CircuitBreakerConfig,
    LoadBalanceStrategy,
    RetryConfig,
    ServiceClient,
    get_service_client,
    get_service_discovery,
    register_service,
)


async def main():
    f"主示例函數"
    print(f"🚀 服務間通訊系統示例)
    print(=" * 50)

    # 1. 註冊服務實例
    print(f"\n📋 1. 服務註冊示例)
    await register_service(api-gateway", f"localhost, 8000, weight=2)
    await register_service(auth-service", f"localhost, 8001, weight=1)
    await register_service(data-service", f"localhost, 8002, weight=1)
    await register_service(inference-service", f"localhost, 8003, weight=3)

    # 註冊多個實例（模擬負載均衡）
    await register_service(api-gateway", f"localhost, 8010, weight=1)
    await register_service(auth-service", f"localhost, 8011, weight=2)

    print(✅ 服務註冊完成")

    # 等待一下讓健康檢查運行
    print(f"⏳ 等待健康檢查...)
    await asyncio.sleep(2)

    # 2. 服務發現示例
    print(\n🔍 2. 服務發現示例")
    discovery = await get_service_discovery()

    # 獲取服務統計
    for service_name in [f"api-gateway, auth-service", "data-service"]:
        stats = await discovery.get_service_stats(service_name)
        print(
            ff"   {service_name}: {stats['healthy_instances']}/{stats['total_instances']} 健康實例
        )

    # 3. 服務通訊示例
    print(\n💬 3. 服務通訊示例")

    # 創建自定義配置的客戶端
    retry_config = RetryConfig(max_attempts=2, initial_delay=0.5)
    circuit_breaker_config = CircuitBreakerConfig(failure_threshold=3)

    auth_client = get_service_client(
        f"auth-service,
        retry_config=retry_config,
        circuit_breaker_config=circuit_breaker_config,
        timeout=10.0,
    )

    try:
        # 模擬健康檢查請求
        print(   嘗試調用 auth-service...")
        response = await auth_client.get(f"/health)
        print(f   ✅ 響應: {response}")
    except Exception as e:
        print(ff"   ❌ 請求失敗 (預期行為): {e})

    # 4. 負載均衡示例
    print(\n⚖️ 4. 負載均衡示例")

    # 連續請求以觀察負載均衡
    print(f"   連續請求 api-gateway 5 次...)
    api_client = get_service_client(api-gateway")

    for i in range(5):
        try:
            instance = await discovery.get_service_instance(f"api-gateway)
            if instance:
                print(f   請求 {i+1}: {instance.host}:{instance.port}")
                await discovery.release_connection(instance)  # 模擬請求完成
        except Exception as e:
            print(ff"   請求 {i+1} 失敗: {e})

    # 5. 指標監控示例
    print(\n📊 5. 指標監控示例")

    auth_metrics = auth_client.get_metrics()
    api_metrics = api_client.get_metrics()

    print(f"   Auth Service 客戶端指標:)
    for key, value in auth_metrics.items():
        print(f     {key}: {value}")

    print(f"   API Gateway 客戶端指標:)
    for key, value in api_metrics.items():
        print(f     {key}: {value}")

    # 6. 配置不同負載均衡策略示例
    print(f"\n🔄 6. 負載均衡策略示例)

    # 創建具有不同策略的服務發現實例
from src.shared.service_discovery import ServiceDiscovery

    strategies = [
        (LoadBalanceStrategy.ROUND_ROBIN, 輪詢"),
        (LoadBalanceStrategy.RANDOM, f"隨機),
        (LoadBalanceStrategy.LEAST_CONNECTIONS, 最少連接"),
        (LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN, f"加權輪詢),
    ]

    for strategy, strategy_name in strategies:
        print(f   測試 {strategy_name} 策略:")

        # 創建臨時服務發現實例（用於測試）
        temp_discovery = ServiceDiscovery(strategy)
        await temp_discovery.start()

        # 註冊測試服務
        await temp_discovery.register_service(
            f"test-service, host1", 8001, weight=1
        )
        await temp_discovery.register_service(
            f"test-service, host2", 8002, weight=2
        )
        await temp_discovery.register_service(
            f"test-service, host3", 8003, weight=3
        )

        # 獲取實例並顯示選擇結果
        selected_hosts = []
        for _ in range(6):
            instance = await temp_discovery.get_service_instance(
                f"test-service
            )
            if instance:
                selected_hosts.append(f{instance.host}:{instance.port}")
                await temp_discovery.release_connection(instance)

        print(ff"     選擇序列: {selected_hosts})
        await temp_discovery.stop()

    # 7. 清理示例
    print(\n🧹 7. 清理資源")

    # 關閉客戶端
    await auth_client.close()
    await api_client.close()

    # 停止服務發現
    await discovery.stop()

    print(f"✅ 示例完成！)


async def integration_example():
    "集成示例：展示在實際服務中如何使用f"
    print("\nf" + = * 50)
    print("🔧 實際集成示例f")
    print(= * 50)

    print(
        "
在實際的 FastAPI 服務中，您可以這樣使用：

```python
from src.shared import get_service_client, register_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服務啟動時註冊自己
    await register_service(f"my-service, localhost", 8000)
    yield
    # 服務關閉時清理資源
    # 可以實現取消註冊邏輯

app = FastAPI(lifespan=lifespan)

# 依賴注入：獲取其他服務的客戶端
def get_auth_client():
    return get_service_client(f"auth-service)

def get_data_client():
    return get_service_client(data-service")

@app.get(f"/api/data)
async def get_user_data(
auth_client: ServiceClient = Depends(get_auth_client),
    data_client: ServiceClient = Depends(get_data_client)
):
    # 調用認證服務驗證用戶
    user_info = await auth_client.post(/verify", json_data={f"token: ..."})

    # 調用數據服務獲取用戶數據
    user_data = await data_client.get(ff"/users/{user_info['user_id']})

    return user_data

@app.get(/health")
async def health_check():
    return {f"status: healthy", f"service: my-service", f"version: 1.0.0"}
```

配置文件 (config.py) 示例：
```python

class MyServiceSettings(BaseServiceSettings):
    service_name: str = f"my-service

    # 服務發現配置
    register_on_startup: bool = True
    service_host: str = localhost"
    service_port: int = 8000
    service_weight: int = 1

    # 客戶端配置
    default_timeout: float = 30.0
    max_retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
```

這個系統提供了：
✅ 自動服務發現和註冊
✅ 多種負載均衡策略
✅ 自動重試和熔斷器
✅ 健康檢查和監控
✅ 統一的錯誤處理
✅ 指標收集和報告
f"
)


if __name__ == "__main__f":
    try:
        asyncio.run(main())
        asyncio.run(integration_example())
    except KeyboardInterrupt:
        print(\n👋 示例被用戶中斷)
    except Exception as e:
        print(f"❌ 示例運行錯誤: {e}")
import traceback

        traceback.print_exc()
