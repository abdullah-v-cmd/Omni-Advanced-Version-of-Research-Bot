"""
OmniSynth - Main FastAPI Application Entry Point
Enterprise-grade AI Research Platform
"""
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Create local log directory (not /app/logs which requires Docker)
_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(_log_dir, exist_ok=True)
logger.add(
    os.path.join(_log_dir, "omnisynth.log"),
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
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    try:
        from app.core.database import AsyncSessionLocal
        from app.models.research import Document, DocumentStatus
        from sqlalchemy import select as sa_select
        async with AsyncSessionLocal() as rebuild_db:
            result = await rebuild_db.execute(
                sa_select(Document).where(
                    Document.extracted_text.isnot(None),
                    Document.is_indexed == True
                )   
            )
            documents = result.scalars().all()
            if documents:
                await embedding_service.initialize()
                for doc in documents:
                    if doc.extracted_text:
                        await embedding_service.add_document(
                            doc_id=str(doc.id),
                            text=doc.extracted_text[:5000],
                            metadata={
                                "title": doc.title,
                                "doc_type": str(doc.doc_type),
                                "user_id": str(doc.user_id)
                                },
                        )
                logger.info(f"✅ FAISS rebuilt with {len(documents)} documents")
            else:
                logger.info("ℹ️ No documents to reindex")
    except Exception as e:
        logger.warning(f"⚠️ FAISS rebuild failed: {e}")

    
    # Initialize Redis (optional - won't crash if unavailable)
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
    allow_origins=[
        "https://frontend-production-c81a.up.railway.app",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers + timing middleware
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
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/auth",
            "chat": f"{settings.API_V1_STR}/chat",
            "research": f"{settings.API_V1_STR}/research",
            "citations": f"{settings.API_V1_STR}/citations",
            "plagiarism": f"{settings.API_V1_STR}/plagiarism",
            "analytics": f"{settings.API_V1_STR}/analytics",
            "collaboration": f"{settings.API_V1_STR}/collaboration",
            "admin": f"{settings.API_V1_STR}/admin",
            "ocr": f"{settings.API_V1_STR}/ocr",
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    checks = {"api": "healthy", "version": settings.APP_VERSION}

    # Check Redis
    try:
        if redis_client.client:
            await redis_client.client.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "unavailable"
    except Exception:
        checks["redis"] = "unavailable"

    # Check Groq
    checks["groq"] = "configured" if groq_service.client else "not_configured"

    return {
        "status": "healthy",
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
