#!/usr/bin/env python3
"""
Google Gemini Pro AI 客戶端
提供文字生成、內容分析和多模態 AI 功能
"""

import asyncio
import base64
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class GeminiMessage:
    """Gemini 對話訊息"""

    role: str  # "user" 或 "model"
    parts: List[Dict[str, Any]]


@dataclass
class GeminiGenerationConfig:
    """Gemini 生成配置"""

    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 40
    max_output_tokens: int = 2048
    candidate_count: int = 1


@dataclass
class GeminiResponse:
    """Gemini 回應結果"""

    text: str
    finish_reason: str
    safety_ratings: List[Dict[str, Any]]
    usage_metadata: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None


class GeminiClient:
    """Google Gemini Pro API 客戶端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.session = None
        self._cost_tracker = None

        # 支援的模型
        self.models = {
            "gemini-pro": "gemini-1.5-pro-latest",
            "gemini-pro-vision": "gemini-1.5-pro-vision-latest",
            "gemini-flash": "gemini-1.5-flash-latest",
        }

        # 初始化成本追蹤
        try:
            from monitoring.cost_tracker import get_cost_tracker

            self._cost_tracker = get_cost_tracker()
        except ImportError:
            logger.warning("成本追蹤器不可用")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def generate_content(
        self,
        prompt: str,
        model: str = "gemini-pro",
        generation_config: GeminiGenerationConfig = None,
        system_instruction: str = None,
        images: List[bytes] = None,
    ) -> GeminiResponse:
        """生成內容"""
        if not self.session:
            raise RuntimeError("客戶端未初始化，請使用 async with")

        if generation_config is None:
            generation_config = GeminiGenerationConfig()

        # 選擇模型
        model_name = self.models.get(model, model)
        if images and "vision" not in model_name:
            model_name = self.models["gemini-pro-vision"]

        logger.info(
            f"使用 Gemini 生成內容: {prompt[:50]}... (模型: {model_name})"
        )

        # 準備請求數據
        contents = []

        # 系統指令
        if system_instruction:
            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": f"System: {system_instruction}"}],
                }
            )

        # 用戶內容
        user_parts = [{"text": prompt}]

        # 添加圖片
        if images:
            for image_data in images:
                image_b64 = base64.b64encode(image_data).decode()
                user_parts.append(
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64,
                        }
                    }
                )

        contents.append({"role": "user", "parts": user_parts})

        request_data = {
            "contents": contents,
            "generationConfig": asdict(generation_config),
        }

        start_time = time.time()

        try:
            url = f"{self.base_url}/models/{model_name}:generateContent"
            params = {"key": self.api_key}

            async with self.session.post(
                url,
                params=params,
                json=request_data,
                headers={"Content-Type": "application/json"},
            ) as response:

                duration = time.time() - start_time

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Gemini API 錯誤 {response.status}: {error_text}"
                    )

                    # 記錄失敗的 API 呼叫
                    if self._cost_tracker:
                        await self._cost_tracker.track_api_call(
                            provider="google",
                            model=model_name,
                            operation_type="text_generation",
                            success=False,
                            metadata={
                                "error": error_text,
                                "status": response.status,
                            },
                        )

                    return GeminiResponse(
                        text="",
                        finish_reason="error",
                        safety_ratings=[],
                        usage_metadata={},
                        success=False,
                        error_message=f"API 錯誤: {response.status} - {error_text}",
                    )

                result_data = await response.json()

                # 解析回應
                candidates = result_data.get("candidates", [])
                if not candidates:
                    logger.error("Gemini 沒有返回有效候選")
                    return GeminiResponse(
                        text="",
                        finish_reason="no_candidates",
                        safety_ratings=[],
                        usage_metadata={},
                        success=False,
                        error_message="沒有返回有效候選",
                    )

                candidate = candidates[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])

                if not parts:
                    logger.error("Gemini 沒有返回內容")
                    return GeminiResponse(
                        text="",
                        finish_reason="no_content",
                        safety_ratings=[],
                        usage_metadata={},
                        success=False,
                        error_message="沒有返回內容",
                    )

                text = parts[0].get("text", "")
                finish_reason = candidate.get("finishReason", "STOP")
                safety_ratings = candidate.get("safetyRatings", [])
                usage_metadata = result_data.get("usageMetadata", {})

                # 記錄成功的 API 呼叫
                if self._cost_tracker:
                    input_tokens = usage_metadata.get("promptTokenCount", 0)
                    output_tokens = usage_metadata.get(
                        "candidatesTokenCount", 0
                    )
                    total_tokens = usage_metadata.get(
                        "totalTokenCount", input_tokens + output_tokens
                    )

                    await self._cost_tracker.track_api_call(
                        provider="google",
                        model=model_name,
                        operation_type="text_generation",
                        tokens_used=total_tokens,
                        success=True,
                        metadata={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "duration": duration,
                            "finish_reason": finish_reason,
                        },
                    )

                return GeminiResponse(
                    text=text,
                    finish_reason=finish_reason,
                    safety_ratings=safety_ratings,
                    usage_metadata=usage_metadata,
                    success=True,
                )

        except asyncio.TimeoutError:
            logger.error("Gemini 請求超時")
            return GeminiResponse(
                text="",
                finish_reason="timeout",
                safety_ratings=[],
                usage_metadata={},
                success=False,
                error_message="請求超時",
            )
        except Exception as e:
            logger.error(f"Gemini 請求失敗: {e}")
            return GeminiResponse(
                text="",
                finish_reason="error",
                safety_ratings=[],
                usage_metadata={},
                success=False,
                error_message=str(e),
            )

    async def chat(
        self,
        messages: List[GeminiMessage],
        model: str = "gemini-pro",
        generation_config: GeminiGenerationConfig = None,
    ) -> GeminiResponse:
        """多輪對話"""
        if not self.session:
            raise RuntimeError("客戶端未初始化，請使用 async with")

        if generation_config is None:
            generation_config = GeminiGenerationConfig()

        model_name = self.models.get(model, model)

        logger.info(f"Gemini 對話 (模型: {model_name})")

        # 轉換訊息格式
        contents = []
        for msg in messages:
            contents.append({"role": msg.role, "parts": msg.parts})

        request_data = {
            "contents": contents,
            "generationConfig": asdict(generation_config),
        }

        start_time = time.time()

        try:
            url = f"{self.base_url}/models/{model_name}:generateContent"
            params = {"key": self.api_key}

            async with self.session.post(
                url,
                params=params,
                json=request_data,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status == 200:
                    result_data = await response.json()
                    duration = time.time() - start_time

                    # 解析回應（類似 generate_content）
                    candidates = result_data.get("candidates", [])
                    if candidates:
                        candidate = candidates[0]
                        content = candidate.get("content", {})
                        parts = content.get("parts", [])

                        if parts:
                            text = parts[0].get("text", "")
                            usage_metadata = result_data.get(
                                "usageMetadata", {}
                            )

                            # 記錄成功的 API 呼叫
                            if self._cost_tracker:
                                total_tokens = usage_metadata.get(
                                    "totalTokenCount", 0
                                )
                                await self._cost_tracker.track_api_call(
                                    provider="google",
                                    model=model_name,
                                    operation_type="chat",
                                    tokens_used=total_tokens,
                                    success=True,
                                    metadata={"duration": duration},
                                )

                            return GeminiResponse(
                                text=text,
                                finish_reason=candidate.get(
                                    "finishReason", "STOP"
                                ),
                                safety_ratings=candidate.get(
                                    "safetyRatings", []
                                ),
                                usage_metadata=usage_metadata,
                                success=True,
                            )

                # 錯誤處理
                error_text = await response.text()
                return GeminiResponse(
                    text="",
                    finish_reason="error",
                    safety_ratings=[],
                    usage_metadata={},
                    success=False,
                    error_message=f"API 錯誤: {response.status} - {error_text}",
                )

        except Exception as e:
            logger.error(f"Gemini 對話失敗: {e}")
            return GeminiResponse(
                text="",
                finish_reason="error",
                safety_ratings=[],
                usage_metadata={},
                success=False,
                error_message=str(e),
            )

    async def analyze_image(
        self, image_data: bytes, prompt: str = "分析這張圖片"
    ) -> GeminiResponse:
        """分析圖片"""
        return await self.generate_content(
            prompt=prompt, model="gemini-pro-vision", images=[image_data]
        )

    async def generate_script(
        self, topic: str, platform: str = "tiktok", style: str = "engaging"
    ) -> GeminiResponse:
        """生成影片腳本"""
        system_instruction = f"""
你是一個專業的{platform}短影片腳本創作者。
請為給定主題創作一個{style}風格的短影片腳本。

腳本要求：
1. 符合{platform}平台特色
2. 長度適中（15-60秒）
3. 開頭吸引人
4. 結尾有號召行動
5. 語言生動有趣
"""

        prompt = f"為以下主題創作短影片腳本：{topic}"

        return await self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            generation_config=GeminiGenerationConfig(
                temperature=0.8, max_output_tokens=1024
            ),
        )

    async def optimize_content(
        self, content: str, platform: str, target_audience: str = "年輕人"
    ) -> GeminiResponse:
        """優化內容"""
        system_instruction = f"""
你是一個專業的內容優化師，專門針對{platform}平台優化內容。
目標受眾是{target_audience}。

請優化以下內容，讓它更適合目標平台和受眾：
1. 調整語調和風格
2. 優化結構和流程
3. 增加吸引力
4. 符合平台特色
"""

        prompt = f"請優化以下內容：\n\n{content}"

        return await self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            generation_config=GeminiGenerationConfig(
                temperature=0.6, max_output_tokens=1024
            ),
        )


# 便利函數
async def generate_video_script(
    topic: str,
    platform: str = "tiktok",
    style: str = "engaging",
    api_key: str = None,
) -> str:
    """生成影片腳本的便利函數"""

    async with GeminiClient(api_key=api_key) as client:
        result = await client.generate_script(topic, platform, style)

        if result.success:
            return result.text
        else:
            logger.error(f"腳本生成失敗: {result.error_message}")
            return ""


async def analyze_trends(content: str, api_key: str = None) -> Dict[str, Any]:
    """分析內容趨勢的便利函數"""

    prompt = f"""
分析以下內容的趨勢潛力，並以 JSON 格式返回分析結果：

內容：{content}

請分析：
1. 病毒潛力 (1-10分)
2. 目標受眾
3. 最佳發布時間
4. 推薦平台
5. 改進建議

返回格式：
{{
    "viral_potential": 數字,
    "target_audience": "描述",
    "best_timing": "時間建議", 
    "recommended_platforms": ["平台1", "平台2"],
    "improvements": ["建議1", "建議2"]
}}
"""

    async with GeminiClient(api_key=api_key) as client:
        result = await client.generate_content(
            prompt=prompt,
            generation_config=GeminiGenerationConfig(
                temperature=0.3, max_output_tokens=512
            ),
        )

        if result.success:
            try:
                # 嘗試解析 JSON
                import re

                json_match = re.search(r"\{.*\}", result.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"error": "無法解析 JSON 格式"}
            except json.JSONDecodeError:
                return {"error": "JSON 解析失敗", "raw_text": result.text}
        else:
            return {"error": result.error_message}


async def main():
    """測試函數"""
    import os

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("請設置 GEMINI_API_KEY 環境變數")
        return

    # 測試腳本生成
    script = await generate_video_script(
        topic="AI 如何改變我們的生活",
        platform="tiktok",
        style="educative",
        api_key=api_key,
    )
    print(f"生成的腳本：\n{script}")

    # 測試趨勢分析
    analysis = await analyze_trends(script, api_key=api_key)
    print(f"趨勢分析：\n{json.dumps(analysis, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
