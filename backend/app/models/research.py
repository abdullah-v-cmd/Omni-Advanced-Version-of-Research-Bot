"""
OmniSynth - Research Models
SQLAlchemy ORM models for research sessions, documents, sources
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum, ForeignKey, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"
    DOCX = "docx"
    TXT = "txt"
    URL = "url"


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(500), nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    tags = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    auto_saved_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="research_sessions")
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="session", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="session", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    doc_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING)
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    language = Column(String(50), default="en")
    faiss_index_id = Column(String(255), nullable=True)
    is_indexed = Column(Boolean, default=False)
    ocr_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    session = relationship("ResearchSession", back_populates="documents")
    plagiarism_reports = relationship("PlagiarismReport", back_populates="document", cascade="all, delete-orphan")


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    draft_type = Column(String(100), nullable=True)  # abstract, intro, literature_review, etc.
    version = Column(Integer, default=1)
    word_count = Column(Integer, default=0)
    is_ai_generated = Column(Boolean, default=False)
    ai_prompt = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="drafts")
    session = relationship("ResearchSession", back_populates="drafts")


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(1000), nullable=False)
    authors = Column(JSON, nullable=True)
    abstract = Column(Text, nullable=True)
    url = Column(String(2000), nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    isbn = Column(String(50), nullable=True)
    journal = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    volume = Column(String(50), nullable=True)
    issue = Column(String(50), nullable=True)
    pages = Column(String(100), nullable=True)
    publisher = Column(String(500), nullable=True)
    source_type = Column(String(100), nullable=True)  # journal, book, conference, etc.
    keywords = Column(JSON, nullable=True)
    citations_count = Column(Integer, default=0)
    embedding_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="SET NULL"), nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    style = Column(String(50), nullable=False)  # APA, MLA, IEEE, Chicago, Harvard
    formatted_text = Column(Text, nullable=False)
    bibtex = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    is_validated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="citations")
    session = relationship("ResearchSession", back_populates="citations")
