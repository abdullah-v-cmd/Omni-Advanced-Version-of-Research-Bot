"""OmniSynth - Schemas Package"""
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, Token, TokenRefresh,
    UserProfileUpdate, UserProfileResponse, PasswordChange
)
from app.schemas.research import (
    ResearchSessionCreate, ResearchSessionUpdate, ResearchSessionResponse,
    DocumentResponse, DraftCreate, DraftUpdate, DraftResponse,
    CitationCreate, CitationResponse, AIQueryRequest, AIQueryResponse,
    PlagiarismCheckRequest, PlagiarismReportResponse,
    OCRRequest, ContentGenerateRequest, RecommendationResponse
)

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "Token", "TokenRefresh",
    "UserProfileUpdate", "UserProfileResponse", "PasswordChange",
    "ResearchSessionCreate", "ResearchSessionUpdate", "ResearchSessionResponse",
    "DocumentResponse", "DraftCreate", "DraftUpdate", "DraftResponse",
    "CitationCreate", "CitationResponse", "AIQueryRequest", "AIQueryResponse",
    "PlagiarismCheckRequest", "PlagiarismReportResponse",
    "OCRRequest", "ContentGenerateRequest", "RecommendationResponse",
]
