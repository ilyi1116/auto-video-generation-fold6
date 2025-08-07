#!/usr/bin/env python3
"""
AI服務客戶端
提供統一的AI服務調用介面，供API Gateway使用
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AIServiceResponse:
    """AI服務回應"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    service_name: str = ""
    timestamp: str = ""


class AIServiceClient:
    """AI服務統一客戶端"""
    
    def __init__(
        self, 
        ai_service_url: str = "http://localhost:8005",
        timeout: int = 300  # 5分鐘超時
    ):
        self.ai_service_url = ai_service_url.rstrip("/")
        self.timeout = timeout
        
    async def generate_script(
        self,
        topic: str,
        platform: str = "youtube",
        style: str = "educational",
        duration: int = 60,
        language: str = "zh-TW",
        target_audience: str = "general"
    ) -> AIServiceResponse:
        """生成影片腳本"""
        
        request_data = {
            "topic": topic,
            "platform": platform,
            "style": style,
            "duration": duration,
            "language": language,
            "target_audience": target_audience
        }
        
        return await self._make_request(
            "POST", 
            "/api/v1/generate/script", 
            request_data,
            service_name="script_generation"
        )
    
    async def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        resolution: str = "1024x1024",
        quantity: int = 1
    ) -> AIServiceResponse:
        """生成圖像"""
        
        request_data = {
            "prompt": prompt,
            "style": style,
            "resolution": resolution,
            "quantity": quantity
        }
        
        return await self._make_request(
            "POST", 
            "/api/v1/generate/image", 
            request_data,
            service_name="image_generation"
        )
    
    async def generate_music(
        self,
        prompt: str,
        style: str = "background",
        duration: int = 30,
        instrumental: bool = True,
        mood: str = "upbeat"
    ) -> AIServiceResponse:
        """生成音樂"""
        
        request_data = {
            "prompt": prompt,
            "style": style,
            "duration": duration,
            "instrumental": instrumental,
            "mood": mood
        }
        
        return await self._make_request(
            "POST", 
            "/api/v1/generate/music", 
            request_data,
            service_name="music_generation"
        )
    
    async def generate_voice(
        self,
        text: str,
        voice_id: str = "female-1",
        speed: float = 1.0,
        emotion: str = "neutral",
        language: str = "zh-TW"
    ) -> AIServiceResponse:
        """生成語音"""
        
        request_data = {
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "emotion": emotion,
            "language": language
        }
        
        return await self._make_request(
            "POST", 
            "/api/v1/generate/voice", 
            request_data,
            service_name="voice_generation"
        )
    
    async def generate_batch(
        self,
        script_params: Optional[Dict[str, Any]] = None,
        image_params: Optional[Dict[str, Any]] = None,
        music_params: Optional[Dict[str, Any]] = None,
        voice_params: Optional[Dict[str, Any]] = None
    ) -> AIServiceResponse:
        """批量生成內容"""
        
        request_data = {}
        
        if script_params:
            request_data["script_request"] = script_params
        if image_params:
            request_data["image_request"] = image_params
        if music_params:
            request_data["music_request"] = music_params
        if voice_params:
            request_data["voice_request"] = voice_params
        
        return await self._make_request(
            "POST", 
            "/api/v1/generate/batch", 
            request_data,
            service_name="batch_generation"
        )
    
    async def check_health(self) -> AIServiceResponse:
        """檢查AI服務健康狀態"""
        
        return await self._make_request(
            "GET", 
            "/health", 
            None,
            service_name="health_check"
        )
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]],
        service_name: str
    ) -> AIServiceResponse:
        """發送請求到AI服務"""
        
        url = f"{self.ai_service_url}{endpoint}"
        timestamp = datetime.utcnow().isoformat()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling AI service: {method} {url}")
                
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                else:
                    return AIServiceResponse(
                        success=False,
                        error_message=f"Unsupported HTTP method: {method}",
                        service_name=service_name,
                        timestamp=timestamp
                    )
                
                response.raise_for_status()
                result_data = response.json()
                
                logger.info(f"AI service response: {response.status_code}")
                
                return AIServiceResponse(
                    success=True,
                    data=result_data.get("data"),
                    service_name=service_name,
                    timestamp=timestamp
                )
                
        except httpx.TimeoutException:
            logger.error(f"AI service timeout: {url}")
            return AIServiceResponse(
                success=False,
                error_message=f"AI service timeout after {self.timeout}s",
                service_name=service_name,
                timestamp=timestamp
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AI service HTTP error: {e.response.status_code} - {e.response.text}")
            return AIServiceResponse(
                success=False,
                error_message=f"AI service error: {e.response.status_code}",
                service_name=service_name,
                timestamp=timestamp
            )
            
        except httpx.RequestError as e:
            logger.error(f"AI service connection error: {e}")
            return AIServiceResponse(
                success=False,
                error_message=f"AI service connection error: {str(e)}",
                service_name=service_name,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Unexpected AI service error: {e}")
            return AIServiceResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                service_name=service_name,
                timestamp=timestamp
            )


# 單例AI服務客戶端
_ai_client: Optional[AIServiceClient] = None


def get_ai_client(ai_service_url: str = "http://localhost:8005") -> AIServiceClient:
    """獲取AI服務客戶端單例"""
    global _ai_client
    
    if _ai_client is None:
        _ai_client = AIServiceClient(ai_service_url)
    
    return _ai_client


# 便利函數
async def generate_video_script(topic: str, **kwargs) -> Dict[str, Any]:
    """生成影片腳本的便利函數"""
    client = get_ai_client()
    response = await client.generate_script(topic, **kwargs)
    
    if response.success:
        return response.data
    else:
        raise Exception(response.error_message)


async def generate_video_images(prompt: str, **kwargs) -> Dict[str, Any]:
    """生成影片圖像的便利函數"""
    client = get_ai_client()
    response = await client.generate_image(prompt, **kwargs)
    
    if response.success:
        return response.data
    else:
        raise Exception(response.error_message)


async def generate_background_music(prompt: str, **kwargs) -> Dict[str, Any]:
    """生成背景音樂的便利函數"""
    client = get_ai_client()
    response = await client.generate_music(prompt, **kwargs)
    
    if response.success:
        return response.data
    else:
        raise Exception(response.error_message)


async def generate_video_voice(text: str, **kwargs) -> Dict[str, Any]:
    """生成影片語音的便利函數"""
    client = get_ai_client()
    response = await client.generate_voice(text, **kwargs)
    
    if response.success:
        return response.data
    else:
        raise Exception(response.error_message)


# 完整的影片內容生成流程
async def generate_complete_video_content(
    topic: str,
    platform: str = "youtube",
    style: str = "educational",
    duration: int = 60
) -> Dict[str, Any]:
    """生成完整的影片內容（腳本+圖像+音樂+語音）"""
    
    client = get_ai_client()
    
    logger.info(f"Starting complete video content generation for topic: {topic}")
    
    try:
        # 第一步：生成腳本
        script_response = await client.generate_script(
            topic=topic,
            platform=platform,
            style=style,
            duration=duration
        )
        
        if not script_response.success:
            raise Exception(f"Script generation failed: {script_response.error_message}")
        
        script_data = script_response.data
        script_text = script_data.get("script", "")
        
        # 第二步：並行生成其他內容
        tasks = []
        
        # 圖像生成
        image_prompt = f"Visual content for {topic}, {style} style"
        tasks.append(client.generate_image(
            prompt=image_prompt,
            quantity=3,  # 生成3張圖片
            resolution="1920x1080" if platform == "youtube" else "1080x1080"
        ))
        
        # 音樂生成
        music_prompt = f"Background music for {topic} video, {style} style"
        tasks.append(client.generate_music(
            prompt=music_prompt,
            duration=duration,
            instrumental=True,
            mood="upbeat" if style == "entertaining" else "calm"
        ))
        
        # 語音生成
        tasks.append(client.generate_voice(
            text=script_text,
            voice_id="female-1",
            speed=1.0,
            emotion="neutral"
        ))
        
        # 等待所有任務完成
        image_response, music_response, voice_response = await asyncio.gather(*tasks)
        
        # 整合結果
        result = {
            "topic": topic,
            "platform": platform,
            "style": style,
            "duration": duration,
            "script": script_data,
            "images": image_response.data if image_response.success else None,
            "music": music_response.data if music_response.success else None,
            "voice": voice_response.data if voice_response.success else None,
            "errors": []
        }
        
        # 收集錯誤
        if not image_response.success:
            result["errors"].append(f"Image generation: {image_response.error_message}")
        if not music_response.success:
            result["errors"].append(f"Music generation: {music_response.error_message}")
        if not voice_response.success:
            result["errors"].append(f"Voice generation: {voice_response.error_message}")
        
        logger.info(f"Complete video content generation finished. Errors: {len(result['errors'])}")
        
        return result
        
    except Exception as e:
        logger.error(f"Complete video content generation failed: {e}")
        raise


if __name__ == "__main__":
    # 測試腳本
    async def test_ai_services():
        print("Testing AI Services...")
        
        # 測試健康檢查
        client = get_ai_client()
        health_response = await client.check_health()
        print(f"Health Check: {health_response.success}")
        
        if health_response.success:
            # 測試腳本生成
            script_response = await client.generate_script(
                topic="人工智能的未來發展",
                platform="youtube",
                style="educational"
            )
            print(f"Script Generation: {script_response.success}")
            
            if script_response.success:
                print(f"Generated script: {script_response.data['script'][:100]}...")
    
    asyncio.run(test_ai_services())