#!/usr/bin/env python3
"""
Suno.ai 音樂生成客戶端
提供 AI 驅動的音樂生成功能
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MusicGenerationRequest:
    """音樂生成請求"""

    prompt: str
    style: Optional[str] = None
    duration: int = 30  # 秒
    instrumental: bool = False
    seed: Optional[int] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None


@dataclass
class MusicGenerationResult:
    """音樂生成結果"""

    id: str
    status: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    duration: Optional[float] = None
    created_at: Optional[str] = None
    error_message: Optional[str] = None


class SunoClient:
    """Suno.ai API 客戶端"""

    def __init__(
        self, api_key: str = None, base_url: str = "https://api.sunoai.com"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = None
        self._cost_tracker = None

        # 初始化成本追蹤
        try:
            from monitoring.cost_tracker import get_cost_tracker

            self._cost_tracker = get_cost_tracker()
        except ImportError:
            logger.warning("成本追蹤器不可用")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=300),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def generate_music(
        self, request: MusicGenerationRequest
    ) -> MusicGenerationResult:
        """生成音樂"""
        if not self.session:
            raise RuntimeError("客戶端未初始化，請使用 async with")

        logger.info(f"生成音樂: {request.prompt[:50]}...")

        # 準備請求數據
        data = {
            "prompt": request.prompt,
            "make_instrumental": request.instrumental,
            "wait_audio": True,
        }

        if request.style:
            data["tags"] = request.style
        if request.duration:
            data["mv"] = (
                "chirp-v3-5" if request.duration <= 60 else "chirp-v3-0"
            )
        if request.title:
            data["title"] = request.title

        start_time = time.time()

        try:
            # 發送生成請求
            async with self.session.post(
                f"{self.base_url}/api/generate", json=data
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Suno API 錯誤 {response.status}: {error_text}"
                    )

                    # 記錄失敗的 API 呼叫
                    if self._cost_tracker:
                        await self._cost_tracker.track_api_call(
                            provider="suno",
                            model="chirp-v3",
                            operation_type="music_generation",
                            success=False,
                            metadata={
                                "error": error_text,
                                "status": response.status,
                            },
                        )

                    return MusicGenerationResult(
                        id="",
                        status="failed",
                        error_message=f"API 錯誤: {response.status} - \
                            {error_text}",
                    )

                result_data = await response.json()
                generation_id = result_data[0]["id"] if result_data else None

                if not generation_id:
                    logger.error("未收到有效的生成 ID")
                    return MusicGenerationResult(
                        id="",
                        status="failed",
                        error_message="未收到有效的生成 ID",
                    )

                # 輪詢生成狀態
                return await self._poll_generation_status(
                    generation_id, start_time
                )

        except asyncio.TimeoutError:
            logger.error("音樂生成請求超時")
            return MusicGenerationResult(
                id="", status="timeout", error_message="請求超時"
            )
        except Exception as e:
            logger.error(f"音樂生成失敗: {e}")
            return MusicGenerationResult(
                id="", status="error", error_message=str(e)
            )

    async def _poll_generation_status(
        self, generation_id: str, start_time: float
    ) -> MusicGenerationResult:
        """輪詢生成狀態"""
        max_attempts = 60  # 最多等待 5 分鐘
        attempt = 0

        while attempt < max_attempts:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/get?ids={generation_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            item = data[0]
                            status = item.get("status", "")

                            if status == "complete":
                                duration = time.time() - start_time

                                # 記錄成功的 API 呼叫
                                if self._cost_tracker:
                                    self._calculate_cost(item)
                                    await self._cost_tracker.track_api_call(
                                        provider="suno",
                                        model="chirp-v3",
                                        operation_type="music_generation",
                                        success=True,
                                        metadata={
                                            "duration": duration,
                                            "audio_duration": item.get(
                                                "duration", 0
                                            ),
                                            "title": item.get("title", ""),
                                        },
                                    )

                                return MusicGenerationResult(
                                    id=generation_id,
                                    status="completed",
                                    audio_url=item.get("audio_url"),
                                    video_url=item.get("video_url"),
                                    title=item.get("title"),
                                    tags=(
                                        item.get("tags", "").split(",")
                                        if item.get("tags")
                                        else None
                                    ),
                                    duration=item.get("duration"),
                                    created_at=item.get("created_at"),
                                )

                            elif status == "error":
                                error_msg = item.get(
                                    "error_message", "生成失敗"
                                )
                                logger.error(f"音樂生成失敗: {error_msg}")

                                # 記錄失敗的 API 呼叫
                                if self._cost_tracker:
                                    await self._cost_tracker.track_api_call(
                                        provider="suno",
                                        model="chirp-v3",
                                        operation_type="music_generation",
                                        success=False,
                                        metadata={"error": error_msg},
                                    )

                                return MusicGenerationResult(
                                    id=generation_id,
                                    status="failed",
                                    error_message=error_msg,
                                )

                            # 仍在處理中
                            logger.info(
                                f"音樂生成進行中... (嘗試 {attempt + 1}/{max_attempts})"
                            )

                await asyncio.sleep(5)  # 等待 5 秒後重試
                attempt += 1

            except Exception as e:
                logger.error(f"檢查生成狀態失敗: {e}")
                await asyncio.sleep(5)
                attempt += 1

        # 超時
        logger.error("音樂生成輪詢超時")
        return MusicGenerationResult(
            id=generation_id, status="timeout", error_message="生成輪詢超時"
        )

    def _calculate_cost(self, result_data: Dict[str, Any]) -> float:
        """計算音樂生成成本"""
        # Suno.ai 的計費通常基於生成的音樂長度
        # 這裡使用估算價格，實際價格請參考官方文檔
        duration = result_data.get("duration", 30)  # 默認 30 秒
        cost_per_minute = 0.5  # 每分鐘 $0.5 (估算)
        return (duration / 60) * cost_per_minute

    async def get_generation_history(
        self, limit: int = 50
    ) -> List[MusicGenerationResult]:
        """獲取生成歷史"""
        if not self.session:
            raise RuntimeError("客戶端未初始化，請使用 async with")

        try:
            async with self.session.get(
                f"{self.base_url}/api/get_all"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []

                    for item in data[:limit]:
                        results.append(
                            MusicGenerationResult(
                                id=item.get("id", ""),
                                status=item.get("status", ""),
                                audio_url=item.get("audio_url"),
                                video_url=item.get("video_url"),
                                title=item.get("title"),
                                tags=(
                                    item.get("tags", "").split(",")
                                    if item.get("tags")
                                    else None
                                ),
                                duration=item.get("duration"),
                                created_at=item.get("created_at"),
                            )
                        )

                    return results
                else:
                    logger.error(f"獲取歷史失敗: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"獲取生成歷史失敗: {e}")
            return []

    async def download_audio(self, audio_url: str, output_path: Path) -> bool:
        """下載音頻文件"""
        if not self.session:
            raise RuntimeError("客戶端未初始化，請使用 async with")

        try:
            async with self.session.get(audio_url) as response:
                if response.status == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(output_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

                    logger.info(f"音頻文件已下載: {output_path}")
                    return True
                else:
                    logger.error(f"下載失敗: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"下載音頻失敗: {e}")
            return False


# 便利函數
async def generate_music_for_video(
    prompt: str,
    duration: int = 30,
    style: str = None,
    instrumental: bool = True,
    api_key: str = None,
) -> MusicGenerationResult:
    """為影片生成背景音樂的便利函數"""

    request = MusicGenerationRequest(
        prompt=prompt,
        duration=duration,
        style=style,
        instrumental=instrumental,
        title=f"Background Music - {prompt[:30]}",
    )

    async with SunoClient(api_key=api_key) as client:
        return await client.generate_music(request)


async def main():
    """測試函數"""
    # 測試音樂生成
    import os

    api_key = os.getenv("SUNO_API_KEY")
    if not api_key:
        print("請設置 SUNO_API_KEY 環境變數")
        return

    result = await generate_music_for_video(
        prompt="輕快的背景音樂，適合科技產品介紹影片",
        duration=30,
        style="upbeat, electronic, corporate",
        instrumental=True,
        api_key=api_key,
    )

    print(f"生成結果: {result}")

    if result.status == "completed" and result.audio_url:
        # 下載音頻
        async with SunoClient(api_key=api_key) as client:
            success = await client.download_audio(
                result.audio_url, Path("test_music.mp3")
            )
            print(f"下載成功: {success}")


if __name__ == "__main__":
    asyncio.run(main())
