# AI 服務整合指南

本文檔介紹如何在 Auto Video Generation System 中使用新整合的 AI 服務。

## 🆕 新增 AI 服務

### Suno.ai 音樂生成服務
- **功能**: AI 驅動的音樂和歌曲生成
- **用途**: 為短影片生成背景音樂
- **位置**: `services/music-service/suno_client.py`

### Google Gemini Pro
- **功能**: 文字生成、多模態 AI、內容分析
- **用途**: 腳本生成、趨勢分析、內容優化
- **位置**: `services/ai-service/gemini_client.py`

### AI 服務編排器
- **功能**: 統一管理多個 AI 服務，自動故障轉移
- **用途**: 智能路由、負載均衡、成本優化
- **位置**: `services/ai-service/ai_orchestrator.py`

## 🚀 快速開始

### 1. 環境配置

```bash
# 設置 API 金鑰
export GEMINI_API_KEY="your_gemini_api_key"
export SUNO_API_KEY="your_suno_api_key"

# 現有的 API 金鑰
export OPENAI_API_KEY="your_openai_api_key"
export STABILITY_API_KEY="your_stability_api_key"
export ELEVENLABS_API_KEY="your_elevenlabs_api_key"
```

### 2. 基本使用

#### Gemini Pro 文字生成

```python
from services.ai_service.gemini_client import generate_video_script

# 生成影片腳本
script = await generate_video_script(
    topic="AI 技術發展",
    platform="tiktok",
    style="educational"
)
```

#### Suno.ai 音樂生成

```python
from services.music_service.suno_client import generate_music_for_video

# 生成背景音樂
music = await generate_music_for_video(
    prompt="輕快的科技風背景音樂",
    duration=30,
    style="electronic, upbeat"
)
```

#### AI 服務編排器

```python
from services.ai_service.ai_orchestrator import generate_text_with_fallback

# 智能文字生成（自動故障轉移）
text = await generate_text_with_fallback(
    prompt="創作短影片腳本",
    primary_provider="gemini",
    fallback_provider="openai"
)
```

### 3. 運行示例

```bash
# 運行完整示例
python examples/ai_integration_demo.py

# 或者測試個別組件
python services/ai-service/gemini_client.py
python services/music-service/suno_client.py
python services/ai-service/ai_orchestrator.py
```

## 📋 功能特性

### Gemini Pro 客戶端

**核心功能:**
- ✅ 文字生成與對話
- ✅ 圖像分析（多模態）
- ✅ 內容分析與優化
- ✅ 腳本生成
- ✅ 趨勢分析
- ✅ 成本追蹤整合

**使用範例:**

```python
from services.ai_service.gemini_client import GeminiClient, GeminiGenerationConfig

async with GeminiClient(api_key="your_key") as client:
    # 基本文字生成
    result = await client.generate_content(
        prompt="寫一個科技短影片腳本",
        generation_config=GeminiGenerationConfig(
            temperature=0.8,
            max_output_tokens=300
        )
    )
    
    # 圖像分析
    with open("image.jpg", "rb") as f:
        image_data = f.read()
    
    analysis = await client.analyze_image(
        image_data=image_data,
        prompt="分析這張圖片的內容和情感"
    )
    
    # 內容優化
    optimized = await client.optimize_content(
        content="原始腳本內容",
        platform="tiktok",
        target_audience="年輕人"
    )
```

### Suno.ai 客戶端

**核心功能:**
- ✅ AI 音樂生成
- ✅ 多種音樂風格
- ✅ 可配置時長
- ✅ 純音樂或有人聲
- ✅ 文件下載
- ✅ 成本追蹤整合

**使用範例:**

```python
from services.music_service.suno_client import SunoClient, MusicGenerationRequest

async with SunoClient(api_key="your_key") as client:
    # 創建音樂生成請求
    request = MusicGenerationRequest(
        prompt="歡快的背景音樂，適合產品介紹",
        duration=30,
        style="upbeat, commercial, electronic",
        instrumental=True,
        title="產品介紹背景音樂"
    )
    
    # 生成音樂
    result = await client.generate_music(request)
    
    if result.status == "completed":
        # 下載音樂文件
        from pathlib import Path
        output_path = Path("generated_music.mp3")
        await client.download_audio(result.audio_url, output_path)
        
        print(f"音樂已生成: {result.title}")
        print(f"時長: {result.duration}秒")
        print(f"文件: {output_path}")
```

### AI 服務編排器

**核心功能:**
- ✅ 多提供商統一管理
- ✅ 自動故障轉移
- ✅ 智能負載均衡
- ✅ 實時健康監控
- ✅ 成本優化
- ✅ 性能指標追蹤

**架構優勢:**

```python
from services.ai_service.ai_orchestrator import AIOrchestrator, AIRequest, AITaskType

orchestrator = AIOrchestrator()

# 自動選擇最佳提供商
request = AIRequest(
    task_type=AITaskType.TEXT_GENERATION,
    prompt="生成影片標題",
    fallback_enabled=True  # 啟用自動故障轉移
)

response = await orchestrator.process_request(request)

# 檢查所有提供商狀態
status = await orchestrator.get_provider_status()
for provider, stats in status.items():
    print(f"{provider}: 成功率 {stats['success_rate']:.2%}")
```

## 🔧 配置管理

### 統一配置系統

新的 AI 服務已整合到統一配置系統中：

```json
{
  "ai_services": {
    "text_generation": {
      "primary_provider": "openai",
      "fallback_provider": "gemini",
      "providers": {
        "openai": {
          "model": "gpt-3.5-turbo",
          "max_tokens": 300,
          "temperature": 0.8
        },
        "gemini": {
          "model": "gemini-pro",
          "max_tokens": 300,
          "temperature": 0.8
        }
      }
    },
    "music_generation": {
      "provider": "suno",
      "model": "chirp-v3",
      "default_duration": 30,
      "instrumental_only": true,
      "quality": "standard"
    }
  },
  "cost_control": {
    "api_rate_limits": {
      "gemini_requests_per_hour": 120,
      "suno_requests_per_hour": 20
    }
  }
}
```

### 模式切換

```bash
# 切換到企業模式（支援所有 AI 服務）
./scripts/switch_mode.sh enterprise

# 切換到啟動模式（基本 AI 服務）
./scripts/switch_mode.sh startup
```

## 💰 成本監控

### 新增成本追蹤

系統已更新以支援新 AI 服務的成本追蹤：

**Gemini Pro 定價:**
- Gemini Pro: $0.0005/1K 輸入 tokens, $0.0015/1K 輸出 tokens
- Gemini 1.5 Pro: $0.0035/1K 輸入 tokens, $0.0105/1K 輸出 tokens
- Gemini 1.5 Flash: $0.000075/1K 輸入 tokens, $0.0003/1K 輸出 tokens

**Suno.ai 定價:**
- Chirp v3: ~$0.5/分鐘（估算）
- Chirp v3.5: ~$0.7/分鐘（估算）

### 成本監控使用

```python
from monitoring.cost_tracker import get_cost_tracker

cost_tracker = get_cost_tracker()

# 檢查今日預算
budget_status = await cost_tracker.check_budget_status()
print(f"已使用: ${budget_status['current_cost']:.2f}")
print(f"剩餘: ${budget_status['remaining_budget']:.2f}")

# 獲取成本報告
from datetime import date
daily_summary = await cost_tracker.get_daily_summary(date.today())
print(f"Gemini 成本: ${daily_summary.providers_breakdown.get('google', 0):.2f}")
print(f"Suno 成本: ${daily_summary.providers_breakdown.get('suno', 0):.2f}")
```

## 🧪 測試和驗證

### 運行測試

```bash
# 測試 AI 服務整合
python -m pytest tests/test_ai_services.py -v

# 測試成本追蹤
python -m pytest tests/test_cost_tracker.py -v

# 運行完整測試套件
python scripts/run_tests.py --type all
```

### 健康檢查

```bash
# 檢查所有服務健康狀態
python monitoring/health_monitor.py once

# 檢查 AI 服務可用性
python examples/ai_integration_demo.py
```

## 🔄 工作流程整合

### 完整影片生成流程

```python
async def generate_video_with_ai():
    """使用新 AI 服務的完整影片生成流程"""
    
    # 1. 使用 Gemini 生成腳本
    script = await generate_video_script(
        topic="科技趨勢",
        platform="tiktok",
        style="engaging"
    )
    
    # 2. 使用 Suno 生成背景音樂
    music = await generate_music_for_video(
        prompt="科技感背景音樂",
        duration=30,
        style="futuristic, upbeat"
    )
    
    # 3. 使用編排器進行內容分析
    from services.ai_service.ai_orchestrator import AIOrchestrator, AIRequest, AITaskType
    
    orchestrator = AIOrchestrator()
    analysis_request = AIRequest(
        task_type=AITaskType.TREND_ANALYSIS,
        prompt=script
    )
    
    analysis = await orchestrator.process_request(analysis_request)
    
    # 4. 整合到影片生成系統
    video_config = {
        "script": script,
        "background_music": music.audio_url if music else None,
        "optimization_hints": analysis.content if analysis.success else None
    }
    
    return video_config
```

### 與現有系統整合

新的 AI 服務已無縫整合到現有的影片生成流程中：

1. **自動腳本生成**: `scripts/auto_trends_video.py` 現在支援 Gemini 作為 OpenAI 的備用選項
2. **音樂生成**: 可選的背景音樂生成功能已添加到影片處理流程
3. **成本控制**: 所有新服務都受到統一的預算管理和成本追蹤

## 🛠️ 開發工具

### VS Code 配置

專案已包含完整的 VS Code 開發環境配置：

- **Extensions**: 推薦的 Python、AI 開發擴展
- **Settings**: 統一的代碼格式化和 linting 規則
- **Launch**: 預配置的調試配置
- **Tasks**: 常用開發任務自動化

### Cursor Pro 支援

專案已針對 Cursor Pro 進行優化：

- **`.cursorrules`**: 專案特定的 AI 協助規則
- **Context**: 結構化的項目上下文信息
- **Code Style**: 統一的代碼風格指南

## 📊 監控和分析

### 實時儀表板

```bash
# 啟動分析儀表板
./scripts/start_analytics.sh dashboard

# 生成詳細報告
./scripts/start_analytics.sh report daily
```

### 性能指標

- **響應時間**: 各 AI 服務的平均響應時間
- **成功率**: API 呼叫成功率統計
- **成本分析**: 實時成本追蹤和預算使用
- **使用模式**: AI 服務使用頻率和模式分析

## 🚨 故障排除

### 常見問題

**1. API 金鑰無效**
```bash
# 檢查環境變數
echo $GEMINI_API_KEY
echo $SUNO_API_KEY

# 測試 API 連接
python -c "
import os
from services.ai_service.gemini_client import GeminiClient
print('Gemini API Key:', 'OK' if os.getenv('GEMINI_API_KEY') else 'Missing')
"
```

**2. 服務無回應**
```bash
# 檢查服務健康狀態
python monitoring/health_monitor.py once

# 檢查網路連接
curl -I https://generativelanguage.googleapis.com/
curl -I https://api.sunoai.com/
```

**3. 成本超限**
```bash
# 檢查當前成本
python monitoring/cost_tracker.py status

# 調整預算限制
# 編輯 config/current-config.json 中的 daily_budget_usd
```

### 調試模式

```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用調試模式運行示例
python examples/ai_integration_demo.py
```

## 🔜 未來計劃

### 即將推出的功能

1. **更多 AI 提供商**: Claude, PaLM 2, LLaMA 2
2. **智能成本優化**: 基於使用模式的動態成本控制
3. **A/B 測試**: AI 生成內容的 A/B 測試框架
4. **品質評估**: 自動內容品質評估和改進建議
5. **多語言支援**: 擴展到更多語言和地區

### 貢獻指南

歡迎貢獻新的 AI 服務整合！請參考：

1. 在 `services/` 下創建新的服務目錄
2. 實現標準的客戶端接口
3. 添加成本追蹤支援
4. 整合到 AI 編排器
5. 添加測試和文檔

---

## 📞 支援

如果遇到問題或需要協助：

1. 查看 `examples/ai_integration_demo.py` 的完整示例
2. 檢查 `monitoring/` 下的日誌和報告
3. 運行 `python scripts/run_tests.py --type all` 進行完整測試
4. 查看各服務的 README 和 docstring 文檔

**Happy Coding! 🚀**