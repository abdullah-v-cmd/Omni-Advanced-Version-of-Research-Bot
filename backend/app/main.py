"""
OmniSynth - Main FastAPI Application Entry Point
Enterprise-grade AI Research Platform
"""
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import redis_client
from app.services.groq_service import groq_service
from app.services.embedding_service import embedding_service
from app.api.v1.router import api_router

# ─── Logging Configuration ─────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)
logger.add(
    "/app/logs/omnisynth.log",
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
)

# ─── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── Application Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    logger.info("🚀 Starting OmniSynth AI Research Platform...")

    # Create required directories
    os.makedirs("/app/logs", exist_ok=True)
    os.makedirs("/app/uploads", exist_ok=True)
    os.makedirs("/app/data/faiss_index", exist_ok=True)

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    # Initialize Redis
    try:
        await redis_client.connect()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed (non-critical): {e}")

    # Initialize Groq service
    try:
        groq_service.initialize()
        logger.info("✅ Groq AI service initialized")
    except Exception as e:
        logger.warning(f"⚠️ Groq service initialization: {e}")

    # Initialize embedding service (lazy - loads on first use)
    logger.info("✅ OmniSynth platform ready!")
    logger.info(f"📖 API docs: http://localhost:8000/docs")

    yield  # Application runs here

    # Cleanup
    logger.info("🛑 Shutting down OmniSynth...")
    try:
        await close_db()
        await redis_client.disconnect()
        await embedding_service.save_index()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    logger.info("👋 OmniSynth shut down complete")


# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"← {request.method} {request.url.path} [{response.status_code}]")
    return response


# ─── Global Exception Handlers ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Resource not found: {request.url.path}"},
    )


# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "status": "operational",
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    checks = {"api": "healthy", "version": settings.APP_VERSION}

    # Check Redis
    try:
        await redis_client.client.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unavailable"

    overall = "healthy" if all(v in ["healthy", "unavailable"] for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "checks": checks,
        "timestamp": time.time(),
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Basic metrics endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
