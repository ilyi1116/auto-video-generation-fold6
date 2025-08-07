#!/usr/bin/env python3
"""
Video Processing Service - FFmpeg影片處理服務
專注於影片的底層處理：合成、編輯、渲染
與 Video Service 協作，提供FFmpeg集成功能
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 導入影片處理器
from src.shared.video_processor import VideoProcessor, VideoQuality, create_simple_video
from src.shared.config import get_service_settings

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 載入配置
settings = get_service_settings("video_service")
settings.api_port = 8006  # 使用不同的端口避免衝突

# 創建FastAPI應用
app = FastAPI(
    title="Video Processing Service",
    version="1.0.0",
    description="FFmpeg-based video processing and rendering service",
)

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:8000",  # API Gateway
        "http://localhost:8003",  # Video Service
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 初始化影片處理器
video_processor = VideoProcessor(
    output_dir="./video_output",
    temp_dir="./video_temp"
)

# Pydantic模型
class VideoCreationRequest(BaseModel):
    title: str
    images: List[str]  # 圖片URL或路徑列表
    background_music: Optional[str] = None  # 背景音樂URL或路徑
    duration_per_image: float = 3.0  # 每張圖片顯示時間
    transition_duration: float = 0.5  # 轉場時間
    quality: str = "high"  # low, medium, high, ultra
    output_format: str = "mp4"

class SubtitleRequest(BaseModel):
    video_path: str
    subtitle_text: str
    font_size: int = 24
    font_color: str = "white"
    background_color: str = "black@0.7"

class AudioMergeRequest(BaseModel):
    video_path: str
    audio_path: str
    video_volume: float = 0.5
    audio_volume: float = 1.0

class ProcessingStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float  # 0-100
    message: str
    output_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# 全域任務狀態儲存（實際應用中應使用資料庫或Redis）
processing_tasks = {}

def get_quality_enum(quality_str: str) -> VideoQuality:
    """轉換品質字串為枚舉"""
    quality_map = {
        "low": VideoQuality.LOW,
        "medium": VideoQuality.MEDIUM,
        "high": VideoQuality.HIGH,
        "ultra": VideoQuality.ULTRA,
    }
    return quality_map.get(quality_str.lower(), VideoQuality.HIGH)

async def update_task_status(task_id: str, status: str, progress: float, message: str, output_path: str = None):
    """更新任務狀態"""
    if task_id in processing_tasks:
        processing_tasks[task_id].update({
            "status": status,
            "progress": progress,
            "message": message,
            "output_path": output_path,
            "updated_at": datetime.utcnow()
        })

# 健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查"""
    # 檢查FFmpeg狀態
    ffmpeg_status = await video_processor.check_ffmpeg()
    
    return {
        "status": "healthy",
        "service": "video-processing-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "ffmpeg": ffmpeg_status,
    }

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Video Processing Service (FFmpeg)",
        "version": "1.0.0",
        "features": [
            "Video creation from images (FFmpeg)",
            "Subtitle overlay (FFmpeg)",
            "Audio-video merging (FFmpeg)",
            "Multiple quality options",
            "Background processing",
            "Integration with Video Service"
        ],
        "docs": "/docs",
        "health": "/health",
    }

@app.post("/api/v1/process/create-video")
async def create_video(
    request: VideoCreationRequest,
    background_tasks: BackgroundTasks
):
    """創建影片（異步處理）"""
    
    # 生成任務ID
    task_id = f"video_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # 初始化任務狀態
    processing_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Task created, waiting to start processing",
        "output_path": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "request": request.dict()
    }
    
    # 添加背景任務
    background_tasks.add_task(process_video_creation, task_id, request)
    
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "pending",
            "message": "Video creation task started. Use /api/v1/process/status/{task_id} to check progress."
        }
    }

async def process_video_creation(task_id: str, request: VideoCreationRequest):
    """背景處理影片創建"""
    try:
        await update_task_status(task_id, "processing", 10.0, "Starting video creation with FFmpeg")
        
        # 驗證圖片檔案
        valid_images = []
        for img_path in request.images:
            if img_path.startswith("http"):
                # 下載網路圖片
                await update_task_status(task_id, "processing", 20.0, f"Downloading image: {img_path}")
                # TODO: 實現圖片下載邏輯
                continue
            elif Path(img_path).exists():
                valid_images.append(img_path)
        
        if not valid_images:
            await update_task_status(task_id, "failed", 0.0, "No valid images found")
            return
        
        await update_task_status(task_id, "processing", 40.0, f"Processing {len(valid_images)} images with FFmpeg")
        
        # 準備輸出檔名
        output_filename = f"{request.title}_{task_id}.{request.output_format}"
        safe_filename = "".join(c for c in output_filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
        
        # 處理背景音樂
        background_music_path = None
        if request.background_music:
            if request.background_music.startswith("http"):
                await update_task_status(task_id, "processing", 50.0, "Downloading background music")
                # TODO: 實現音樂下載邏輯
            elif Path(request.background_music).exists():
                background_music_path = request.background_music
        
        await update_task_status(task_id, "processing", 60.0, "Generating video with FFmpeg")
        
        # 創建影片
        quality = get_quality_enum(request.quality)
        output_path = await video_processor.create_video_from_images(
            image_paths=valid_images,
            output_filename=safe_filename,
            duration_per_image=request.duration_per_image,
            transition_duration=request.transition_duration,
            background_music=background_music_path,
            quality=quality
        )
        
        await update_task_status(task_id, "processing", 90.0, "Finalizing video")
        
        # 獲取影片資訊
        video_info = await video_processor.get_video_info(output_path)
        
        await update_task_status(
            task_id, 
            "completed", 
            100.0, 
            f"Video created successfully. Duration: {video_info.get('duration', 0):.1f}s, Size: {video_info.get('width', 0)}x{video_info.get('height', 0)}",
            output_path
        )
        
    except Exception as e:
        logger.error(f"Video creation failed for task {task_id}: {e}")
        await update_task_status(task_id, "failed", 0.0, f"Video creation failed: {str(e)}")

@app.get("/api/v1/process/status/{task_id}")
async def get_processing_status(task_id: str):
    """獲取處理狀態"""
    
    if task_id not in processing_tasks:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    task_info = processing_tasks[task_id]
    
    return {
        "success": True,
        "data": ProcessingStatus(
            task_id=task_info["task_id"],
            status=task_info["status"],
            progress=task_info["progress"],
            message=task_info["message"],
            output_path=task_info["output_path"],
            created_at=task_info["created_at"],
            updated_at=task_info["updated_at"]
        )
    }

@app.get("/api/v1/process/download/{task_id}")
async def download_video(task_id: str):
    """下載生成的影片"""
    
    if task_id not in processing_tasks:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    task_info = processing_tasks[task_id]
    
    if task_info["status"] != "completed" or not task_info["output_path"]:
        raise HTTPException(
            status_code=400,
            detail="Video not ready for download"
        )
    
    output_path = task_info["output_path"]
    if not Path(output_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found"
        )
    
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=Path(output_path).name
    )

@app.post("/api/v1/process/subtitle")
async def add_subtitle(
    request: SubtitleRequest,
    background_tasks: BackgroundTasks
):
    """為影片添加字幕"""
    
    if not Path(request.video_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found"
        )
    
    task_id = f"subtitle_{int(datetime.utcnow().timestamp() * 1000)}"
    
    processing_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Subtitle task created",
        "output_path": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "request": request.dict()
    }
    
    background_tasks.add_task(process_subtitle_addition, task_id, request)
    
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "pending",
            "message": "Subtitle addition task started."
        }
    }

async def process_subtitle_addition(task_id: str, request: SubtitleRequest):
    """背景處理字幕添加"""
    try:
        await update_task_status(task_id, "processing", 30.0, "Adding subtitles with FFmpeg")
        
        output_filename = f"subtitled_{Path(request.video_path).stem}_{task_id}.mp4"
        
        output_path = await video_processor.add_subtitles(
            video_path=request.video_path,
            subtitle_text=request.subtitle_text,
            output_filename=output_filename,
            font_size=request.font_size,
            font_color=request.font_color,
            background_color=request.background_color
        )
        
        await update_task_status(
            task_id,
            "completed",
            100.0,
            "Subtitles added successfully with FFmpeg",
            output_path
        )
        
    except Exception as e:
        logger.error(f"Subtitle addition failed for task {task_id}: {e}")
        await update_task_status(task_id, "failed", 0.0, f"Subtitle addition failed: {str(e)}")

@app.post("/api/v1/process/merge-audio")
async def merge_audio(
    request: AudioMergeRequest,
    background_tasks: BackgroundTasks
):
    """合併音頻到影片"""
    
    if not Path(request.video_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Video file not found"
        )
    
    if not Path(request.audio_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )
    
    task_id = f"merge_{int(datetime.utcnow().timestamp() * 1000)}"
    
    processing_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Audio merge task created",
        "output_path": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "request": request.dict()
    }
    
    background_tasks.add_task(process_audio_merge, task_id, request)
    
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "pending",
            "message": "Audio merge task started."
        }
    }

async def process_audio_merge(task_id: str, request: AudioMergeRequest):
    """背景處理音頻合併"""
    try:
        await update_task_status(task_id, "processing", 40.0, "Merging audio with video using FFmpeg")
        
        output_filename = f"merged_{Path(request.video_path).stem}_{task_id}.mp4"
        
        output_path = await video_processor.merge_audio_video(
            video_path=request.video_path,
            audio_path=request.audio_path,
            output_filename=output_filename,
            video_volume=request.video_volume,
            audio_volume=request.audio_volume
        )
        
        await update_task_status(
            task_id,
            "completed",
            100.0,
            "Audio merged successfully with FFmpeg",
            output_path
        )
        
    except Exception as e:
        logger.error(f"Audio merge failed for task {task_id}: {e}")
        await update_task_status(task_id, "failed", 0.0, f"Audio merge failed: {str(e)}")

@app.get("/api/v1/process/info/{task_id}")
async def get_video_info(task_id: str):
    """獲取影片資訊"""
    
    if task_id not in processing_tasks:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    task_info = processing_tasks[task_id]
    
    if task_info["status"] != "completed" or not task_info["output_path"]:
        raise HTTPException(
            status_code=400,
            detail="Video not ready"
        )
    
    video_info = await video_processor.get_video_info(task_info["output_path"])
    
    return {
        "success": True,
        "data": video_info
    }

@app.delete("/api/v1/process/{task_id}")
async def delete_video(task_id: str):
    """删除影片檔案"""
    
    if task_id not in processing_tasks:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    task_info = processing_tasks[task_id]
    
    if task_info["output_path"] and Path(task_info["output_path"]).exists():
        Path(task_info["output_path"]).unlink()
    
    # 删除任務記錄
    del processing_tasks[task_id]
    
    return {
        "success": True,
        "message": "Video and task deleted successfully"
    }

@app.post("/api/v1/process/cleanup")
async def cleanup_temp_files():
    """清理暫存檔案"""
    
    video_processor.cleanup_temp_files()
    
    return {
        "success": True,
        "message": "Temporary files cleaned up"
    }

@app.get("/api/v1/process/ffmpeg-check")
async def check_ffmpeg():
    """檢查FFmpeg狀態"""
    
    ffmpeg_status = await video_processor.check_ffmpeg()
    
    return {
        "success": True,
        "data": ffmpeg_status
    }

if __name__ == "__main__":
    print("🎬 Starting Video Processing Service (FFmpeg)...")
    print("🛠️ Features:")
    print("   - FFmpeg-based video creation from images")
    print("   - Subtitle overlay with FFmpeg")
    print("   - Audio-video merging with FFmpeg")
    print("   - Multiple quality options (low/medium/high/ultra)")
    print("   - Background processing with status tracking")
    print("   - Dedicated FFmpeg integration")
    print(f"   - API Docs: http://localhost:8006/docs")
    print(f"   - Health Check: http://localhost:8006/health")
    
    # 檢查FFmpeg狀態
    print("\n🔧 Checking FFmpeg...")
    try:
        import asyncio
        async def check():
            status = await video_processor.check_ffmpeg()
            if status.get("available"):
                print(f"✅ FFmpeg ready: {status.get('version', 'Unknown version')}")
                print(f"   - H.264 Support: {'✅' if status.get('h264_supported') else '❌'}")
                print(f"   - MP4 Support: {'✅' if status.get('mp4_supported') else '❌'}")
            else:
                print(f"❌ FFmpeg not available: {status.get('error')}")
                print("   Please install FFmpeg to use video processing features")
        
        asyncio.run(check())
    except Exception as e:
        print(f"❌ FFmpeg check failed: {e}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info",
    )