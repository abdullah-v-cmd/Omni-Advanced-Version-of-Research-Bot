"""OmniSynth - User Schemas (Pydantic)"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @validator("username")
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username must be alphanumeric")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileUpdate(BaseModel):
    bio: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    research_interests: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    orcid_id: Optional[str] = None
    google_scholar_id: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: UUID
    bio: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    research_interests: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    orcid_id: Optional[str] = None
    total_research_hours: int = 0
    total_documents: int = 0
    total_citations: int = 0

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str] = None
    role: UserRole
    status: UserStatus
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
