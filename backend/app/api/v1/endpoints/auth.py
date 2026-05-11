"""
OmniSynth - Authentication API Endpoints
Register, Login, Token Refresh, Profile Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from datetime import datetime
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.models.user import User, UserProfile, UserRole, UserStatus
from app.schemas.user import UserCreate, UserLogin, TokenRefresh, UserUpdate, UserProfileUpdate, PasswordChange
from app.middleware.auth import get_current_user
from loguru import logger
import uuid

router = APIRouter()


def _user_to_dict(user):
    """Convert User ORM object to plain dict — avoids any lazy-load / greenlet issues."""
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "status": user.status,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "profile": None,
    }


# ─── Register ─────────────────────────────────────────────────────────────────
@router.post("/register", status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user_id = uuid.uuid4()
    now = datetime.utcnow()

    # Use raw INSERT to avoid ORM tracking / greenlet issues
    await db.execute(
        insert(User).values(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=UserRole.RESEARCHER,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_superuser=False,
            is_verified=False,
            avatar_url=None,
            created_at=now,
            updated_at=now,
            last_login=None,
        )
    )

    # Create user profile
    await db.execute(
        insert(UserProfile).values(
            id=uuid.uuid4(),
            user_id=user_id,
            total_research_hours=0,
            total_documents=0,
            total_citations=0,
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()

    logger.info(f"New user registered: {user_data.email}")
    return {
        "id": str(user_id),
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "role": UserRole.RESEARCHER,
        "status": UserStatus.ACTIVE,
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "avatar_url": None,
        "created_at": now.isoformat(),
        "last_login": None,
        "profile": None,
    }


# ─── Login ────────────────────────────────────────────────────────────────────
@router.post("/login")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")

    now = datetime.utcnow()

    # Use raw UPDATE — avoids ORM attribute tracking & greenlet issues
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=now, updated_at=now)
    )
    await db.commit()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    logger.info(f"User logged in: {user.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_to_dict(user),
    }


# ─── Refresh token ────────────────────────────────────────────────────────────
@router.post("/refresh")
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    user_id = verify_token(token_data.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(str(user.id))
    refresh_token_new = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_new,
        "token_type": "bearer",
        "user": _user_to_dict(user),
    }


# ─── Get current user ─────────────────────────────────────────────────────────
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return _user_to_dict(current_user)


# ─── Update current user ──────────────────────────────────────────────────────
@router.put("/me")
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's information."""
    values = {"updated_at": datetime.utcnow()}
    if user_data.full_name is not None:
        values["full_name"] = user_data.full_name
    if user_data.avatar_url is not None:
        values["avatar_url"] = user_data.avatar_url

    await db.execute(update(User).where(User.id == current_user.id).values(**values))
    await db.commit()

    # Re-fetch to get updated record
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    return _user_to_dict(user) if user else _user_to_dict(current_user)


# ─── Update profile ───────────────────────────────────────────────────────────
@router.put("/me/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile details."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    now = datetime.utcnow()

    dump = profile_data.model_dump(exclude_none=True)
    dump["updated_at"] = now

    if not profile:
        dump["id"] = uuid.uuid4()
        dump["user_id"] = current_user.id
        dump["created_at"] = now
        dump["total_research_hours"] = 0
        dump["total_documents"] = 0
        dump["total_citations"] = 0
        await db.execute(insert(UserProfile).values(**dump))
    else:
        await db.execute(
            update(UserProfile).where(UserProfile.user_id == current_user.id).values(**dump)
        )

    await db.commit()
    return {"message": "Profile updated successfully"}


# ─── Change password ──────────────────────────────────────────────────────────
@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(hashed_password=get_password_hash(password_data.new_password),
                updated_at=datetime.utcnow())
    )
    await db.commit()
    return {"message": "Password changed successfully"}


# ─── Logout ───────────────────────────────────────────────────────────────────
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard tokens)."""
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}
