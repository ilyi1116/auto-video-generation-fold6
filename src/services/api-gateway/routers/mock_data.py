#!/usr/bin/env python3
"""
假資料管理API路由
Mock Data Management API Routes
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.fixtures import mock_data_manager

router = APIRouter(prefix="/api/v1/mock-data", tags=["Mock Data"])

class MockDataResponse(BaseModel):
    success: bool
    data: Any
    message: Optional[str] = None

class ScriptGenerationRequest(BaseModel):
    topic: str
    style: str = "educational"
    host_name: str = "主持人"
    channel_name: str = "頻道"

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str = "realistic"
    count: int = 1

class VoiceSynthesisRequest(BaseModel):
    text: str
    voice_id: str = "tw_male_professional"
    speed: float = 1.0

@router.get("/users", response_model=MockDataResponse)
async def get_mock_users(count: Optional[int] = Query(None, ge=1, le=10)):
    """獲取測試用戶資料"""
    try:
        users = mock_data_manager.get_test_users(count)
        return MockDataResponse(
            success=True,
            data=users,
            message=f"獲取 {len(users)} 個測試用戶"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=MockDataResponse)
async def get_mock_user(user_id: int):
    """獲取單個測試用戶"""
    try:
        users = mock_data_manager.get_test_users()
        if user_id >= len(users):
            raise HTTPException(status_code=404, detail="用戶不存在")
        
        user = users[user_id]
        return MockDataResponse(
            success=True,
            data=user,
            message=f"獲取用戶 {user['username']}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-templates", response_model=MockDataResponse)
async def get_video_templates(category: Optional[str] = None):
    """獲取影片模板"""
    try:
        templates = mock_data_manager.get_video_templates(category)
        return MockDataResponse(
            success=True,
            data=templates,
            message=f"獲取 {len(templates)} 個影片模板"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sample-videos", response_model=MockDataResponse)
async def get_sample_videos(status: Optional[str] = None):
    """獲取範例影片"""
    try:
        videos = mock_data_manager.get_sample_videos(status)
        return MockDataResponse(
            success=True,
            data=videos,
            message=f"獲取 {len(videos)} 個範例影片"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-options", response_model=MockDataResponse)
async def get_voice_options(gender: Optional[str] = Query(None, regex="^(male|female)$")):
    """獲取語音選項"""
    try:
        voices = mock_data_manager.get_voice_options(gender)
        return MockDataResponse(
            success=True,
            data=voices,
            message=f"獲取 {len(voices)} 個語音選項"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image-prompts/{category}", response_model=MockDataResponse)
async def get_image_prompts(category: str):
    """獲取圖像生成提示詞"""
    try:
        prompts = mock_data_manager.get_image_prompts(category)
        if not prompts:
            available_categories = ["tech", "lifestyle", "business", "education"]
            raise HTTPException(
                status_code=404, 
                detail=f"分類 '{category}' 不存在。可用分類: {available_categories}"
            )
        
        return MockDataResponse(
            success=True,
            data=prompts,
            message=f"獲取 {category} 分類的 {len(prompts)} 個提示詞"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/script", response_model=MockDataResponse)
async def generate_mock_script(request: ScriptGenerationRequest):
    """生成模擬腳本"""
    try:
        # 生成腳本內容
        script_content = mock_data_manager.generate_mock_script(
            topic=request.topic,
            style=request.style,
            host_name=request.host_name,
            channel_name=request.channel_name
        )
        
        # 生成完整回應
        response_data = mock_data_manager.generate_mock_response(
            'script_generation',
            topic=request.topic,
            style=request.style
        )
        
        # 使用實際生成的腳本
        response_data['data']['script'] = script_content
        
        return MockDataResponse(
            success=True,
            data=response_data['data'],
            message="腳本生成成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/image", response_model=MockDataResponse)
async def generate_mock_image(request: ImageGenerationRequest):
    """生成模擬圖像"""
    try:
        response_data = mock_data_manager.generate_mock_response(
            'image_generation',
            prompt=request.prompt,
            style=request.style,
            count=request.count
        )
        
        return MockDataResponse(
            success=True,
            data=response_data['data'],
            message=f"生成 {request.count} 張圖像"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/voice", response_model=MockDataResponse)
async def generate_mock_voice(request: VoiceSynthesisRequest):
    """生成模擬語音"""
    try:
        response_data = mock_data_manager.generate_mock_response(
            'voice_synthesis',
            text=request.text,
            voice_id=request.voice_id
        )
        
        return MockDataResponse(
            success=True,
            data=response_data['data'],
            message="語音合成成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=MockDataResponse)
async def get_content_categories():
    """獲取內容分類"""
    try:
        videos_data = mock_data_manager.load_fixture('videos')
        categories = videos_data.get('content_categories', [])
        
        return MockDataResponse(
            success=True,
            data=categories,
            message=f"獲取 {len(categories)} 個內容分類"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/script-templates/{style}", response_model=MockDataResponse)
async def get_script_templates(style: str):
    """獲取腳本模板"""
    try:
        template = mock_data_manager.get_script_template(style)
        if not template:
            available_styles = ["educational", "entertaining", "tutorial"]
            raise HTTPException(
                status_code=404,
                detail=f"風格 '{style}' 不存在。可用風格: {available_styles}"
            )
        
        return MockDataResponse(
            success=True,
            data=template,
            message=f"獲取 {style} 風格的腳本模板"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fixtures/{fixture_name}", response_model=MockDataResponse)
async def update_fixture_data(fixture_name: str, data: Dict[str, Any]):
    """更新假資料檔案"""
    try:
        # 驗證檔案名稱
        allowed_fixtures = ["users", "videos", "ai_responses"]
        if fixture_name not in allowed_fixtures:
            raise HTTPException(
                status_code=400,
                detail=f"不允許的假資料類型。允許的類型: {allowed_fixtures}"
            )
        
        # 儲存資料
        mock_data_manager.save_custom_data(fixture_name, data)
        
        return MockDataResponse(
            success=True,
            data={"fixture_name": fixture_name, "updated": True},
            message=f"成功更新 {fixture_name} 假資料"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache", response_model=MockDataResponse)
async def clear_mock_data_cache():
    """清除假資料快取"""
    try:
        mock_data_manager.clear_cache()
        return MockDataResponse(
            success=True,
            data={"cache_cleared": True},
            message="假資料快取已清除"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=MockDataResponse)
async def get_mock_data_stats():
    """獲取假資料統計"""
    try:
        users = mock_data_manager.get_test_users()
        templates = mock_data_manager.get_video_templates()
        samples = mock_data_manager.get_sample_videos()
        voices = mock_data_manager.get_voice_options()
        
        stats = {
            "test_users_count": len(users),
            "video_templates_count": len(templates),
            "sample_videos_count": len(samples),
            "voice_options_count": len(voices),
            "cache_size": len(mock_data_manager._cache),
            "available_fixtures": ["users", "videos", "ai_responses"]
        }
        
        return MockDataResponse(
            success=True,
            data=stats,
            message="假資料統計獲取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))