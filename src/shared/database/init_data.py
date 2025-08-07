#!/usr/bin/env python3
"""
資料庫初始化和測試數據
"""

import asyncio
from datetime import datetime
from pathlib import Path
import sys

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.database.connection import create_tables_sync, get_db
from src.shared.database.models import User, Video, VideoStatus, ProcessingTask, TaskStatus, UserRole
from src.shared.security import get_password_hash


def create_test_users(db):
    """創建測試用戶"""
    
    test_users = [
        {
            "username": "testuser1",
            "email": "test1@example.com",
            "full_name": "Test User One",
            "password": "password123"
        },
        {
            "username": "testuser2", 
            "email": "test2@example.com",
            "full_name": "Test User Two",
            "password": "password123"
        },
        {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password": "admin123",
            "role": UserRole.ADMIN
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        # 檢查用戶是否已存在
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping...")
            created_users.append(existing_user)
            continue
        
        # 創建新用戶
        hashed_password = get_password_hash(user_data["password"])
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=hashed_password,
            role=user_data.get("role", UserRole.USER),
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        created_users.append(user)
        print(f"Created user: {user.email}")
    
    db.commit()
    
    # 刷新用戶對象以獲取生成的ID
    for user in created_users:
        db.refresh(user)
    
    return created_users


def create_test_videos(db, users):
    """創建測試影片項目"""
    
    test_videos = [
        {
            "title": "AI技術介紹",
            "description": "人工智能技術的基本介紹和應用",
            "topic": "人工智能",
            "style": "educational",
            "platform": "youtube",
            "language": "zh-TW",
            "status": VideoStatus.COMPLETED,
            "progress_percentage": 100.0
        },
        {
            "title": "短影片製作技巧",
            "description": "如何製作吸引人的短影片內容",
            "topic": "短影片製作",
            "style": "entertaining",
            "platform": "tiktok",
            "language": "zh-TW",
            "status": VideoStatus.GENERATING_SCRIPT,
            "progress_percentage": 65.0
        },
        {
            "title": "科技趨勢分析",
            "description": "2024年最新科技趨勢分析",
            "topic": "科技趨勢",
            "style": "analytical",
            "platform": "youtube",
            "language": "zh-TW",
            "status": VideoStatus.PENDING,
            "progress_percentage": 0.0
        }
    ]
    
    created_videos = []
    
    for i, video_data in enumerate(test_videos):
        # 使用不同的用戶
        user = users[i % len(users)]
        
        # 檢查影片是否已存在
        existing_video = db.query(Video).filter(
            Video.title == video_data["title"],
            Video.user_id == user.id
        ).first()
        
        if existing_video:
            print(f"Video '{video_data['title']}' already exists for user {user.email}, skipping...")
            created_videos.append(existing_video)
            continue
        
        # 創建新影片
        video = Video(
            user_id=user.id,
            title=video_data["title"],
            description=video_data["description"],
            topic=video_data["topic"],
            style=video_data["style"],
            platform=video_data["platform"],
            language=video_data["language"],
            status=video_data["status"],
            progress_percentage=video_data["progress_percentage"],
            duration_seconds=60,  # 預設60秒
        )
        
        # 如果是完成的影片，添加一些範例URL
        if video_data["status"] == VideoStatus.COMPLETED:
            video.thumbnail_url = f"https://example.com/thumbnails/{i+1}.jpg"
            video.final_video_url = f"https://example.com/videos/{i+1}.mp4"
            video.completed_at = datetime.utcnow()
        
        db.add(video)
        created_videos.append(video)
        print(f"Created video: {video.title} for user {user.email}")
    
    db.commit()
    
    # 刷新影片對象以獲取生成的ID
    for video in created_videos:
        db.refresh(video)
    
    return created_videos


def create_test_processing_tasks(db, videos):
    """創建測試處理任務"""
    
    test_tasks = [
        {
            "task_type": "script_generation",
            "task_name": "生成影片腳本",
            "status": TaskStatus.SUCCESS
        },
        {
            "task_type": "voice_synthesis",
            "task_name": "語音合成",
            "status": TaskStatus.SUCCESS
        },
        {
            "task_type": "image_generation",
            "task_name": "圖像生成",
            "status": TaskStatus.RUNNING
        },
        {
            "task_type": "video_composition",
            "task_name": "影片合成",
            "status": TaskStatus.QUEUED
        }
    ]
    
    created_tasks = []
    
    for video in videos:
        for i, task_data in enumerate(test_tasks):
            # 為每個影片創建不同數量的任務
            if video.status == VideoStatus.COMPLETED and i < 2:
                # 完成的影片有完成的任務
                task = ProcessingTask(
                    video_id=video.id,
                    user_id=video.user_id,
                    task_type=task_data["task_type"],
                    task_name=task_data["task_name"],
                    status=TaskStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
            elif video.status == VideoStatus.GENERATING_SCRIPT and i < 3:
                # 處理中的影片有各種狀態的任務
                task = ProcessingTask(
                    video_id=video.id,
                    user_id=video.user_id,
                    task_type=task_data["task_type"],
                    task_name=task_data["task_name"],
                    status=task_data["status"],
                    started_at=datetime.utcnow() if task_data["status"] != TaskStatus.QUEUED else None,
                    completed_at=datetime.utcnow() if task_data["status"] == TaskStatus.SUCCESS else None
                )
            elif video.status == VideoStatus.PENDING and i < 1:
                # 待處理的影片只有一個待處理任務
                task = ProcessingTask(
                    video_id=video.id,
                    user_id=video.user_id,
                    task_type="initialization",
                    task_name="初始化影片項目",
                    status=TaskStatus.QUEUED
                )
            else:
                continue
            
            db.add(task)
            created_tasks.append(task)
    
    db.commit()
    
    print(f"Created {len(created_tasks)} processing tasks")
    return created_tasks


def init_database():
    """初始化資料庫"""
    
    print("🗄️ Initializing database...")
    
    # 創建表格
    print("Creating database tables...")
    create_tables_sync()
    print("✅ Database tables created")
    
    # 獲取資料庫會話
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 創建測試用戶
        print("\n👥 Creating test users...")
        users = create_test_users(db)
        print(f"✅ Created {len(users)} users")
        
        # 創建測試影片
        print("\n🎬 Creating test videos...")
        videos = create_test_videos(db, users)
        print(f"✅ Created {len(videos)} videos")
        
        # 創建處理任務
        print("\n⚙️ Creating test processing tasks...")
        tasks = create_test_processing_tasks(db, videos)
        print(f"✅ Created {len(tasks)} processing tasks")
        
        print("\n🎉 Database initialization completed!")
        
        # 打印總結
        print("\n📊 Database Summary:")
        print(f"   - Users: {db.query(User).count()}")
        print(f"   - Videos: {db.query(Video).count()}")
        print(f"   - Processing Tasks: {db.query(ProcessingTask).count()}")
        
        print("\n🔑 Test Login Credentials:")
        for user in users:
            password = "password123" if user.role == UserRole.USER else "admin123"
            print(f"   - {user.email} / {password}")
            
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()