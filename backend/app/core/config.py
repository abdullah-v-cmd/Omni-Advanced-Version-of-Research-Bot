"""
OmniSynth - Core Configuration
Enterprise-grade settings management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from typing import List, Optional, Union
import secrets
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "OmniSynth"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise AI-Powered Research & Productivity Automation Platform"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "*"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://omnisynth:omnisynth_pass@postgres:5432/omnisynth_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # AI Models - Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL_PRIMARY: str = "llama3-70b-8192"
    GROQ_MODEL_SECONDARY: str = "mixtral-8x7b-32768"
    GROQ_MODEL_FAST: str = "llama3-8b-8192"
    GROQ_MAX_TOKENS: int = 4096
    GROQ_TEMPERATURE: float = 0.7

    # Hugging Face
    HUGGINGFACE_API_KEY: str = ""
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HF_SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"

    # FAISS Vector DB
    FAISS_INDEX_PATH: str = "/app/data/faiss_index"
    FAISS_DIMENSION: int = 384

    # File Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "png", "jpg", "jpeg", "docx", "txt"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    AI_RATE_LIMIT_PER_MINUTE: int = 20

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Email (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Admin
    FIRST_SUPERUSER_EMAIL: str = "admin@omnisynth.ai"
    FIRST_SUPERUSER_PASSWORD: str = "Admin@123456"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v


settings = Settings()
