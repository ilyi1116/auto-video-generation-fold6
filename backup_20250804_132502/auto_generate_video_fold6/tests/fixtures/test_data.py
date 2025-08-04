#!/usr/bin/env python3
"""
測試數據和 Fixtures
提供測試所需的固定數據
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# ================================
# 用戶測試數據
# ================================


@pytest.fixture
def sample_user_data():
    """範例用戶數據"""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "Test123456!",
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat(),
        "credits": {"total": 1000, "used": 100, "remaining": 900},
    }


@pytest.fixture
def multiple_users_data():
    """多個用戶數據"""
    users = []
    for i in range(5):
        users.append(
            {
                "id": str(uuid.uuid4()),
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "full_name": f"User {i}",
                "password": "Test123456!",
                "is_verified": i % 2 == 0,  # 偶數用戶已驗證
                "created_at": (
                    datetime.utcnow() - timedelta(days=i)
                ).isoformat(),
                "credits": {
                    "total": 1000 + i * 100,
                    "used": i * 50,
                    "remaining": 1000 + i * 50,
                },
            }
        )
    return users


# ================================
# 專案測試數據
# ================================


@pytest.fixture
def sample_project_data():
    """範例專案數據"""
    return {
        "id": str(uuid.uuid4()),
        "title": "Test Video Project",
        "description": "A test video about AI technology",
        "status": "draft",
        "settings": {
            "aspect_ratio": "9:16",
            "duration": 60,
            "style": "engaging",
            "voice_style": "professional",
            "music": True,
            "captions": True,
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def project_with_assets():
    """包含資產的專案數據"""
    project_id = str(uuid.uuid4())
    return {
        "id": project_id,
        "title": "Complete Video Project",
        "description": "A complete video project with all assets",
        "status": "completed",
        "settings": {
            "aspect_ratio": "9:16",
            "duration": 60,
            "style": "engaging",
            "voice_style": "professional",
        },
        "assets": {
            "script": {
                "id": str(uuid.uuid4()),
                "content": "Welcome to the future of AI! In this video, we'll explore...",
                "word_count": 150,
                "estimated_duration": 60,
                "status": "approved",
            },
            "images": [
                {
                    "id": str(uuid.uuid4()),
                    "url": f"https://storage.example.com/{project_id}/image1.jpg",
                    "prompt": "Modern AI workspace with holographic displays",
                    "style": "modern",
                    "resolution": "1080p",
                },
                {
                    "id": str(uuid.uuid4()),
                    "url": f"https://storage.example.com/{project_id}/image2.jpg",
                    "prompt": "Futuristic robot assistant helping with tasks",
                    "style": "cyberpunk",
                    "resolution": "1080p",
                },
            ],
            "audio": {
                "id": str(uuid.uuid4()),
                "url": f"https://storage.example.com/{project_id}/voice.mp3",
                "duration": 58.5,
                "voice_style": "professional",
                "language": "en",
            },
            "music": {
                "id": str(uuid.uuid4()),
                "url": f"https://storage.example.com/{project_id}/background.mp3",
                "duration": 60,
                "style": "electronic",
                "mood": "energetic",
            },
            "video": {
                "id": str(uuid.uuid4()),
                "url": f"https://storage.example.com/{project_id}/final.mp4",
                "duration": 60,
                "resolution": "1080p",
                "file_size": 15728640,  # 15MB
            },
        },
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ================================
# AI 生成測試數據
# ================================


@pytest.fixture
def script_generation_request():
    """腳本生成請求數據"""
    return {
        "topic": "5 Amazing AI Tools for Productivity",
        "style": "engaging",
        "duration_seconds": 60,
        "target_audience": "professionals",
        "keywords": ["AI", "productivity", "automation", "efficiency"],
        "tone": "enthusiastic",
    }


@pytest.fixture
def script_generation_response():
    """腳本生成回應數據"""
    return {
        "script_id": str(uuid.uuid4()),
        "content": """🚀 Ready to supercharge your productivity with AI?

Today I'm sharing 5 incredible AI tools that will transform how you work!

First up - ChatGPT for writing and brainstorming. This powerhouse can draft emails, create content, and solve complex problems in seconds.

Second - Midjourney for stunning visuals. Generate professional graphics without design skills!

Third - Notion AI for smart note-taking. It organizes your thoughts and creates summaries automatically.

Fourth - Grammarly for perfect writing. Say goodbye to typos and unclear sentences.

Finally - Calendly AI for seamless scheduling. It finds the perfect meeting times for everyone.

These tools aren't just cool - they're game-changers! Which one will you try first? Let me know in the comments! 👇""",
        "word_count": 142,
        "estimated_duration": 58,
        "style": "engaging",
        "status": "generated",
        "generation_time_seconds": 3.2,
        "metadata": {
            "model_used": "gpt-4",
            "temperature": 0.8,
            "tokens_used": 456,
        },
    }


@pytest.fixture
def image_generation_request():
    """圖像生成請求數據"""
    return {
        "prompt": "Modern office with AI hologram, clean minimalist design, blue accents",
        "style": "modern",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "negative_prompt": "blurry, low quality, distorted, dark",
        "guidance_scale": 7.5,
        "num_inference_steps": 50,
    }


@pytest.fixture
def music_generation_request():
    """音樂生成請求數據"""
    return {
        "prompt": "Upbeat electronic music for tech product showcase",
        "style": "electronic",
        "duration": 60,
        "instrumental": True,
        "mood": "energetic",
        "tempo": "medium",
        "tags": ["upbeat", "modern", "tech", "corporate"],
    }


# ================================
# 趨勢分析測試數據
# ================================


@pytest.fixture
def trending_keywords_data():
    """趨勢關鍵字數據"""
    return {
        "keywords": [
            {
                "keyword": "AI productivity",
                "score": 95,
                "trend": "rising",
                "platforms": ["tiktok", "youtube", "instagram"],
                "engagement_rate": 8.5,
                "competition": "medium",
                "suggested_tags": ["AI", "productivity", "tech", "automation"],
            },
            {
                "keyword": "remote work tips",
                "score": 87,
                "trend": "stable",
                "platforms": ["youtube", "instagram", "linkedin"],
                "engagement_rate": 7.2,
                "competition": "high",
                "suggested_tags": ["remote", "work", "tips", "productivity"],
            },
            {
                "keyword": "crypto trading",
                "score": 76,
                "trend": "declining",
                "platforms": ["tiktok", "youtube"],
                "engagement_rate": 6.8,
                "competition": "very_high",
                "suggested_tags": [
                    "crypto",
                    "trading",
                    "bitcoin",
                    "investment",
                ],
            },
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "data_sources": ["google_trends", "tiktok_api", "youtube_api"],
        "update_frequency": "hourly",
    }


# ================================
# 社交媒體測試數據
# ================================


@pytest.fixture
def social_platforms_data():
    """社交媒體平台數據"""
    return [
        {
            "platform": "tiktok",
            "account_id": "user123",
            "username": "@testuser",
            "connected": True,
            "access_token": "encrypted_token_123",
            "permissions": ["upload", "analytics"],
            "followers": 15420,
            "last_sync": datetime.utcnow().isoformat(),
        },
        {
            "platform": "youtube",
            "channel_id": "UC123456789",
            "channel_name": "Test Channel",
            "connected": True,
            "access_token": "encrypted_youtube_token",
            "permissions": ["upload", "analytics", "manage"],
            "subscribers": 8750,
            "last_sync": datetime.utcnow().isoformat(),
        },
        {
            "platform": "instagram",
            "account_id": "17841234567890",
            "username": "testuser_ig",
            "connected": False,
            "access_token": None,
            "permissions": [],
            "followers": 0,
            "last_sync": None,
        },
    ]


# ================================
# API 回應測試數據
# ================================


@pytest.fixture
def api_success_response():
    """API 成功回應模板"""
    return {
        "success": True,
        "data": {},
        "message": "Operation completed successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }


@pytest.fixture
def api_error_response():
    """API 錯誤回應模板"""
    return {
        "success": False,
        "error": "validation_error",
        "message": "Invalid input data",
        "details": [{"field": "email", "message": "Invalid email format"}],
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }


# ================================
# 檔案上傳測試數據
# ================================


@pytest.fixture
def file_upload_data():
    """檔案上傳測試數據"""
    return {
        "audio_files": [
            {
                "filename": "test_voice.mp3",
                "size": 1024000,  # 1MB
                "duration": 30.5,
                "format": "mp3",
                "sample_rate": 44100,
                "content_type": "audio/mpeg",
            },
            {
                "filename": "test_music.wav",
                "size": 5120000,  # 5MB
                "duration": 60.0,
                "format": "wav",
                "sample_rate": 48000,
                "content_type": "audio/wav",
            },
        ],
        "video_files": [
            {
                "filename": "test_video.mp4",
                "size": 10485760,  # 10MB
                "duration": 30.0,
                "format": "mp4",
                "resolution": "1920x1080",
                "fps": 30,
                "content_type": "video/mp4",
            }
        ],
    }


# ================================
# 數據庫種子數據
# ================================


class TestDataSeeder:
    """測試數據播種器"""

    @staticmethod
    def seed_users(db_session, count: int = 10):
        """播種用戶數據"""
        from services.auth_service.app.models import User

        users = []
        for i in range(count):
            user = User(
                email=f"testuser{i}@example.com",
                username=f"testuser{i}",
                full_name=f"Test User {i}",
                password_hash="hashed_password",
                is_verified=i % 2 == 0,
            )
            users.append(user)
            db_session.add(user)

        db_session.commit()
        return users

    @staticmethod
    def seed_projects(db_session, user_id: str, count: int = 5):
        """播種專案數據"""
        from services.data_service.app.models import VideoProject

        projects = []
        for i in range(count):
            project = VideoProject(
                title=f"Test Project {i}",
                description=f"Description for test project {i}",
                user_id=user_id,
                status="draft" if i % 2 == 0 else "completed",
                settings={
                    "aspect_ratio": "9:16",
                    "duration": 60 + i * 10,
                    "style": "engaging",
                },
            )
            projects.append(project)
            db_session.add(project)

        db_session.commit()
        return projects


# ================================
# 效能測試數據
# ================================


@pytest.fixture
def performance_test_data():
    """效能測試數據"""
    return {
        "concurrent_users": [1, 5, 10, 20, 50, 100],
        "request_patterns": [
            {
                "endpoint": "/api/v1/ai/text/generate-script",
                "method": "POST",
                "payload_size": 500,
                "expected_response_time": 2000,  # ms
            },
            {
                "endpoint": "/api/v1/ai/images/generate",
                "method": "POST",
                "payload_size": 1000,
                "expected_response_time": 5000,  # ms
            },
            {
                "endpoint": "/api/v1/projects",
                "method": "GET",
                "payload_size": 0,
                "expected_response_time": 500,  # ms
            },
        ],
        "stress_test_duration": 300,  # 5 minutes
        "expected_error_rate": 0.01,  # 1%
    }


# ================================
# Mock 數據生成器
# ================================


class MockDataGenerator:
    """Mock 數據生成器"""

    @staticmethod
    def generate_user(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成用戶數據"""
        data = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_verified": True,
            "created_at": datetime.utcnow().isoformat(),
        }

        if overrides:
            data.update(overrides)

        return data

    @staticmethod
    def generate_project(
        user_id: str = None, overrides: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """生成專案數據"""
        data = {
            "id": str(uuid.uuid4()),
            "title": "Test Project",
            "description": "A test project",
            "user_id": user_id or str(uuid.uuid4()),
            "status": "draft",
            "settings": {"aspect_ratio": "9:16", "duration": 60},
            "created_at": datetime.utcnow().isoformat(),
        }

        if overrides:
            data.update(overrides)

        return data

    @staticmethod
    def generate_api_response(
        success: bool = True, data: Any = None
    ) -> Dict[str, Any]:
        """生成 API 回應數據"""
        if success:
            return {
                "success": True,
                "data": data or {},
                "message": "Success",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "success": False,
                "error": "test_error",
                "message": "Test error message",
                "timestamp": datetime.utcnow().isoformat(),
            }
