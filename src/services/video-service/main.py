"""
Video Generation Service - Main Application

This service orchestrates the video generation process by coordinating:
- AI voice synthesis (Suno.ai Pro)
- Script generation (Google Gemini Pro)
- Image generation (Stable Diffusion)
- Video composition and rendering
"""

import asyncio
import logging
import os

# 導入統一資料庫模型
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.database import (
    ProcessingTask,
    Video,
    VideoAsset,
    get_async_db,
)
from src.shared.services.message_queue import (
    Message,
    MessageHandler,
    VideoEvents,
    get_message_queue,
    publish_video_event,
)
from src.shared.services.service_discovery import (
    get_service_registry,
)

from .ai.gemini_client import GeminiClient
from .ai.stable_diffusion_client import StableDiffusionClient
from .ai.suno_client import SunoAIClient
from .auth import verify_token
from .routers import entrepreneur_workflows, social_media, video_generation
from .video.composer import VideoComposer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Video Generation Service",
    description="AI-powered video generation and composition service",
    version="1.0.0",
)

# 服務註冊和訊息佇列
registry = get_service_registry()
message_queue = get_message_queue()


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    # 註冊服務實例
    from src.shared.services.service_discovery import (
        ServiceInstance,
        ServiceStatus,
    )

    video_service = ServiceInstance(
        name="video-service",
        host="localhost",
        port=8003,
        status=ServiceStatus.HEALTHY,
        metadata={"version": "1.0.0", "capabilities": ["video_generation", "ai_processing"]},
    )
    registry.register_service(video_service)

    # 啟動訊息佇列
    await message_queue.start()

    # 註冊事件處理器
    video_processor = VideoProcessingHandler()
    message_queue.register_handler(VideoEvents.VIDEO_PROCESSING_STARTED, video_processor)

    logger.info("Video service started and registered")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    await message_queue.stop()
    logger.info("Video service stopped")


class VideoProcessingHandler(MessageHandler):
    """影片處理事件處理器"""

    async def handle(self, message: Message) -> bool:
        """處理影片處理事件"""
        try:
            payload = message.payload
            video_id = payload.get("video_id")
            user_id = payload.get("user_id")

            if not video_id or not user_id:
                logger.error("Missing video_id or user_id in message payload")
                return False

            logger.info(f"Processing video event for video {video_id}")

            # 這裡可以添加額外的處理邏輯
            # 例如發送通知、更新分析數據等

            return True

        except Exception as e:
            logger.error(f"Failed to handle video processing event: {e}")
            return False


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://app.autovideo.com",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(video_generation.router, prefix="/api/v1/video", tags=["video-generation"])
app.include_router(social_media.router, prefix="/api/v1/social", tags=["social-media"])
app.include_router(
    entrepreneur_workflows.router,
    prefix="/api/v1/entrepreneur",
    tags=["entrepreneur-workflows"],
)

security = HTTPBearer()

# AI Clients initialization
suno_client = SunoAIClient(api_key=os.getenv("SUNO_API_KEY"))
gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
stable_diffusion_client = StableDiffusionClient(api_key=os.getenv("STABLE_DIFFUSION_API_KEY"))
video_composer = VideoComposer()


class VideoGenerationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    theme: str = Field(..., description="Video theme/topic")
    style: Optional[str] = Field("modern", description="Visual style preference")
    duration: Optional[int] = Field(60, ge=15, le=300, description="Video duration in seconds")
    voice_type: Optional[str] = Field("default", description="Voice style for narration")
    music_genre: Optional[str] = Field("ambient", description="Background music genre")
    include_captions: bool = Field(True, description="Whether to include captions")
    target_platform: Optional[str] = Field(
        "youtube", description="Target platform (youtube, tiktok, instagram)"
    )


class VideoProjectResponse(BaseModel):
    project_id: int
    title: str
    status: str
    progress: int
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    preview_url: Optional[str] = None
    final_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "video-generation",
        "timestamp": datetime.utcnow(),
        "ai_services": {
            "suno": await suno_client.health_check(),
            "gemini": await gemini_client.health_check(),
            "stable_diffusion": await stable_diffusion_client.health_check(),
        },
    }


@app.post("/api/v1/video/generate", response_model=VideoProjectResponse)
async def create_video_project(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_async_db),
):
    """Create a new video generation project"""

    # Verify user authentication
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Create video record using unified database model
    video = Video(
        user_id=user_id,
        title=request.title,
        description=request.description,
        script_content=f"Theme: {request.theme}, Style: {request.style}",
        voice_parameters={
            "voice_type": request.voice_type,
            "music_genre": request.music_genre,
        },
        video_parameters={
            "style": request.style,
            "duration": request.duration,
            "target_platform": request.target_platform,
            "include_captions": request.include_captions,
        },
        status="initializing",
        progress_percentage=0,
    )

    async with db:
        db.add(video)
        await db.commit()
        await db.refresh(video)

    # 發布影片創建事件
    await publish_video_event(
        VideoEvents.VIDEO_CREATED,
        video_id=video.id,
        user_id=user_id,
        title=video.title,
        description=video.description,
    )

    # Start background video generation
    background_tasks.add_task(generate_video_pipeline, video.id, request, user_id)

    logger.info(f"Created video project {video.id} for user {user_id}")

    return VideoProjectResponse(
        project_id=video.id,
        title=video.title,
        status=video.status,
        progress=video.progress_percentage,
        created_at=video.created_at,
        estimated_completion=None,
        preview_url=None,
        final_url=None,
    )


@app.get("/api/v1/video/projects/{project_id}", response_model=VideoProjectResponse)
async def get_video_project(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_async_db),
):
    """Get video project status and details"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    async with db:
        from sqlalchemy import select

        result = await db.execute(select(Video).where(Video.id == project_id))
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail="Project not found")

        if video.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return VideoProjectResponse(
            project_id=video.id,
            title=video.title,
            status=video.status,
            progress=video.progress_percentage,
            created_at=video.created_at,
            estimated_completion=video.completed_at,
            preview_url=video.thumbnail_url,
            final_url=video.final_video_url,
            thumbnail_url=video.thumbnail_url,
        )


@app.get("/api/v1/video/projects", response_model=List[VideoProjectResponse])
async def list_user_projects(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db_connection),
    limit: int = 20,
    offset: int = 0,
):
    """List user's video projects"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    projects = await VideoProject.get_by_user(db, user_id, limit=limit, offset=offset)

    return [
        VideoProjectResponse(
            project_id=project.id,
            title=project.title,
            status=project.status,
            progress=project.progress,
            created_at=project.created_at,
            estimated_completion=project.estimated_completion,
            preview_url=project.preview_url,
            final_url=project.final_url,
        )
        for project in projects
    ]


@app.get("/api/v1/video/projects/{project_id}/tasks")
async def get_project_tasks(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_async_db),
):
    """Get processing tasks for a video project"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    async with db:
        from sqlalchemy import select

        # 驗證用戶擁有這個影片項目
        result = await db.execute(select(Video).where(Video.id == project_id))
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail="Project not found")

        if video.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 獲取處理任務
        tasks_result = await db.execute(
            select(ProcessingTask)
            .where(ProcessingTask.video_id == project_id)
            .order_by(ProcessingTask.created_at)
        )
        tasks = tasks_result.scalars().all()

        return {
            "project_id": project_id,
            "tasks": [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "task_name": task.task_name,
                    "status": task.status,
                    "progress": task.progress_percentage,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "error_message": task.error_message,
                }
                for task in tasks
            ],
        }


@app.get("/api/v1/video/projects/{project_id}/assets")
async def get_project_assets(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_async_db),
):
    """Get video assets for a project"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    async with db:
        from sqlalchemy import select

        # 驗證用戶擁有這個影片項目
        result = await db.execute(select(Video).where(Video.id == project_id))
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail="Project not found")

        if video.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 獲取資產
        assets_result = await db.execute(
            select(VideoAsset)
            .where(VideoAsset.video_id == project_id)
            .order_by(VideoAsset.created_at)
        )
        assets = assets_result.scalars().all()

        return {
            "project_id": project_id,
            "assets": [
                {
                    "id": asset.id,
                    "asset_type": asset.asset_type,
                    "asset_name": asset.asset_name,
                    "file_url": asset.file_url,
                    "file_size_bytes": asset.file_size_bytes,
                    "mime_type": asset.mime_type,
                    "duration_seconds": asset.duration_seconds,
                    "generation_parameters": asset.generation_parameters,
                    "created_at": asset.created_at,
                }
                for asset in assets
            ],
        }


@app.delete("/api/v1/video/projects/{project_id}")
async def delete_video_project(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_async_db),
):
    """Delete a video project"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    project = await VideoProject.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await project.delete(db)

    # Clean up associated files and resources
    try:
        # Clean up generated files
        if project.voice_url:
            await cleanup_file(project.voice_url)
        if project.music_url:
            await cleanup_file(project.music_url)
        if project.preview_url:
            await cleanup_file(project.preview_url)
        if project.final_url:
            await cleanup_file(project.final_url)
        if project.thumbnail_url:
            await cleanup_file(project.thumbnail_url)

        # Clean up image files
        if project.image_urls:
            for image_url in project.image_urls:
                await cleanup_file(image_url)

        logger.info(f"Cleaned up resources for project {project_id}")
    except Exception as e:
        logger.warning(f"Failed to cleanup some resources for project {project_id}: {e}")

    return {"message": "Project deleted successfully"}


async def generate_video_pipeline(project_id: int, request: VideoGenerationRequest, user_id: int):
    """Background video generation pipeline"""

    from src.shared.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select

            # 獲取影片記錄
            result = await db.execute(select(Video).where(Video.id == project_id))
            video = result.scalar_one_or_none()

            if not video:
                logger.error(f"Video project {project_id} not found")
                return

            # 發布處理開始事件
            await publish_video_event(
                VideoEvents.VIDEO_PROCESSING_STARTED,
                video_id=project_id,
                user_id=user_id,
                stage="initialization",
            )

            # Phase 1: Script Generation (20% progress)
            await update_video_progress(db, video, "generating_script", 10)
            logger.info(f"Generating script for project {project_id}")

            script_response = await gemini_client.generate_script(
                theme=request.theme,
                duration=request.duration,
                style=request.style,
                target_platform=request.target_platform,
            )

            video.script_content = script_response.content
            await update_video_progress(db, video, "generating_script", 20)

            # 創建腳本處理任務
            script_task = ProcessingTask(
                video_id=project_id,
                task_type="script_generation",
                task_name="Generate script content",
                status="completed",
                progress_percentage=100,
                result={"content": script_response.content, "scenes": script_response.scenes},
            )
            db.add(script_task)

            # Phase 2: Voice Generation (40% progress)
            await update_video_progress(db, video, "generating_voice", 25)
            logger.info(f"Generating voice for project {project_id}")

            voice_response = await suno_client.generate_voice(
                text=script_response.narration_text,
                voice_type=request.voice_type,
                music_genre=request.music_genre,
            )

            # 保存語音資產
            voice_asset = VideoAsset(
                video_id=project_id,
                asset_type="audio",
                asset_name="Voice narration",
                file_url=voice_response.audio_url,
                generation_parameters={"voice_type": request.voice_type},
            )
            db.add(voice_asset)

            if voice_response.music_url:
                music_asset = VideoAsset(
                    video_id=project_id,
                    asset_type="music",
                    asset_name="Background music",
                    file_url=voice_response.music_url,
                    generation_parameters={"music_genre": request.music_genre},
                )
                db.add(music_asset)

            await update_video_progress(db, video, "generating_voice", 40)

            # Phase 3: Image Generation (60% progress)
            await update_video_progress(db, video, "generating_images", 45)
            logger.info(f"Generating images for project {project_id}")

            image_tasks = []
            for i, scene in enumerate(script_response.scenes):
                image_tasks.append(
                    stable_diffusion_client.generate_image(
                        prompt=scene.visual_description,
                        style=request.style,
                        aspect_ratio=get_aspect_ratio(request.target_platform),
                    )
                )

            image_responses = await asyncio.gather(*image_tasks)

            # 保存圖片資產
            for i, img_response in enumerate(image_responses):
                image_asset = VideoAsset(
                    video_id=project_id,
                    asset_type="image",
                    asset_name=f"Scene {i+1} image",
                    file_url=img_response.url,
                    generation_parameters={"style": request.style, "scene": i},
                )
                db.add(image_asset)

            await update_video_progress(db, video, "generating_images", 60)

            # Phase 4: Video Composition (80% progress)
            await update_video_progress(db, video, "composing", 65)
            logger.info(f"Composing video for project {project_id}")

            image_urls = [img.url for img in image_responses]
            composition_result = await video_composer.create_video(
                script_scenes=script_response.scenes,
                voice_url=voice_response.audio_url,
                music_url=voice_response.music_url,
                image_urls=image_urls,
                include_captions=request.include_captions,
                target_platform=request.target_platform,
            )

            video.thumbnail_url = composition_result.preview_url
            await update_video_progress(db, video, "composing", 80)

            # Phase 5: Final Rendering (100% progress)
            await update_video_progress(db, video, "rendering", 85)
            logger.info(f"Final rendering for project {project_id}")

            final_result = await video_composer.render_final(
                composition_id=composition_result.composition_id, quality="high"
            )

            video.final_video_url = final_result.video_url
            video.thumbnail_url = final_result.thumbnail_url
            video.duration_seconds = final_result.duration
            video.file_size_bytes = final_result.file_size

            await update_video_progress(db, video, "completed", 100)

            # 發布處理完成事件
            await publish_video_event(
                VideoEvents.VIDEO_PROCESSING_COMPLETED,
                video_id=project_id,
                user_id=user_id,
                final_video_url=video.final_video_url,
                thumbnail_url=video.thumbnail_url,
                duration_seconds=video.duration_seconds,
                file_size_bytes=video.file_size_bytes,
            )

            logger.info(f"Video generation completed for project {project_id}")

        except Exception as e:
            logger.error(f"Video generation failed for project {project_id}: {str(e)}")
            try:
                await update_video_progress(db, video, "failed", video.progress_percentage)

                # 發布處理失敗事件
                await publish_video_event(
                    VideoEvents.VIDEO_PROCESSING_FAILED,
                    video_id=project_id,
                    user_id=user_id,
                    error=str(e),
                    stage=video.status if video else "unknown",
                )

                # 創建錯誤任務記錄
                error_task = ProcessingTask(
                    video_id=project_id,
                    task_type="error_handling",
                    task_name="Video generation error",
                    status="failed",
                    error_message=str(e),
                )
                db.add(error_task)
                await db.commit()
            except Exception as commit_error:
                logger.error(f"Failed to save error state: {commit_error}")


async def update_video_progress(db, video: Video, status: str, progress: int):
    """更新影片進度和狀態"""
    video.status = status
    video.progress_percentage = progress

    if status == "completed":
        video.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(video)


def get_aspect_ratio(platform: str) -> str:
    """Get aspect ratio based on target platform"""
    ratios = {
        "youtube": "16:9",
        "tiktok": "9:16",
        "instagram": "1:1",
        "default": "16:9",
    }
    return ratios.get(platform, "16:9")


async def cleanup_file(file_url: str):
    """Clean up file from storage"""
    try:
        # Extract file path from URL
        if file_url.startswith("http"):
            # Handle remote files
            pass
        else:
            # Handle local files
            import os

            if os.path.exists(file_url):
                os.remove(file_url)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_url}: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
