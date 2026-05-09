"""OmniSynth - Research Schemas (Pydantic)"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.research import SessionStatus, DocumentType, DocumentStatus


class ResearchSessionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None


class ResearchSessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[SessionStatus] = None


class ResearchSessionResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    topic: Optional[str] = None
    status: SessionStatus
    tags: Optional[List[str]] = None
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    doc_type: DocumentType
    status: DocumentStatus
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: str
    is_indexed: bool
    ocr_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DraftCreate(BaseModel):
    title: str
    content: Optional[str] = None
    draft_type: Optional[str] = None
    session_id: Optional[UUID] = None


class DraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    draft_type: Optional[str] = None


class DraftResponse(BaseModel):
    id: UUID
    title: str
    content: Optional[str] = None
    draft_type: Optional[str] = None
    version: int
    word_count: int
    is_ai_generated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CitationCreate(BaseModel):
    style: str
    raw_data: Dict[str, Any]
    session_id: Optional[UUID] = None


class CitationResponse(BaseModel):
    id: UUID
    style: str
    formatted_text: str
    bibtex: Optional[str] = None
    is_validated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AIQueryRequest(BaseModel):
    query: str
    session_id: Optional[UUID] = None
    use_hyde: bool = True
    top_k: int = 5
    stream: bool = False


class AIQueryResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    hyde_document: Optional[str] = None
    model_used: str
    tokens_used: Optional[int] = None


class PlagiarismCheckRequest(BaseModel):
    text: str
    document_id: Optional[UUID] = None


class PlagiarismReportResponse(BaseModel):
    id: UUID
    overall_score: int
    plagiarism_percentage: int
    matches: Optional[List[Dict[str, Any]]] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OCRRequest(BaseModel):
    language: str = "en"
    extract_tables: bool = True


class ContentGenerateRequest(BaseModel):
    content_type: str  # abstract, introduction, literature_review, methodology, conclusion
    topic: str
    context: Optional[str] = None
    session_id: Optional[UUID] = None
    word_limit: int = 500
    academic_style: bool = True


class RecommendationResponse(BaseModel):
    id: UUID
    title: str
    abstract: Optional[str] = None
    authors: Optional[List[str]] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    relevance_score: int
    recommendation_reason: Optional[str] = None

    class Config:
        from_attributes = True
