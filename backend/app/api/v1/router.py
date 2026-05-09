"""
OmniSynth - Main API Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, chat, research, citations, plagiarism,
    analytics, collaboration, admin, ocr
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chat"])
api_router.include_router(research.router, prefix="/research", tags=["Research"])
api_router.include_router(citations.router, prefix="/citations", tags=["Citations"])
api_router.include_router(plagiarism.router, prefix="/plagiarism", tags=["Plagiarism"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(collaboration.router, prefix="/collaboration", tags=["Collaboration"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
