from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from . import crud, schemas, security
from .database import get_db
from .dependencies import (
    get_current_active_user,
    get_current_superuser,
)
from .config import settings

router = APIRouter()


@router.post(
    "/register",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    if crud.check_user_exists(db, email=user.email, username=user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    return crud.create_user(db=db, user=user)


@router.post("/login", response_model=schemas.Token)
def login_user(
    user_credentials: schemas.UserLogin, db: Session = Depends(get_db)
):
    """Login user and return access token"""
    user = crud.authenticate_user(
        db, user_credentials.email, user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Update last login
    crud.update_last_login(db, user.id)

    # Create access token
    access_token_expires = timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
        "user": user,
    }


@router.get("/me", response_model=schemas.User)
def read_users_me(current_user=Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update current user profile"""
    # Check if email/username is already taken by another user
    if user_update.email and user_update.email != current_user.email:
        if crud.get_user_by_email(db, user_update.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username and user_update.username != current_user.username:
        if crud.get_user_by_username(db, user_update.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    updated_user = crud.update_user(db, current_user.id, user_update)
    return updated_user


@router.post("/change-password")
def change_password(
    password_change: schemas.PasswordChange,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    # Verify current password
    if not security.verify_password(
        password_change.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Update password
    success = crud.update_user_password(
        db, current_user.id, password_change.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return {"message": "Password updated successfully"}


@router.post("/password-reset")
def request_password_reset(
    password_reset: schemas.PasswordReset, db: Session = Depends(get_db)
):
    """Request password reset token"""
    user = crud.get_user_by_email(db, password_reset.email)
    if not user:
        # Don't reveal if email exists or not
        return {
            "message": (
                "If the email exists, a password reset link has been sent"
            )
        }

    reset_token = security.create_password_reset_token(user.email)

    # In production, send this token via email
    # For now, we'll return it (remove this in production)
    return {
        "message": "If the email exists, a password reset link has been sent",
        "reset_token": reset_token,  # Remove this in production
    }


@router.post("/password-reset-confirm")
def confirm_password_reset(
    password_reset_confirm: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Confirm password reset with token"""
    email = security.verify_password_reset_token(password_reset_confirm.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update password
    success = crud.update_user_password(
        db, user.id, password_reset_confirm.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return {"message": "Password reset successfully"}


# Admin endpoints
@router.get("/users", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Get all users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    current_user=Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)"""
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user=Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Delete user (admin only)"""
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"message": "User deleted successfully"}
