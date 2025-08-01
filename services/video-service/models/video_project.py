"""
Video Project Database Models

This module defines the database models for video generation projects,
including status tracking, media associations, and user relationships.
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import asyncpg
import json
import logging

logger = logging.getLogger(__name__)


class VideoStatus(str, Enum):
    """Video generation status enumeration"""

    INITIALIZING = "initializing"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_VOICE = "generating_voice"
    GENERATING_IMAGES = "generating_images"
    COMPOSING = "composing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoProject(BaseModel):
    """Video project model"""

    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    theme: str
    style: str = "modern"
    duration: int = 60  # seconds
    voice_type: str = "default"
    music_genre: str = "ambient"
    include_captions: bool = True
    target_platform: str = "youtube"

    # Generation status
    status: VideoStatus = VideoStatus.INITIALIZING
    progress: int = 0  # 0-100
    error_message: Optional[str] = None

    # Generated content
    script_content: Optional[str] = None
    script_scenes: Optional[List[Dict[str, Any]]] = None
    voice_url: Optional[str] = None
    music_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    preview_url: Optional[str] = None
    final_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

    # Analytics
    view_count: int = 0
    download_count: int = 0
    like_count: int = 0

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    @classmethod
    async def create_table(cls, db_pool):
        """Create the video_projects table"""

        create_sql = """
        CREATE TABLE IF NOT EXISTS video_projects (
            id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            theme VARCHAR(100) NOT NULL,
            style VARCHAR(50) DEFAULT 'modern',
            duration INTEGER DEFAULT 60,
            voice_type VARCHAR(50) DEFAULT 'default',
            music_genre VARCHAR(50) DEFAULT 'ambient',
            include_captions BOOLEAN DEFAULT TRUE,
            target_platform VARCHAR(20) DEFAULT 'youtube',
            
            status VARCHAR(30) DEFAULT 'initializing',
            progress INTEGER DEFAULT 0,
            error_message TEXT,
            
            script_content TEXT,
            script_scenes JSONB,
            voice_url VARCHAR(500),
            music_url VARCHAR(500),
            image_urls JSONB,
            preview_url VARCHAR(500),
            final_url VARCHAR(500),
            thumbnail_url VARCHAR(500),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            completed_at TIMESTAMP,
            estimated_completion TIMESTAMP,
            
            view_count INTEGER DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_video_projects_user_id ON video_projects(user_id);
        CREATE INDEX IF NOT EXISTS idx_video_projects_status ON video_projects(status);
        CREATE INDEX IF NOT EXISTS idx_video_projects_created_at ON video_projects(created_at DESC);
        """

        async with db_pool.acquire() as conn:
            await conn.execute(create_sql)

    async def save(self, db_pool):
        """Save video project to database"""

        try:
            async with db_pool.acquire() as conn:
                # Check if project exists
                existing = await conn.fetchrow(
                    "SELECT id FROM video_projects WHERE id = $1", self.id
                )

                if existing:
                    # Update existing project
                    await self._update_project(conn)
                else:
                    # Insert new project
                    await self._insert_project(conn)

                self.updated_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to save video project {self.id}: {str(e)}")
            raise

    async def _insert_project(self, conn):
        """Insert new project into database"""

        insert_sql = """
        INSERT INTO video_projects (
            id, user_id, title, description, theme, style, duration,
            voice_type, music_genre, include_captions, target_platform,
            status, progress, error_message,
            script_content, script_scenes, voice_url, music_url, image_urls,
            preview_url, final_url, thumbnail_url,
            created_at, updated_at, completed_at, estimated_completion,
            view_count, download_count, like_count
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                 $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26,
                 $27, $28, $29)
        """

        await conn.execute(
            insert_sql,
            self.id,
            self.user_id,
            self.title,
            self.description,
            self.theme,
            self.style,
            self.duration,
            self.voice_type,
            self.music_genre,
            self.include_captions,
            self.target_platform,
            self.status.value,
            self.progress,
            self.error_message,
            self.script_content,
            json.dumps(self.script_scenes) if self.script_scenes else None,
            self.voice_url,
            self.music_url,
            json.dumps(self.image_urls) if self.image_urls else None,
            self.preview_url,
            self.final_url,
            self.thumbnail_url,
            self.created_at,
            self.updated_at,
            self.completed_at,
            self.estimated_completion,
            self.view_count,
            self.download_count,
            self.like_count,
        )

    async def _update_project(self, conn):
        """Update existing project in database"""

        update_sql = """
        UPDATE video_projects SET
            title = $2, description = $3, theme = $4, style = $5, duration = $6,
            voice_type = $7, music_genre = $8, include_captions = $9, target_platform = $10,
            status = $11, progress = $12, error_message = $13,
            script_content = $14, script_scenes = $15, voice_url = $16, music_url = $17,
            image_urls = $18, preview_url = $19, final_url = $20, thumbnail_url = $21,
            updated_at = $22, completed_at = $23, estimated_completion = $24,
            view_count = $25, download_count = $26, like_count = $27
        WHERE id = $1
        """

        await conn.execute(
            update_sql,
            self.id,
            self.title,
            self.description,
            self.theme,
            self.style,
            self.duration,
            self.voice_type,
            self.music_genre,
            self.include_captions,
            self.target_platform,
            self.status.value,
            self.progress,
            self.error_message,
            self.script_content,
            json.dumps(self.script_scenes) if self.script_scenes else None,
            self.voice_url,
            self.music_url,
            json.dumps(self.image_urls) if self.image_urls else None,
            self.preview_url,
            self.final_url,
            self.thumbnail_url,
            datetime.utcnow(),
            self.completed_at,
            self.estimated_completion,
            self.view_count,
            self.download_count,
            self.like_count,
        )

    @classmethod
    async def get_by_id(
        cls, db_pool, project_id: str
    ) -> Optional["VideoProject"]:
        """Get video project by ID"""

        try:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM video_projects WHERE id = $1", project_id
                )

                if not row:
                    return None

                return cls._from_db_row(row)

        except Exception as e:
            logger.error(f"Failed to get video project {project_id}: {str(e)}")
            return None

    @classmethod
    async def get_by_user(
        cls,
        db_pool,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[VideoStatus] = None,
    ) -> List["VideoProject"]:
        """Get video projects by user ID"""

        try:
            async with db_pool.acquire() as conn:
                where_clause = "WHERE user_id = $1"
                params = [user_id]

                if status_filter:
                    where_clause += " AND status = $2"
                    params.append(status_filter.value)
                    params.extend([limit, offset])
                    param_nums = "$3, $4"
                else:
                    params.extend([limit, offset])
                    param_nums = "$2, $3"

                query = f"""
                SELECT * FROM video_projects 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT {param_nums.split(", ")[0]} OFFSET {param_nums.split(", ")[1]}
                """

                rows = await conn.fetch(query, *params)

                return [cls._from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(
                f"Failed to get video projects for user {user_id}: {str(e)}"
            )
            return []

    @classmethod
    def _from_db_row(cls, row) -> "VideoProject":
        """Create VideoProject instance from database row"""

        return cls(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            description=row["description"],
            theme=row["theme"],
            style=row["style"],
            duration=row["duration"],
            voice_type=row["voice_type"],
            music_genre=row["music_genre"],
            include_captions=row["include_captions"],
            target_platform=row["target_platform"],
            status=VideoStatus(row["status"]),
            progress=row["progress"],
            error_message=row["error_message"],
            script_content=row["script_content"],
            script_scenes=json.loads(row["script_scenes"])
            if row["script_scenes"]
            else None,
            voice_url=row["voice_url"],
            music_url=row["music_url"],
            image_urls=json.loads(row["image_urls"])
            if row["image_urls"]
            else None,
            preview_url=row["preview_url"],
            final_url=row["final_url"],
            thumbnail_url=row["thumbnail_url"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            estimated_completion=row["estimated_completion"],
            view_count=row["view_count"],
            download_count=row["download_count"],
            like_count=row["like_count"],
        )

    async def update_status(
        self,
        db_pool,
        status: VideoStatus,
        progress: int,
        error_message: Optional[str] = None,
    ):
        """Update project status and progress"""

        self.status = status
        self.progress = progress
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

        # Set completion time if status is completed or failed
        if status in [VideoStatus.COMPLETED, VideoStatus.FAILED]:
            self.completed_at = datetime.utcnow()

        # Update estimated completion for active statuses
        if status in [
            VideoStatus.GENERATING_SCRIPT,
            VideoStatus.GENERATING_VOICE,
            VideoStatus.GENERATING_IMAGES,
            VideoStatus.COMPOSING,
            VideoStatus.RENDERING,
        ]:
            # Rough estimation based on current progress
            remaining_time = max(
                0, (100 - progress) * 2
            )  # 2 seconds per percent
            self.estimated_completion = datetime.utcnow() + timedelta(
                seconds=remaining_time
            )

        await self.save(db_pool)

    async def delete(self, db_pool):
        """Delete video project from database"""

        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM video_projects WHERE id = $1", self.id
                )

                logger.info(f"Deleted video project: {self.id}")

        except Exception as e:
            logger.error(f"Failed to delete video project {self.id}: {str(e)}")
            raise

    async def increment_view_count(self, db_pool):
        """Increment view count"""

        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE video_projects SET view_count = view_count + 1 WHERE id = $1",
                    self.id,
                )

                self.view_count += 1

        except Exception as e:
            logger.error(
                f"Failed to increment view count for {self.id}: {str(e)}"
            )

    async def increment_download_count(self, db_pool):
        """Increment download count"""

        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE video_projects SET download_count = download_count + 1 WHERE id = $1",
                    self.id,
                )

                self.download_count += 1

        except Exception as e:
            logger.error(
                f"Failed to increment download count for {self.id}: {str(e)}"
            )

    async def toggle_like(self, db_pool, increment: bool = True):
        """Toggle like count"""

        try:
            async with db_pool.acquire() as conn:
                operation = "+" if increment else "-"
                await conn.execute(
                    f"UPDATE video_projects SET like_count = like_count {operation} 1 WHERE id = $1",
                    self.id,
                )

                self.like_count += 1 if increment else -1

        except Exception as e:
            logger.error(f"Failed to toggle like for {self.id}: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "theme": self.theme,
            "style": self.style,
            "duration": self.duration,
            "voice_type": self.voice_type,
            "music_genre": self.music_genre,
            "include_captions": self.include_captions,
            "target_platform": self.target_platform,
            "status": self.status.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "preview_url": self.preview_url,
            "final_url": self.final_url,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at
            else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "view_count": self.view_count,
            "download_count": self.download_count,
            "like_count": self.like_count,
        }
