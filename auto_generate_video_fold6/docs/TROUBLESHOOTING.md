# 🔧 Auto Video 故障排除指南

## 📖 概覽

本指南提供 Auto Video 系統常見問題的診斷和解決方案，幫助開發者和運維人員快速定位並解決系統問題。

## 🎯 快速診斷

### 系統健康檢查清單

在深入特定問題之前，請先執行以下基本檢查：

```bash
# 1. 檢查所有服務狀態
docker-compose ps

# 2. 檢查系統資源
df -h                    # 磁碟空間
free -h                  # 記憶體使用
htop                     # CPU 和程序狀態

# 3. 檢查網路連接
curl -f http://localhost:8000/health

# 4. 檢查日誌
docker-compose logs --tail=100 -f
```

### 服務健康狀態快速檢查

```bash
#!/bin/bash
# scripts/quick-health-check.sh

echo "🔍 執行系統健康檢查..."

# 檢查核心服務
services=("api-gateway" "auth-service" "video-service" "ai-service" "postgres" "redis")

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✅ $service: 正常運行"
    else
        echo "❌ $service: 狀態異常"
        docker-compose logs --tail=10 $service
    fi
done

# 檢查端點可用性
endpoints=(
    "http://localhost:8000/health:API Gateway"
    "http://localhost:8001/health:Auth Service"
    "http://localhost:8004/health:Video Service"
    "http://localhost:3000:Frontend"
)

for endpoint_info in "${endpoints[@]}"; do
    endpoint=$(echo $endpoint_info | cut -d: -f1)
    name=$(echo $endpoint_info | cut -d: -f2)
    
    if curl -s -f $endpoint > /dev/null; then
        echo "✅ $name: 端點可訪問"
    else
        echo "❌ $name: 端點不可訪問 ($endpoint)"
    fi
done

# 檢查資料庫連接
if docker-compose exec postgres pg_isready -U autovideo > /dev/null 2>&1; then
    echo "✅ PostgreSQL: 資料庫連接正常"
else
    echo "❌ PostgreSQL: 資料庫連接失敗"
fi

# 檢查 Redis 連接
if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis: 快取服務正常"
else
    echo "❌ Redis: 快取服務異常"
fi
```

## 🚨 常見問題分類

### 1. 服務啟動問題

#### 1.1 容器無法啟動

**症狀**：
- `docker-compose up` 失敗
- 容器狀態顯示 `Exited`
- 服務無法訪問

**診斷步驟**：
```bash
# 查看容器狀態
docker-compose ps

# 查看失敗容器的日誌
docker-compose logs service-name

# 檢查資源使用
docker stats

# 檢查磁碟空間
df -h
```

**常見原因和解決方案**：

| 錯誤類型 | 症狀 | 解決方案 |
|----------|------|----------|
| 端口衝突 | `Port already in use` | 更改端口配置或停止衝突程序 |
| 記憶體不足 | `OOMKilled` | 增加系統記憶體或調整容器限制 |
| 磁碟空間不足 | `No space left on device` | 清理磁碟空間或掛載更大存儲 |
| 環境變數錯誤 | `Config error` | 檢查 `.env` 文件配置 |
| 映像問題 | `Image not found` | 重新構建映像或檢查映像名稱 |

**解決示例**：
```bash
# 端口衝突解決
sudo lsof -i :8000                    # 找出佔用端口的程序
sudo kill -9 PID                      # 終止佔用程序
# 或修改 docker-compose.yml 中的端口映射

# 磁碟空間清理
docker system prune -a                # 清理未使用的 Docker 資源
docker volume prune                   # 清理未使用的卷
sudo apt clean                        # 清理系統快取
```

#### 1.2 資料庫連接失敗

**症狀**：
- 應用啟動時資料庫連接失敗
- `Connection refused` 或 `Connection timeout` 錯誤
- 服務健康檢查失敗

**診斷步驟**：
```bash
# 檢查資料庫容器狀態
docker-compose logs postgres

# 測試資料庫連接
docker-compose exec postgres pg_isready -U autovideo

# 檢查網路連接
docker network ls
docker network inspect autovideo_default

# 驗證資料庫配置
docker-compose exec postgres psql -U autovideo -d autovideo_prod -c "SELECT version();"
```

**解決方案**：
```bash
# 重啟資料庫服務
docker-compose restart postgres

# 檢查資料庫日誌
docker-compose logs postgres --tail=50

# 重新初始化資料庫（僅開發環境）
docker-compose down
docker volume rm autovideo_postgres_data
docker-compose up -d postgres
# 等待資料庫啟動
sleep 30
# 執行遷移
docker-compose exec api-gateway alembic upgrade head
```

### 2. 效能問題

#### 2.1 API 回應時間過長

**症狀**：
- API 請求超時
- 回應時間 > 5 秒
- 用戶體驗緩慢

**診斷步驟**：
```bash
# 檢查 API 回應時間
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/videos"

# curl-format.txt 內容：
#     time_namelookup:  %{time_namelookup}s\n
#        time_connect:  %{time_connect}s\n
#     time_appconnect:  %{time_appconnect}s\n
#    time_pretransfer:  %{time_pretransfer}s\n
#       time_redirect:  %{time_redirect}s\n
#  time_starttransfer:  %{time_starttransfer}s\n
#                     ----------\n
#          time_total:  %{time_total}s\n

# 檢查資料庫查詢效能
docker-compose exec postgres psql -U autovideo -d autovideo_prod -c "
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# 檢查系統負載
htop
iostat -x 1
```

**效能分析工具**：
```python
# 建立效能分析腳本 scripts/performance-analysis.py
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

async def benchmark_endpoint(url: str, num_requests: int = 100):
    """基準測試 API 端點"""
    response_times = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for _ in range(num_requests):
            tasks.append(measure_request(session, url))
        
        results = await asyncio.gather(*tasks)
        response_times = [r for r in results if r is not None]
    
    if response_times:
        print(f"\n📊 {url} 效能分析:")
        print(f"總請求數: {len(response_times)}")
        print(f"成功率: {len(response_times)/num_requests*100:.1f}%")
        print(f"平均回應時間: {statistics.mean(response_times):.3f}s")
        print(f"中位數回應時間: {statistics.median(response_times):.3f}s")
        print(f"95% 分位數: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
        print(f"最大回應時間: {max(response_times):.3f}s")
        print(f"最小回應時間: {min(response_times):.3f}s")

async def measure_request(session: aiohttp.ClientSession, url: str):
    """測量單個請求的回應時間"""
    try:
        start_time = time.time()
        async with session.get(url) as response:
            await response.text()
            return time.time() - start_time
    except Exception as e:
        print(f"請求失敗: {e}")
        return None

# 使用方式
if __name__ == "__main__":
    endpoints = [
        "http://localhost:8000/api/v1/videos",
        "http://localhost:8000/api/v1/users/me",
        "http://localhost:8000/health"
    ]
    
    for endpoint in endpoints:
        asyncio.run(benchmark_endpoint(endpoint, 50))
```

**解決方案**：
```bash
# 1. 優化資料庫查詢
# 添加適當的索引
docker-compose exec postgres psql -U autovideo -d autovideo_prod -c "
CREATE INDEX CONCURRENTLY idx_videos_user_created 
ON videos(user_id, created_at DESC);"

# 2. 啟用查詢快取
# 在應用中添加 Redis 快取層

# 3. 增加資源限制
# 修改 docker-compose.yml
#   deploy:
#     resources:
#       limits:
#         memory: 2G
#         cpus: '1.0'

# 4. 啟用連接池
# 調整資料庫連接池設置
```

#### 2.2 記憶體洩漏

**症狀**：
- 記憶體使用持續增長
- 容器被 OOM Kill
- 系統變得不穩定

**診斷步驟**：
```bash
# 監控記憶體使用
docker stats --no-stream

# 檢查程序記憶體使用
docker-compose exec api-gateway top

# 分析記憶體洩漏
docker-compose exec api-gateway python -c "
import gc
import psutil
import os

process = psutil.Process(os.getpid())
print(f'記憶體使用: {process.memory_info().rss / 1024 / 1024:.2f} MB')
print(f'未回收對象數量: {len(gc.garbage)}')
"
```

**記憶體洩漏分析工具**：
```python
# scripts/memory-profiler.py
import tracemalloc
import asyncio
import gc
from typing import Dict, List

class MemoryProfiler:
    """記憶體分析器"""
    
    def __init__(self):
        self.snapshots = []
    
    def start_tracing(self):
        """開始記憶體追蹤"""
        tracemalloc.start()
        print("記憶體追蹤已啟動")
    
    def take_snapshot(self, label: str = None):
        """拍攝記憶體快照"""
        if not tracemalloc.is_tracing():
            print("記憶體追蹤未啟動")
            return
        
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({
            'label': label or f'snapshot_{len(self.snapshots)}',
            'snapshot': snapshot,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        print(f"記憶體快照已拍攝: {label}")
    
    def compare_snapshots(self, start_idx: int = 0, end_idx: int = -1):
        """比較記憶體快照"""
        if len(self.snapshots) < 2:
            print("需要至少兩個快照進行比較")
            return
        
        start_snapshot = self.snapshots[start_idx]['snapshot']
        end_snapshot = self.snapshots[end_idx]['snapshot']
        
        top_stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        
        print(f"\n記憶體變化分析 ({self.snapshots[start_idx]['label']} -> {self.snapshots[end_idx]['label']}):")
        print("=" * 60)
        
        for index, stat in enumerate(top_stats[:10], 1):
            print(f"{index:2d}. {stat}")
    
    def get_current_memory_info(self):
        """獲取當前記憶體資訊"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent(),
            'gc_objects': len(gc.get_objects()),
            'gc_garbage': len(gc.garbage)
        }
    
    def print_memory_info(self):
        """打印記憶體資訊"""
        info = self.get_current_memory_info()
        print(f"RSS 記憶體: {info['rss']:.2f} MB")
        print(f"VMS 記憶體: {info['vms']:.2f} MB") 
        print(f"記憶體百分比: {info['percent']:.2f}%")
        print(f"GC 對象數量: {info['gc_objects']}")
        print(f"GC 垃圾數量: {info['gc_garbage']}")

# 使用範例
async def profile_memory_leak():
    profiler = MemoryProfiler()
    profiler.start_tracing()
    
    # 初始快照
    profiler.take_snapshot("初始狀態")
    profiler.print_memory_info()
    
    # 模擬一些操作
    for i in range(1000):
        # 執行可能導致記憶體洩漏的操作
        await some_operation()
        
        if i % 100 == 0:
            profiler.take_snapshot(f"操作_{i}")
            profiler.print_memory_info()
    
    # 比較快照
    profiler.compare_snapshots(0, -1)
```

### 3. AI 服務問題

#### 3.1 AI API 調用失敗

**症狀**：
- AI 生成請求失敗
- API 金鑰錯誤
- 請求配額超限

**診斷步驟**：
```bash
# 檢查 AI 服務日誌
docker-compose logs ai-service --tail=50

# 測試 API 金鑰有效性
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# 檢查配額使用情況
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/usage
```

**AI 服務診斷工具**：
```python
# scripts/ai-service-diagnostics.py
import asyncio
import aiohttp
import os
from datetime import datetime

class AIServiceDiagnostics:
    """AI 服務診斷工具"""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'base_url': 'https://api.openai.com/v1',
                'test_endpoint': '/models'
            },
            'gemini': {
                'api_key': os.getenv('GEMINI_API_KEY'),
                'base_url': 'https://generativelanguage.googleapis.com/v1',
                'test_endpoint': '/models'
            }
        }
    
    async def test_provider_connectivity(self, provider_name: str):
        """測試提供商連接性"""
        provider = self.providers.get(provider_name)
        if not provider:
            return {'status': 'error', 'message': f'未知提供商: {provider_name}'}
        
        if not provider['api_key']:
            return {
                'status': 'error', 
                'message': f'{provider_name} API 金鑰未設置'
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {provider["api_key"]}',
                    'Content-Type': 'application/json'
                }
                
                url = provider['base_url'] + provider['test_endpoint']
                
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return {
                            'status': 'success',
                            'message': f'{provider_name} 連接正常',
                            'response_time': response.headers.get('response-time')
                        }
                    else:
                        text = await response.text()
                        return {
                            'status': 'error',
                            'message': f'{provider_name} API 錯誤: {response.status}',
                            'details': text
                        }
        
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'message': f'{provider_name} 連接超時'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'{provider_name} 連接失敗: {str(e)}'
            }
    
    async def test_all_providers(self):
        """測試所有提供商"""
        print(f"🤖 AI 服務診斷 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        tasks = []
        for provider_name in self.providers.keys():
            tasks.append(self.test_provider_connectivity(provider_name))
        
        results = await asyncio.gather(*tasks)
        
        for provider_name, result in zip(self.providers.keys(), results):
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {provider_name.upper()}: {result['message']}")
            
            if result['status'] == 'error' and 'details' in result:
                print(f"   詳情: {result['details'][:100]}...")
    
    async def test_generation(self, provider_name: str, prompt: str = "Hello"):
        """測試文字生成功能"""
        if provider_name == 'openai':
            return await self._test_openai_generation(prompt)
        elif provider_name == 'gemini':
            return await self._test_gemini_generation(prompt)
        else:
            return {'status': 'error', 'message': '不支援的提供商'}
    
    async def _test_openai_generation(self, prompt: str):
        """測試 OpenAI 文字生成"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.providers["openai"]["api_key"]}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 50
                }
                
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'status': 'success',
                            'message': 'OpenAI 生成測試成功',
                            'generated_text': result['choices'][0]['message']['content']
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'status': 'error',
                            'message': f'OpenAI 生成失敗: {response.status}',
                            'details': error_text
                        }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'OpenAI 生成測試失敗: {str(e)}'
            }

# 運行診斷
if __name__ == "__main__":
    diagnostics = AIServiceDiagnostics()
    asyncio.run(diagnostics.test_all_providers())
```

#### 3.2 影片處理卡住

**症狀**：
- 影片處理狀態長時間停留在某個階段
- 處理進度不更新
- 任務佇列堆積

**診斷步驟**：
```bash
# 檢查 Celery 任務狀態
docker-compose exec api-gateway celery -A app.celery inspect active

# 檢查任務佇列長度
docker-compose exec redis redis-cli llen celery

# 檢查正在處理的任務
docker-compose exec api-gateway celery -A app.celery inspect reserved

# 檢查失敗的任務
docker-compose exec api-gateway celery -A app.celery inspect failed
```

**任務診斷工具**：
```python
# scripts/task-diagnostics.py
import redis
import json
from datetime import datetime, timedelta

class TaskDiagnostics:
    """任務診斷工具"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
    
    def get_queue_stats(self):
        """獲取佇列統計"""
        stats = {}
        
        # 獲取所有佇列
        queues = ['celery', 'video_queue', 'ai_queue', 'social_queue']
        
        for queue in queues:
            length = self.redis_client.llen(queue)
            stats[queue] = {
                'length': length,
                'status': 'normal' if length < 100 else 'warning' if length < 500 else 'critical'
            }
        
        return stats
    
    def get_stuck_tasks(self, threshold_minutes: int = 30):
        """獲取卡住的任務"""
        stuck_tasks = []
        
        # 從資料庫查詢長時間處理的任務
        # 這裡需要根據實際的資料庫結構調整
        query = """
        SELECT id, user_id, status, created_at, updated_at, processing_stages
        FROM videos 
        WHERE status = 'processing' 
        AND updated_at < NOW() - INTERVAL %s MINUTE
        ORDER BY updated_at DESC
        """
        
        # 執行查詢邏輯...
        
        return stuck_tasks
    
    def restart_stuck_tasks(self, task_ids: list):
        """重新啟動卡住的任務"""
        for task_id in task_ids:
            try:
                # 重置任務狀態
                # 重新提交到佇列
                print(f"重新啟動任務: {task_id}")
            except Exception as e:
                print(f"重新啟動任務 {task_id} 失敗: {e}")
    
    def clear_failed_tasks(self):
        """清理失敗的任務"""
        # 清理 Redis 中的失敗任務記錄
        failed_tasks = self.redis_client.keys("celery-task-meta-*")
        
        for task_key in failed_tasks:
            task_data = self.redis_client.get(task_key)
            if task_data:
                task_info = json.loads(task_data)
                if task_info.get('status') == 'FAILURE':
                    self.redis_client.delete(task_key)
                    print(f"已清理失敗任務: {task_key}")
    
    def monitor_task_performance(self):
        """監控任務效能"""
        # 統計各階段平均處理時間
        # 識別效能瓶頸
        # 生成效能報告
        pass

# 使用範例
if __name__ == "__main__":
    diagnostics = TaskDiagnostics()
    
    print("📊 任務佇列統計:")
    stats = diagnostics.get_queue_stats()
    for queue, info in stats.items():
        status_icon = {"normal": "✅", "warning": "⚠️", "critical": "🚨"}[info['status']]
        print(f"{status_icon} {queue}: {info['length']} 個任務")
    
    print("\n🔍 檢查卡住的任務:")
    stuck_tasks = diagnostics.get_stuck_tasks()
    if stuck_tasks:
        print(f"發現 {len(stuck_tasks)} 個卡住的任務")
        for task in stuck_tasks:
            print(f"- 任務 {task['id']}: 卡住 {task['stuck_duration']} 分鐘")
    else:
        print("未發現卡住的任務")
```

### 4. 資料庫問題

#### 4.1 資料庫效能下降

**症狀**：
- 查詢回應時間增加
- 資料庫 CPU 使用率高
- 連接數達到上限

**診斷步驟**：
```sql
-- 檢查慢查詢
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements 
WHERE mean_time > 100  -- 平均執行時間 > 100ms
ORDER BY mean_time DESC 
LIMIT 20;

-- 檢查表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- 檢查索引使用情況
SELECT 
    indexrelname as index_name,
    relname as table_name,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- 檢查當前連接
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity 
WHERE state != 'idle';
```

**資料庫優化工具**：
```python
# scripts/db-optimization.py
import asyncpg
import asyncio
from datetime import datetime

class DatabaseOptimizer:
    """資料庫優化工具"""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
    
    async def analyze_slow_queries(self):
        """分析慢查詢"""
        conn = await asyncpg.connect(self.dsn)
        
        slow_queries = await conn.fetch("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            WHERE mean_time > 100
            ORDER BY mean_time DESC 
            LIMIT 10
        """)
        
        print("🐌 慢查詢分析:")
        print("=" * 80)
        
        for query in slow_queries:
            print(f"平均執行時間: {query['mean_time']:.2f}ms")
            print(f"調用次數: {query['calls']}")
            print(f"命中率: {query['hit_percent']:.1f}%")
            print(f"查詢: {query['query'][:100]}...")
            print("-" * 40)
        
        await conn.close()
    
    async def suggest_indexes(self):
        """建議創建索引"""
        conn = await asyncpg.connect(self.dsn)
        
        # 查找可能需要索引的查詢
        queries_need_indexes = await conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                seq_tup_read / seq_scan as avg_seq_read
            FROM pg_stat_user_tables 
            WHERE seq_scan > 0
            AND seq_tup_read / seq_scan > 1000
            ORDER BY seq_tup_read DESC
        """)
        
        print("📚 索引建議:")
        print("=" * 60)
        
        for table in queries_need_indexes:
            print(f"表: {table['tablename']}")
            print(f"順序掃描次數: {table['seq_scan']}")
            print(f"平均掃描行數: {table['avg_seq_read']:.0f}")
            print(f"建議: 考慮為常用查詢條件添加索引")
            print("-" * 30)
        
        await conn.close()
    
    async def check_table_bloat(self):
        """檢查表膨脹"""
        conn = await asyncpg.connect(self.dsn)
        
        bloat_info = await conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
                n_dead_tup,
                n_live_tup,
                CASE WHEN n_live_tup > 0 
                     THEN round(100 * n_dead_tup / (n_live_tup + n_dead_tup), 2)
                     ELSE 0 
                END as dead_tuple_percent
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 1000
            ORDER BY dead_tuple_percent DESC
        """)
        
        print("💀 表膨脹檢查:")
        print("=" * 60)
        
        for table in bloat_info:
            if table['dead_tuple_percent'] > 10:
                print(f"⚠️  表: {table['tablename']}")
                print(f"   大小: {table['table_size']}")
                print(f"   死元組比例: {table['dead_tuple_percent']:.1f}%")
                print(f"   建議: 執行 VACUUM ANALYZE {table['tablename']}")
                print()
        
        await conn.close()
    
    async def optimize_database(self):
        """執行資料庫優化"""
        conn = await asyncpg.connect(self.dsn)
        
        print("🔧 執行資料庫優化...")
        
        # 更新統計信息
        await conn.execute("ANALYZE;")
        print("✅ 統計信息已更新")
        
        # 檢查需要 VACUUM 的表
        tables_need_vacuum = await conn.fetch("""
            SELECT tablename 
            FROM pg_stat_user_tables 
            WHERE n_dead_tup > n_live_tup * 0.1
            AND n_dead_tup > 1000
        """)
        
        for table in tables_need_vacuum:
            table_name = table['tablename']
            print(f"🧹 對表 {table_name} 執行 VACUUM...")
            await conn.execute(f"VACUUM ANALYZE {table_name};")
        
        print("✅ 資料庫優化完成")
        await conn.close()

# 使用範例
async def main():
    optimizer = DatabaseOptimizer("postgresql://user:pass@localhost/db")
    
    await optimizer.analyze_slow_queries()
    await optimizer.suggest_indexes()
    await optimizer.check_table_bloat()
    await optimizer.optimize_database()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 4.2 資料庫連接洩漏

**症狀**：
- 資料庫連接數持續增長
- `too many connections` 錯誤
- 應用無法獲取新連接

**解決方案**：
```python
# 連接池監控和管理
import asyncio
import asyncpg
from datetime import datetime

class ConnectionPoolMonitor:
    """連接池監控器"""
    
    def __init__(self, pool):
        self.pool = pool
        self.connection_history = []
    
    def log_connection_event(self, event_type: str, details: dict = None):
        """記錄連接事件"""
        event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'pool_size': self.pool.get_size(),
            'pool_free': self.pool.get_idle_size(),
            'pool_used': self.pool.get_size() - self.pool.get_idle_size(),
            'details': details or {}
        }
        
        self.connection_history.append(event)
        
        # 保留最近 1000 條記錄
        if len(self.connection_history) > 1000:
            self.connection_history = self.connection_history[-1000:]
    
    async def check_connection_leaks(self):
        """檢查連接洩漏"""
        if not self.connection_history:
            return []
        
        # 分析連接使用模式
        recent_events = self.connection_history[-100:]  # 最近 100 個事件
        
        # 計算平均連接使用率
        avg_used = sum(event['pool_used'] for event in recent_events) / len(recent_events)
        max_used = max(event['pool_used'] for event in recent_events)
        
        warnings = []
        
        if avg_used > self.pool.get_size() * 0.8:
            warnings.append(f"平均連接使用率過高: {avg_used:.1f}/{self.pool.get_size()}")
        
        if max_used >= self.pool.get_size():
            warnings.append("連接池已滿，可能存在連接洩漏")
        
        # 檢查長時間佔用的連接
        current_time = datetime.now()
        long_running_connections = [
            event for event in recent_events 
            if event['event_type'] == 'acquire' and 
            (current_time - event['timestamp']).total_seconds() > 300  # 5分鐘
        ]
        
        if long_running_connections:
            warnings.append(f"發現 {len(long_running_connections)} 個長時間佔用的連接")
        
        return warnings
    
    def get_pool_stats(self):
        """獲取連接池統計"""
        return {
            'total_size': self.pool.get_size(),
            'idle_size': self.pool.get_idle_size(),
            'used_size': self.pool.get_size() - self.pool.get_idle_size(),
            'usage_percent': (self.pool.get_size() - self.pool.get_idle_size()) / self.pool.get_size() * 100
        }

# 連接管理上下文管理器
class ManagedConnection:
    """託管連接上下文管理器"""
    
    def __init__(self, pool, monitor=None, timeout=30):
        self.pool = pool
        self.monitor = monitor
        self.timeout = timeout
        self.connection = None
        self.acquired_at = None
    
    async def __aenter__(self):
        try:
            self.connection = await asyncio.wait_for(
                self.pool.acquire(), 
                timeout=self.timeout
            )
            self.acquired_at = datetime.now()
            
            if self.monitor:
                self.monitor.log_connection_event('acquire', {
                    'connection_id': id(self.connection)
                })
            
            return self.connection
            
        except asyncio.TimeoutError:
            raise Exception(f"獲取資料庫連接超時 ({self.timeout}s)")
        except Exception as e:
            if self.monitor:
                self.monitor.log_connection_event('acquire_failed', {
                    'error': str(e)
                })
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            try:
                await self.pool.release(self.connection)
                
                if self.monitor and self.acquired_at:
                    duration = (datetime.now() - self.acquired_at).total_seconds()
                    self.monitor.log_connection_event('release', {
                        'connection_id': id(self.connection),
                        'duration': duration
                    })
                
            except Exception as e:
                if self.monitor:
                    self.monitor.log_connection_event('release_failed', {
                        'error': str(e)
                    })

# 使用範例
pool = await asyncpg.create_pool(
    "postgresql://user:pass@localhost/db",
    min_size=5,
    max_size=20
)

monitor = ConnectionPoolMonitor(pool)

# 使用託管連接
async with ManagedConnection(pool, monitor) as conn:
    result = await conn.fetch("SELECT * FROM users LIMIT 10")

# 定期檢查連接洩漏
async def periodic_leak_check():
    while True:
        warnings = await monitor.check_connection_leaks()
        if warnings:
            for warning in warnings:
                print(f"⚠️  連接池警告: {warning}")
        
        stats = monitor.get_pool_stats()
        print(f"連接池狀態: {stats['used_size']}/{stats['total_size']} ({stats['usage_percent']:.1f}%)")
        
        await asyncio.sleep(60)  # 每分鐘檢查一次

# 在後台運行監控
asyncio.create_task(periodic_leak_check())
```

### 5. 網路和連接問題

#### 5.1 服務間通信失敗

**症狀**：
- 服務間 API 調用失敗
- 網路連接超時
- DNS 解析問題

**診斷步驟**：
```bash
# 檢查 Docker 網路
docker network ls
docker network inspect autovideo_default

# 檢查服務間連通性
docker-compose exec api-gateway ping video-service
docker-compose exec api-gateway nslookup video-service

# 檢查端口開放狀態
docker-compose exec api-gateway netstat -tlnp

# 測試服務間 HTTP 連接
docker-compose exec api-gateway curl -f http://video-service:8004/health
```

**網路診斷工具**：
```bash
#!/bin/bash
# scripts/network-diagnostics.sh

echo "🌐 網路診斷開始..."

# 檢查所有服務的網路連接
services=("api-gateway" "auth-service" "video-service" "ai-service" "postgres" "redis")

for service in "${services[@]}"; do
    echo "檢查 $service 的網路狀態..."
    
    # 檢查容器是否運行
    if ! docker-compose ps $service | grep -q "Up"; then
        echo "❌ $service 容器未運行"
        continue
    fi
    
    # 檢查端口監聽
    docker-compose exec $service netstat -tln 2>/dev/null | grep LISTEN | head -5
    
    # 測試與其他服務的連通性
    for target_service in "${services[@]}"; do
        if [ "$service" != "$target_service" ]; then
            if docker-compose exec $service ping -c 1 -W 2 $target_service >/dev/null 2>&1; then
                echo "✅ $service -> $target_service: 連通"
            else
                echo "❌ $service -> $target_service: 不通"
            fi
        fi
    done
    
    echo "---"
done

# 檢查外部網路連接
echo "檢查外部網路連接..."
if docker-compose exec api-gateway ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "✅ 外部網路: 正常"
else
    echo "❌ 外部網路: 異常"
fi

# 檢查 DNS 解析
echo "檢查 DNS 解析..."
if docker-compose exec api-gateway nslookup google.com >/dev/null 2>&1; then
    echo "✅ DNS 解析: 正常"
else
    echo "❌ DNS 解析: 異常"
fi
```

### 6. 監控和告警問題

#### 6.1 指標收集失敗

**症狀**：
- Prometheus 無法採集指標
- Grafana 儀表板顯示無數據
- 告警規則不觸發

**解決方案**：
```bash
# 檢查 Prometheus 配置
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# 檢查指標端點
curl http://localhost:8000/metrics
curl http://localhost:9090/metrics

# 查看 Prometheus 目標狀態
curl http://localhost:9090/api/v1/targets

# 重新載入 Prometheus 配置
curl -X POST http://localhost:9090/-/reload
```

**指標診斷工具**：
```python
# scripts/metrics-diagnostics.py
import requests
import json
from datetime import datetime

class MetricsDiagnostics:
    """指標診斷工具"""
    
    def __init__(self, prometheus_url="http://localhost:9090"):
        self.prometheus_url = prometheus_url
    
    def check_targets(self):
        """檢查 Prometheus 目標狀態"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets")
            if response.status_code == 200:
                data = response.json()
                targets = data['data']['activeTargets']
                
                print("🎯 Prometheus 目標狀態:")
                print("=" * 50)
                
                for target in targets:
                    job_name = target['labels']['job']
                    instance = target['labels']['instance']
                    health = target['health']
                    last_error = target.get('lastError', '')
                    
                    status_icon = "✅" if health == 'up' else "❌"
                    print(f"{status_icon} {job_name} ({instance}): {health}")
                    
                    if last_error:
                        print(f"   錯誤: {last_error}")
            else:
                print(f"❌ 無法獲取目標狀態: {response.status_code}")
        
        except Exception as e:
            print(f"❌ 檢查目標狀態失敗: {e}")
    
    def check_metrics_availability(self):
        """檢查關鍵指標可用性"""
        key_metrics = [
            'http_requests_total',
            'http_request_duration_seconds',
            'database_query_duration_seconds',
            'video_processing_duration_seconds'
        ]
        
        print("\n📊 關鍵指標可用性:")
        print("=" * 50)
        
        for metric in key_metrics:
            try:
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': metric}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['data']['result']:
                        print(f"✅ {metric}: 可用")
                    else:
                        print(f"⚠️  {metric}: 無數據")
                else:
                    print(f"❌ {metric}: 查詢失敗")
            
            except Exception as e:
                print(f"❌ {metric}: 檢查失敗 - {e}")
    
    def check_alerting_rules(self):
        """檢查告警規則"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules")
            if response.status_code == 200:
                data = response.json()
                rule_groups = data['data']['groups']
                
                print("\n🚨 告警規則狀態:")
                print("=" * 50)
                
                for group in rule_groups:
                    group_name = group['name']
                    print(f"規則組: {group_name}")
                    
                    for rule in group['rules']:
                        rule_name = rule['name']
                        rule_state = rule['state']
                        
                        status_icon = {
                            'inactive': "✅",
                            'pending': "⚠️ ",
                            'firing': "🚨"
                        }.get(rule_state, "❓")
                        
                        print(f"  {status_icon} {rule_name}: {rule_state}")
                        
                        if rule_state == 'firing':
                            print(f"    告警詳情: {rule.get('annotations', {}).get('description', 'N/A')}")
            else:
                print(f"❌ 無法獲取告警規則: {response.status_code}")
        
        except Exception as e:
            print(f"❌ 檢查告警規則失敗: {e}")

# 使用範例
if __name__ == "__main__":
    diagnostics = MetricsDiagnostics()
    
    diagnostics.check_targets()
    diagnostics.check_metrics_availability()
    diagnostics.check_alerting_rules()
```

## 🚨 緊急情況處理

### 系統完全當機恢復流程

```bash
#!/bin/bash
# scripts/emergency-recovery.sh

echo "🚨 緊急恢復流程啟動..."

# 1. 停止所有服務
echo "停止所有服務..."
docker-compose down

# 2. 檢查系統資源
echo "檢查系統資源..."
df -h
free -h
docker system df

# 3. 清理系統資源（如果需要）
echo "清理 Docker 資源..."
docker system prune -f
docker volume prune -f

# 4. 檢查配置文件
echo "檢查配置文件..."
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在"
    cp .env.example .env
    echo "⚠️  請編輯 .env 文件後重新運行"
    exit 1
fi

# 5. 重新啟動核心服務
echo "啟動核心服務..."
docker-compose up -d postgres redis

# 等待資料庫就緒
echo "等待資料庫啟動..."
sleep 30

if ! docker-compose exec postgres pg_isready -U autovideo; then
    echo "❌ 資料庫啟動失敗"
    exit 1
fi

# 6. 啟動應用服務
echo "啟動應用服務..."
docker-compose up -d

# 7. 等待服務就緒
echo "等待服務就緒..."
sleep 60

# 8. 執行健康檢查
echo "執行健康檢查..."
if curl -f http://localhost:8000/health; then
    echo "✅ 系統恢復成功"
else
    echo "❌ 系統恢復失敗，請檢查日誌"
    docker-compose logs --tail=20
fi

# 9. 發送恢復通知
curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-type: application/json' \
    --data '{"text":"🚨 Auto Video 系統緊急恢復完成"}'
```

### 數據恢復流程

```bash
#!/bin/bash
# scripts/data-recovery.sh

BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "用法: $0 <備份日期>"
    echo "可用備份:"
    ls -la backup/database/postgres_backup_*.sql | head -5
    exit 1
fi

echo "🔄 開始數據恢復流程..."
echo "恢復點: $BACKUP_DATE"

# 確認操作
read -p "這將覆蓋當前數據，確定繼續嗎？(yes/no): " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "操作已取消"
    exit 1
fi

# 1. 創建當前數據的緊急備份
echo "創建緊急備份..."
./scripts/backup.sh

# 2. 停止應用服務
echo "停止應用服務..."
docker-compose stop api-gateway auth-service video-service ai-service

# 3. 恢復資料庫
echo "恢復資料庫..."
docker-compose exec -T postgres dropdb -U autovideo autovideo_prod
docker-compose exec -T postgres createdb -U autovideo autovideo_prod
docker-compose exec -T postgres psql -U autovideo -d autovideo_prod < backup/database/postgres_backup_$BACKUP_DATE.sql

# 4. 恢復文件
echo "恢復文件..."
if [ -f "backup/files/uploads_backup_$BACKUP_DATE.tar.gz" ]; then
    tar -xzf backup/files/uploads_backup_$BACKUP_DATE.tar.gz -C data/
fi

# 5. 重啟服務
echo "重啟服務..."
docker-compose up -d

# 6. 驗證恢復
echo "驗證恢復..."
sleep 30

if curl -f http://localhost:8000/health; then
    echo "✅ 數據恢復成功"
else
    echo "❌ 數據恢復失敗"
    exit 1
fi
```

## 📞 支援聯繫

### 問題回報

當遇到無法解決的問題時，請提供以下資訊：

1. **系統資訊**：
```bash
# 收集系統資訊
echo "=== 系統資訊 ===" > support-info.txt
uname -a >> support-info.txt
docker --version >> support-info.txt
docker-compose --version >> support-info.txt

echo "=== 服務狀態 ===" >> support-info.txt
docker-compose ps >> support-info.txt

echo "=== 系統資源 ===" >> support-info.txt
free -h >> support-info.txt
df -h >> support-info.txt

echo "=== 錯誤日誌 ===" >> support-info.txt
docker-compose logs --tail=100 >> support-info.txt 2>&1
```

2. **重現步驟**：
   - 詳細描述操作步驟
   - 預期結果 vs 實際結果
   - 錯誤截圖或日誌

3. **環境配置**：
   - 部署方式 (Docker Compose / Kubernetes)
   - 環境變數配置
   - 自定義修改

### 聯繫方式

- **GitHub Issues**: [項目 Issues 頁面]
- **技術支援**: support@autovideo.com
- **緊急聯繫**: +886 2 1234 5678
- **文檔問題**: docs@autovideo.com

---

## 📚 相關資源

- [📖 開發者指南](DEVELOPER_GUIDE.md)
- [🏗️ 架構文檔](ARCHITECTURE.md)
- [🚀 部署指南](DEPLOYMENT.md)
- [🔌 API 文檔](API_REFERENCE.md)

---

*本故障排除指南會持續更新，如有新的問題模式或解決方案，歡迎透過 GitHub Issues 貢獻。*