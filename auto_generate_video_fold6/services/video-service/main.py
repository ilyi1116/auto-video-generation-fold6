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
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .ai.gemini_client import GeminiClient
from .ai.stable_diffusion_client import StableDiffusionClient
from .ai.suno_client import SunoAIClient
from .auth import verify_token
from .database import get_db_connection
from .models.video_project import VideoProject, VideoStatus
from .routers import social_media, video_generation, entrepreneur_workflows
from .video.composer import VideoComposer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Video Generation Service",
    description="AI-powered video generation and composition service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    video_generation.router, prefix="/api/v1/video", tags=["video-generation"]
)
app.include_router(
    social_media.router, prefix="/api/v1/social", tags=["social-media"]
)
app.include_router(
    entrepreneur_workflows.router, prefix="/api/v1/entrepreneur", tags=["entrepreneur-workflows"]
)

security = HTTPBearer()

# AI Clients initialization
suno_client = SunoAIClient(api_key=os.getenv("SUNO_API_KEY"))
gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
stable_diffusion_client = StableDiffusionClient(
    api_key=os.getenv("STABLE_DIFFUSION_API_KEY")
)
video_composer = VideoComposer()


class VideoGenerationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    theme: str = Field(..., description="Video theme/topic")
    style: Optional[str] = Field(
        "modern", description="Visual style preference"
    )
    duration: Optional[int] = Field(
        60, ge=15, le=300, description="Video duration in seconds"
    )
    voice_type: Optional[str] = Field(
        "default", description="Voice style for narration"
    )
    music_genre: Optional[str] = Field(
        "ambient", description="Background music genre"
    )
    include_captions: bool = Field(
        True, description="Whether to include captions"
    )
    target_platform: Optional[str] = Field(
        "youtube", description="Target platform (youtube, tiktok, instagram)"
    )


class VideoProjectResponse(BaseModel):
    project_id: str
    title: str
    status: VideoStatus
    progress: int
    created_at: datetime
    estimated_completion: Optional[datetime]
    preview_url: Optional[str]
    final_url: Optional[str]


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
    db=Depends(get_db_connection),
):
    """Create a new video generation project"""

    # Verify user authentication
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Invalid authentication token"
        )

    # Create project record
    project_id = str(uuid.uuid4())
    project = VideoProject(
        id=project_id,
        user_id=user_id,
        title=request.title,
        description=request.description,
        theme=request.theme,
        style=request.style,
        duration=request.duration,
        voice_type=request.voice_type,
        music_genre=request.music_genre,
        include_captions=request.include_captions,
        target_platform=request.target_platform,
        status=VideoStatus.INITIALIZING,
        progress=0,
        created_at=datetime.utcnow(),
    )

    # Save to database
    await project.save(db)

    # Start background video generation
    background_tasks.add_task(generate_video_pipeline, project_id, request)

    logger.info(f"Created video project {project_id} for user {user_id}")

    return VideoProjectResponse(
        project_id=project_id,
        title=request.title,
        status=VideoStatus.INITIALIZING,
        progress=0,
        created_at=project.created_at,
        estimated_completion=None,
        preview_url=None,
        final_url=None,
    )


@app.get(
    "/api/v1/video/projects/{project_id}", response_model=VideoProjectResponse
)
async def get_video_project(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db_connection),
):
    """Get video project status and details"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Invalid authentication token"
        )

    project = await VideoProject.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return VideoProjectResponse(
        project_id=project.id,
        title=project.title,
        status=project.status,
        progress=project.progress,
        created_at=project.created_at,
        estimated_completion=project.estimated_completion,
        preview_url=project.preview_url,
        final_url=project.final_url,
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
        raise HTTPException(
            status_code=401, detail="Invalid authentication token"
        )

    projects = await VideoProject.get_by_user(
        db, user_id, limit=limit, offset=offset
    )

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


@app.delete("/api/v1/video/projects/{project_id}")
async def delete_video_project(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db_connection),
):
    """Delete a video project"""

    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Invalid authentication token"
        )

    project = await VideoProject.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await project.delete(db)

    # TODO: Clean up associated files and resources

    return {"message": "Project deleted successfully"}


async def generate_video_pipeline(
    project_id: str, request: VideoGenerationRequest
):
    """Background video generation pipeline"""

    try:
        db = get_db_connection()
        project = await VideoProject.get_by_id(db, project_id)

        if not project:
            logger.error(f"Project {project_id} not found")
            return

        # Phase 1: Script Generation (20% progress)
        await project.update_status(db, VideoStatus.GENERATING_SCRIPT, 10)
        logger.info(f"Generating script for project {project_id}")

        script_response = await gemini_client.generate_script(
            theme=request.theme,
            duration=request.duration,
            style=request.style,
            target_platform=request.target_platform,
        )

        project.script_content = script_response.content
        project.script_scenes = script_response.scenes
        await project.update_status(db, VideoStatus.GENERATING_SCRIPT, 20)

        # Phase 2: Voice Generation (40% progress)
        await project.update_status(db, VideoStatus.GENERATING_VOICE, 25)
        logger.info(f"Generating voice for project {project_id}")

        voice_response = await suno_client.generate_voice(
            text=script_response.narration_text,
            voice_type=request.voice_type,
            music_genre=request.music_genre,
        )

        project.voice_url = voice_response.audio_url
        project.music_url = voice_response.music_url
        await project.update_status(db, VideoStatus.GENERATING_VOICE, 40)

        # Phase 3: Image Generation (60% progress)
        await project.update_status(db, VideoStatus.GENERATING_IMAGES, 45)
        logger.info(f"Generating images for project {project_id}")

        image_tasks = []
        for scene in script_response.scenes:
            image_tasks.append(
                stable_diffusion_client.generate_image(
                    prompt=scene.visual_description,
                    style=request.style,
                    aspect_ratio=get_aspect_ratio(request.target_platform),
                )
            )

        image_responses = await asyncio.gather(*image_tasks)
        project.image_urls = [img.url for img in image_responses]
        await project.update_status(db, VideoStatus.GENERATING_IMAGES, 60)

        # Phase 4: Video Composition (80% progress)
        await project.update_status(db, VideoStatus.COMPOSING, 65)
        logger.info(f"Composing video for project {project_id}")

        composition_result = await video_composer.create_video(
            script_scenes=script_response.scenes,
            voice_url=voice_response.audio_url,
            music_url=voice_response.music_url,
            image_urls=project.image_urls,
            include_captions=request.include_captions,
            target_platform=request.target_platform,
        )

        project.preview_url = composition_result.preview_url
        await project.update_status(db, VideoStatus.COMPOSING, 80)

        # Phase 5: Final Rendering (100% progress)
        await project.update_status(db, VideoStatus.RENDERING, 85)
        logger.info(f"Final rendering for project {project_id}")

        final_result = await video_composer.render_final(
            composition_id=composition_result.composition_id, quality="high"
        )

        project.final_url = final_result.video_url
        project.thumbnail_url = final_result.thumbnail_url
        await project.update_status(db, VideoStatus.COMPLETED, 100)

        logger.info(f"Video generation completed for project {project_id}")

    except Exception as e:
        logger.error(
            f"Video generation failed for project {project_id}: {str(e)}"
        )
        try:
            await project.update_status(
                db, VideoStatus.FAILED, project.progress
            )
            project.error_message = str(e)
            await project.save(db)
        except:
            pass


def get_aspect_ratio(platform: str) -> str:
    """Get aspect ratio based on target platform"""
    ratios = {
        "youtube": "16:9",
        "tiktok": "9:16",
        "instagram": "1:1",
        "default": "16:9",
    }
    return ratios.get(platform, "16:9")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
