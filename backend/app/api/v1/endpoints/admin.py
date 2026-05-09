"""
OmniSynth - Admin API Endpoints
System administration, user management, monitoring
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.models.research import ResearchSession, Document
from app.models.collaboration import Analytics, ActivityLog, SystemLog
from app.middleware.auth import get_current_superuser
from loguru import logger

router = APIRouter()


class UserUpdateAdmin(BaseModel):
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    query = select(User).order_by(desc(User.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "status": u.status,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "created_at": u.created_at.isoformat(),
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.put("/users/{user_id}")
async def update_user_admin(
    user_id: UUID,
    data: UserUpdateAdmin,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Update user status/role (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_superuser is not None:
        user.is_superuser = data.is_superuser
    if data.role is not None:
        user.role = data.role
    if data.status is not None:
        user.status = data.status

    await db.commit()
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive system statistics."""
    # User stats
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
    
    # Research stats
    total_sessions = (await db.execute(select(func.count(ResearchSession.id)))).scalar() or 0
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar() or 0

    # Recent activity
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= seven_days_ago)
    )).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_last_7_days": recent_users,
        },
        "research": {
            "total_sessions": total_sessions,
            "total_documents": total_documents,
        },
        "system": {
            "version": "1.0.0",
            "environment": "production",
            "uptime": "Online",
        }
    }


@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get system logs (admin only)."""
    query = select(SystemLog).order_by(desc(SystemLog.created_at)).offset(skip).limit(limit)
    if level:
        query = query.where(SystemLog.level == level.upper())
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "level": l.level,
            "message": l.message,
            "module": l.module,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.post("/create-superuser")
async def create_superuser(
    email: str,
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db),
):
    """Create initial superuser (only works if no superusers exist)."""
    existing = (await db.execute(select(func.count(User.id)).where(User.is_superuser == True))).scalar() or 0
    if existing > 0:
        raise HTTPException(status_code=403, detail="Superuser already exists")

    from app.core.security import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        full_name="System Admin",
        hashed_password=get_password_hash(password),
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    return {"message": "Superuser created", "user_id": str(user.id)}
