#!/usr/bin/env python3
"""
AI 服務編排器 - 統一管理多個 AI 服務提供商
支援自動故障轉移、負載均衡和智能路由
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# 導入各 AI 客戶端
try:
    from services.ai_service.gemini_client import (
        GeminiClient,
        GeminiGenerationConfig,
    )

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini 客戶端不可用")

try:
    from services.music_service.suno_client import (
        MusicGenerationRequest,
        SunoClient,
    )

    SUNO_AVAILABLE = True
except ImportError:
    SUNO_AVAILABLE = False
    logging.warning("Suno 客戶端不可用")

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """AI 服務提供商"""

    OPENAI = "openai"
    GEMINI = "gemini"
    STABILITY_AI = "stability_ai"
    ELEVENLABS = "elevenlabs"
    SUNO = "suno"


class AITaskType(Enum):
    """AI 任務類型"""

    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    VOICE_SYNTHESIS = "voice_synthesis"
    MUSIC_GENERATION = "music_generation"
    CONTENT_ANALYSIS = "content_analysis"
    TREND_ANALYSIS = "trend_analysis"


@dataclass
class AIRequest:
    """AI 請求"""

    task_type: AITaskType
    prompt: str
    provider: Optional[AIProvider] = None
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    fallback_enabled: bool = True
    priority: int = 1  # 1-5, 5 最高優先級


@dataclass
class AIResponse:
    """AI 回應"""

    success: bool
    content: Any
    provider: AIProvider
    model: str
    duration: float
    cost: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIOrchestrator:
    """AI 服務編排器"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.providers = {}
        self.provider_health = {}
        self.provider_metrics = {}
        self._initialize_providers()

        # 初始化成本追蹤
        try:
            from monitoring.cost_tracker import get_cost_tracker

            self.cost_tracker = get_cost_tracker(config_manager)
        except ImportError:
            self.cost_tracker = None
            logger.warning("成本追蹤器不可用")

    def _initialize_providers(self):
        """初始化 AI 服務提供商"""
        # 初始化提供商健康狀態
        for provider in AIProvider:
            self.provider_health[provider] = True
            self.provider_metrics[provider] = {
                "total_requests": 0,
                "successful_requests": 0,
                "average_response_time": 0,
                "last_request_time": 0,
                "error_count": 0,
            }

        logger.info("AI 服務編排器初始化完成")

    async def process_request(self, request: AIRequest) -> AIResponse:
        """處理 AI 請求"""
        start_time = time.time()

        # 選擇提供商
        provider = await self._select_provider(request)
        if not provider:
            return AIResponse(
                success=False,
                content=None,
                provider=AIProvider.OPENAI,
                model="unknown",
                duration=time.time() - start_time,
                error_message="沒有可用的 AI 服務提供商",
            )

        # 執行請求
        try:
            response = await self._execute_request(request, provider)

            # 更新提供商指標
            await self._update_provider_metrics(
                provider, True, time.time() - start_time
            )

            return response

        except Exception as e:
            logger.error(f"AI 請求執行失敗 ({provider.value}): {e}")

            # 更新提供商指標
            await self._update_provider_metrics(
                provider, False, time.time() - start_time
            )

            # 嘗試故障轉移
            if request.fallback_enabled:
                fallback_response = await self._try_fallback(request, provider)
                if fallback_response:
                    return fallback_response

            return AIResponse(
                success=False,
                content=None,
                provider=provider,
                model="unknown",
                duration=time.time() - start_time,
                error_message=str(e),
            )

    async def _select_provider(
        self, request: AIRequest
    ) -> Optional[AIProvider]:
        """選擇最佳 AI 服務提供商"""
        # 如果指定了提供商，直接使用
        if request.provider:
            if self.provider_health.get(request.provider, False):
                return request.provider
            elif not request.fallback_enabled:
                return None

        # 根據任務類型獲取可用提供商
        available_providers = self._get_available_providers(request.task_type)

        if not available_providers:
            return None

        # 智能選擇：考慮健康狀態、成功率、響應時間
        best_provider = None
        best_score = -1

        for provider in available_providers:
            if not self.provider_health.get(provider, False):
                continue

            metrics = self.provider_metrics[provider]

            # 計算提供商分數
            success_rate = metrics["successful_requests"] / max(
                metrics["total_requests"], 1
            )
            avg_response_time = metrics["average_response_time"]

            # 分數計算：成功率 * 0.6 + 響應時間權重 * 0.4
            time_score = max(0, 1 - (avg_response_time / 10))  # 10秒為基準
            score = success_rate * 0.6 + time_score * 0.4

            if score > best_score:
                best_score = score
                best_provider = provider

        return best_provider

    def _get_available_providers(
        self, task_type: AITaskType
    ) -> List[AIProvider]:
        """獲取支援指定任務類型的提供商"""
        providers_map = {
            AITaskType.TEXT_GENERATION: [AIProvider.OPENAI, AIProvider.GEMINI],
            AITaskType.IMAGE_GENERATION: [AIProvider.STABILITY_AI],
            AITaskType.VOICE_SYNTHESIS: [AIProvider.ELEVENLABS],
            AITaskType.MUSIC_GENERATION: [AIProvider.SUNO],
            AITaskType.CONTENT_ANALYSIS: [
                AIProvider.GEMINI,
                AIProvider.OPENAI,
            ],
            AITaskType.TREND_ANALYSIS: [AIProvider.GEMINI, AIProvider.OPENAI],
        }

        return providers_map.get(task_type, [])

    async def _execute_request(
        self, request: AIRequest, provider: AIProvider
    ) -> AIResponse:
        """執行 AI 請求"""
        start_time = time.time()

        if request.task_type == AITaskType.TEXT_GENERATION:
            return await self._execute_text_generation(
                request, provider, start_time
            )
        elif request.task_type == AITaskType.MUSIC_GENERATION:
            return await self._execute_music_generation(
                request, provider, start_time
            )
        elif request.task_type == AITaskType.CONTENT_ANALYSIS:
            return await self._execute_content_analysis(
                request, provider, start_time
            )
        elif request.task_type == AITaskType.TREND_ANALYSIS:
            return await self._execute_trend_analysis(
                request, provider, start_time
            )
        else:
            raise ValueError(f"不支援的任務類型: {request.task_type}")

    async def _execute_text_generation(
        self, request: AIRequest, provider: AIProvider, start_time: float
    ) -> AIResponse:
        """執行文字生成"""
        if provider == AIProvider.GEMINI and GEMINI_AVAILABLE:
            # 使用 Gemini
            config = GeminiGenerationConfig(
                temperature=request.parameters.get("temperature", 0.7),
                max_output_tokens=request.parameters.get("max_tokens", 300),
            )

            api_key = self._get_api_key("gemini")
            async with GeminiClient(api_key=api_key) as client:
                result = await client.generate_content(
                    prompt=request.prompt,
                    model=request.model or "gemini-pro",
                    generation_config=config,
                )

                return AIResponse(
                    success=result.success,
                    content=result.text if result.success else None,
                    provider=provider,
                    model=request.model or "gemini-pro",
                    duration=time.time() - start_time,
                    error_message=(
                        result.error_message if not result.success else None
                    ),
                    metadata={"usage": result.usage_metadata},
                )

        elif provider == AIProvider.OPENAI:
            # 使用 OpenAI (需要從現有代碼整合)
            # 這裡可以整合現有的 OpenAI 客戶端
            pass

        raise ValueError(f"提供商 {provider.value} 不支援文字生成或不可用")

    async def _execute_music_generation(
        self, request: AIRequest, provider: AIProvider, start_time: float
    ) -> AIResponse:
        """執行音樂生成"""
        if provider == AIProvider.SUNO and SUNO_AVAILABLE:
            music_request = MusicGenerationRequest(
                prompt=request.prompt,
                duration=request.parameters.get("duration", 30),
                style=request.parameters.get("style"),
                instrumental=request.parameters.get("instrumental", True),
            )

            api_key = self._get_api_key("suno")
            async with SunoClient(api_key=api_key) as client:
                result = await client.generate_music(music_request)

                return AIResponse(
                    success=result.status == "completed",
                    content=(
                        {
                            "audio_url": result.audio_url,
                            "video_url": result.video_url,
                            "title": result.title,
                            "duration": result.duration,
                        }
                        if result.status == "completed"
                        else None
                    ),
                    provider=provider,
                    model="chirp-v3",
                    duration=time.time() - start_time,
                    error_message=(
                        result.error_message
                        if result.status != "completed"
                        else None
                    ),
                )

        raise ValueError(f"提供商 {provider.value} 不支援音樂生成或不可用")

    async def _execute_content_analysis(
        self, request: AIRequest, provider: AIProvider, start_time: float
    ) -> AIResponse:
        """執行內容分析"""
        if provider == AIProvider.GEMINI and GEMINI_AVAILABLE:
            # 使用 Gemini 進行內容分析
            analysis_prompt = f"""
請分析以下內容並提供結構化分析：

內容：{request.prompt}

請分析：
1. 主要主題
2. 情感基調
3. 目標受眾
4. 內容品質評分 (1-10)
5. 改進建議

請以 JSON 格式回覆。
"""

            api_key = self._get_api_key("gemini")
            async with GeminiClient(api_key=api_key) as client:
                result = await client.generate_content(
                    prompt=analysis_prompt,
                    generation_config=GeminiGenerationConfig(
                        temperature=0.3, max_output_tokens=512
                    ),
                )

                if result.success:
                    try:
                        import json
                        import re

                        json_match = re.search(
                            r"\{.*\}", result.text, re.DOTALL
                        )
                        analysis_data = (
                            json.loads(json_match.group())
                            if json_match
                            else {"raw_text": result.text}
                        )
                    except json.JSONDecodeError:
                        analysis_data = {"raw_text": result.text}
                else:
                    analysis_data = None

                return AIResponse(
                    success=result.success,
                    content=analysis_data,
                    provider=provider,
                    model="gemini-pro",
                    duration=time.time() - start_time,
                    error_message=(
                        result.error_message if not result.success else None
                    ),
                )

        raise ValueError(f"提供商 {provider.value} 不支援內容分析或不可用")

    async def _execute_trend_analysis(
        self, request: AIRequest, provider: AIProvider, start_time: float
    ) -> AIResponse:
        """執行趨勢分析"""
        if provider == AIProvider.GEMINI and GEMINI_AVAILABLE:
            from services.ai_service.gemini_client import analyze_trends

            api_key = self._get_api_key("gemini")
            result = await analyze_trends(request.prompt, api_key=api_key)

            return AIResponse(
                success="error" not in result,
                content=result,
                provider=provider,
                model="gemini-pro",
                duration=time.time() - start_time,
                error_message=(
                    result.get("error") if "error" in result else None
                ),
            )

        raise ValueError(f"提供商 {provider.value} 不支援趨勢分析或不可用")

    async def _try_fallback(
        self, request: AIRequest, failed_provider: AIProvider
    ) -> Optional[AIResponse]:
        """嘗試故障轉移"""
        logger.info(f"嘗試故障轉移，原提供商: {failed_provider.value}")

        # 獲取其他可用提供商
        available_providers = self._get_available_providers(request.task_type)
        fallback_providers = [
            p
            for p in available_providers
            if p != failed_provider and self.provider_health.get(p, False)
        ]

        if not fallback_providers:
            logger.warning("沒有可用的故障轉移提供商")
            return None

        # 隨機選擇一個故障轉移提供商
        fallback_provider = random.choice(fallback_providers)

        try:
            fallback_request = AIRequest(
                task_type=request.task_type,
                prompt=request.prompt,
                provider=fallback_provider,
                model=request.model,
                parameters=request.parameters,
                fallback_enabled=False,  # 避免遞迴故障轉移
            )

            response = await self._execute_request(
                fallback_request, fallback_provider
            )
            logger.info(f"故障轉移成功，使用提供商: {fallback_provider.value}")
            return response

        except Exception as e:
            logger.error(f"故障轉移失敗 ({fallback_provider.value}): {e}")
            return None

    async def _update_provider_metrics(
        self, provider: AIProvider, success: bool, duration: float
    ):
        """更新提供商指標"""
        metrics = self.provider_metrics[provider]

        metrics["total_requests"] += 1
        metrics["last_request_time"] = time.time()

        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["error_count"] += 1

        # 更新平均響應時間
        total_requests = metrics["total_requests"]
        metrics["average_response_time"] = (
            metrics["average_response_time"] * (total_requests - 1) + duration
        ) / total_requests

        # 檢查提供商健康狀態
        success_rate = metrics["successful_requests"] / total_requests
        if success_rate < 0.5 and total_requests >= 5:
            self.provider_health[provider] = False
            logger.warning(
                f"提供商 {provider.value} 標記為不健康 (成功率: {success_rate:.2f})"
            )
        elif success_rate >= 0.8:
            self.provider_health[provider] = True

    def _get_api_key(self, provider: str) -> str:
        """獲取 API 金鑰"""
        import os

        key_map = {
            "gemini": "GEMINI_API_KEY",
            "suno": "SUNO_API_KEY",
            "openai": "OPENAI_API_KEY",
            "stability": "STABILITY_API_KEY",
            "elevenlabs": "ELEVENLABS_API_KEY",
        }

        env_var = key_map.get(provider)
        if env_var:
            return os.getenv(env_var, "")

        return ""

    async def get_provider_status(self) -> Dict[str, Any]:
        """獲取所有提供商狀態"""
        status = {}

        for provider in AIProvider:
            metrics = self.provider_metrics[provider]
            status[provider.value] = {
                "healthy": self.provider_health[provider],
                "total_requests": metrics["total_requests"],
                "success_rate": metrics["successful_requests"]
                / max(metrics["total_requests"], 1),
                "average_response_time": metrics["average_response_time"],
                "error_count": metrics["error_count"],
            }

        return status

    async def reset_provider_health(self, provider: AIProvider):
        """重置提供商健康狀態"""
        self.provider_health[provider] = True
        logger.info(f"提供商 {provider.value} 健康狀態已重置")


# 便利函數
async def generate_text_with_fallback(
    prompt: str,
    primary_provider: str = "openai",
    fallback_provider: str = "gemini",
    config_manager=None,
    **kwargs,
) -> str:
    """生成文字的便利函數（支援故障轉移）"""

    orchestrator = AIOrchestrator(config_manager)

    request = AIRequest(
        task_type=AITaskType.TEXT_GENERATION,
        prompt=prompt,
        provider=AIProvider(primary_provider),
        parameters=kwargs,
    )

    response = await orchestrator.process_request(request)

    if response.success:
        return response.content
    else:
        logger.error(f"文字生成失敗: {response.error_message}")
        return ""


async def generate_music_for_video(
    prompt: str, duration: int = 30, style: str = None, config_manager=None
) -> Optional[Dict[str, Any]]:
    """為影片生成音樂的便利函數"""

    orchestrator = AIOrchestrator(config_manager)

    request = AIRequest(
        task_type=AITaskType.MUSIC_GENERATION,
        prompt=prompt,
        provider=AIProvider.SUNO,
        parameters={
            "duration": duration,
            "style": style,
            "instrumental": True,
        },
    )

    response = await orchestrator.process_request(request)

    if response.success:
        return response.content
    else:
        logger.error(f"音樂生成失敗: {response.error_message}")
        return None


async def main():
    """測試函數"""
    orchestrator = AIOrchestrator()

    # 測試文字生成
    text_request = AIRequest(
        task_type=AITaskType.TEXT_GENERATION,
        prompt="寫一個關於 AI 技術的短影片腳本",
        parameters={"temperature": 0.8, "max_tokens": 200},
    )

    response = await orchestrator.process_request(text_request)
    print(f"文字生成結果: {response}")

    # 獲取提供商狀態
    status = await orchestrator.get_provider_status()
    print(f"提供商狀態: {status}")


if __name__ == "__main__":
    asyncio.run(main())
