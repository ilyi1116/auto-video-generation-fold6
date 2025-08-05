from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import PlatformAccount, ScheduledPost
from ..schemas import (
    PlatformAccountRequest,
    PlatformAccountResponse,
    PlatformType,
    PostStatus,
    ScheduleListResponse,
    SchedulePostRequest,
    SchedulePostResponse,
    UpdateScheduleRequest,
)
from ..tasks import publish_post

router = APIRouter()


@router.post("/posts", response_model=SchedulePostResponse)
async def schedule_post(
    request: SchedulePostRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """排程發布貼文"""

    # 檢查排程時間是否為未來時間
    if request.scheduled_time <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")

    # 檢查平台帳號是否存在
    if request.platform_account_id:
        platform_account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.id == request.platform_account_id,
                PlatformAccount.user_id == current_user["user_id"],
                PlatformAccount.platform == request.platform,
                PlatformAccount.is_active is True,
            )
            .first()
        )

        if not platform_account:
            raise HTTPException(status_code=404, detail="Platform account not found")

    # 建立排程記錄
    scheduled_post = ScheduledPost(
        user_id=current_user["user_id"],
        video_id=request.video_id,
        platform=request.platform,
        platform_account_id=request.platform_account_id,
        scheduled_time=request.scheduled_time,
        title=request.title,
        description=request.description,
        tags=request.tags,
        platform_settings=request.platform_settings,
    )

    db.add(scheduled_post)
    db.commit()
    db.refresh(scheduled_post)

    return scheduled_post


@router.get("/posts", response_model=ScheduleListResponse)
async def get_scheduled_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[PostStatus] = None,
    platform: Optional[PlatformType] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取排程列表"""

    query = db.query(ScheduledPost).filter(ScheduledPost.user_id == current_user["user_id"])

    if status:
        query = query.filter(ScheduledPost.status == status)

    if platform:
        query = query.filter(ScheduledPost.platform == platform)

    total = query.count()

    posts = (
        query.order_by(ScheduledPost.scheduled_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ScheduleListResponse(total=total, items=posts, page=page, page_size=page_size)


@router.get("/posts/{post_id}", response_model=SchedulePostResponse)
async def get_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取單一排程貼文"""

    post = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user["user_id"],
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    return post


@router.put("/posts/{post_id}", response_model=SchedulePostResponse)
async def update_scheduled_post(
    post_id: int,
    request: UpdateScheduleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """更新排程貼文"""

    post = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user["user_id"],
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot update non-pending post")

    # 更新欄位
    if request.scheduled_time is not None:
        if request.scheduled_time <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future")
        post.scheduled_time = request.scheduled_time

    if request.title is not None:
        post.title = request.title

    if request.description is not None:
        post.description = request.description

    if request.tags is not None:
        post.tags = request.tags

    if request.platform_settings is not None:
        post.platform_settings = request.platform_settings

    db.commit()
    db.refresh(post)

    return post


@router.delete("/posts/{post_id}")
async def cancel_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """取消排程貼文"""

    post = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user["user_id"],
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot cancel non-pending post")

    post.status = "cancelled"
    db.commit()

    return {"message": "Scheduled post cancelled successfully"}


@router.post("/posts/{post_id}/publish")
async def publish_now(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """立即發布排程貼文"""

    post = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user["user_id"],
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot publish non-pending post")

    # 觸發發布任務
    publish_post.delay(post_id)

    return {"message": "Publish task triggered successfully"}


# 平台帳號管理
@router.post("/accounts", response_model=PlatformAccountResponse)
async def connect_platform_account(
    request: PlatformAccountRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """連接平台帳號"""

    # 檢查是否已存在相同平台帳號
    existing_account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.user_id == current_user["user_id"],
            PlatformAccount.platform == request.platform,
            PlatformAccount.platform_user_id == request.platform_user_id,
        )
        .first()
    )

    if existing_account:
        # 更新現有帳號
        existing_account.access_token = request.access_token
        existing_account.refresh_token = request.refresh_token
        existing_account.token_expires_at = request.token_expires_at
        existing_account.platform_username = request.platform_username
        existing_account.is_active = True
        existing_account.is_connected = True

        db.commit()
        db.refresh(existing_account)
        return existing_account
    else:
        # 建立新帳號
        platform_account = PlatformAccount(
            user_id=current_user["user_id"],
            platform=request.platform,
            platform_user_id=request.platform_user_id,
            platform_username=request.platform_username,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            token_expires_at=request.token_expires_at,
        )

        db.add(platform_account)
        db.commit()
        db.refresh(platform_account)
        return platform_account


@router.get("/accounts", response_model=List[PlatformAccountResponse])
async def get_platform_accounts(
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token)
):
    """獲取用戶的平台帳號列表"""

    accounts = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.user_id == current_user["user_id"],
            PlatformAccount.is_active is True,
        )
        .all()
    )

    return accounts


@router.delete("/accounts/{account_id}")
async def disconnect_platform_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """斷開平台帳號連接"""

    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.id == account_id,
            PlatformAccount.user_id == current_user["user_id"],
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Platform account not found")

    account.is_active = False
    account.is_connected = False
    db.commit()

    return {"message": "Platform account disconnected successfully"}
