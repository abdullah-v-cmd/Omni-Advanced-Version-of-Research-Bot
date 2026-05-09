"""
OmniSynth - Research Sessions API Endpoints
Session management, document processing, AI queries
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
import os
import aiofiles

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.research import ResearchSession, Document, Draft, SessionStatus, DocumentType, DocumentStatus
from app.schemas.research import (
    ResearchSessionCreate, ResearchSessionUpdate, ResearchSessionResponse,
    DocumentResponse, DraftCreate, DraftUpdate, DraftResponse,
    AIQueryRequest, AIQueryResponse, ContentGenerateRequest,
)
from app.middleware.auth import get_current_user
from app.services.ocr_service import ocr_service
from app.services.groq_service import groq_service
from app.services.embedding_service import embedding_service
from app.agents.research_agent import research_agent
from loguru import logger

router = APIRouter()


# ─── Research Sessions ─────────────────────────────────────────────────────────

@router.post("/sessions", response_model=ResearchSessionResponse, status_code=201)
async def create_session(
    data: ResearchSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ResearchSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        topic=data.topic,
        tags=data.tags,
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=List[ResearchSessionResponse])
async def list_sessions(
    status: Optional[SessionStatus] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ResearchSession).where(ResearchSession.user_id == current_user.id)
    if status:
        query = query.where(ResearchSession.status == status)
    query = query.order_by(desc(ResearchSession.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=ResearchSessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id, ResearchSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}", response_model=ResearchSessionResponse)
async def update_session(
    session_id: UUID,
    data: ResearchSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id, ResearchSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    for field, value in data.dict(exclude_none=True).items():
        setattr(session, field, value)
    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id, ResearchSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}


# ─── Document Upload & Processing ─────────────────────────────────────────────

@router.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    language: str = Form("en"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a document (PDF, image, DOCX, TXT)."""
    # Validate file type
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")

    # Determine doc type
    doc_type_map = {"pdf": DocumentType.PDF, "png": DocumentType.IMAGE, "jpg": DocumentType.IMAGE,
                    "jpeg": DocumentType.IMAGE, "docx": DocumentType.DOCX, "txt": DocumentType.TXT}
    doc_type = doc_type_map.get(ext, DocumentType.TXT)

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{ext}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Create document record
    doc = Document(
        id=uuid.uuid4(),
        user_id=current_user.id,
        session_id=uuid.UUID(session_id) if session_id else None,
        title=file.filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        doc_type=doc_type,
        status=DocumentStatus.PROCESSING,
        language=language,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Process in background
    background_tasks.add_task(process_document_background, str(doc.id), file_path, doc_type.value, language)

    return {
        "id": str(doc.id),
        "title": doc.title,
        "status": doc.status,
        "message": "Document uploaded. Processing in background.",
    }


async def process_document_background(doc_id: str, file_path: str, doc_type: str, language: str):
    """Background task to process uploaded document."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            # Extract text
            ocr_result = await ocr_service.process_document(file_path, doc_type, language)
            text = ocr_result.get("text", "")

            # Extract metadata
            structured = await ocr_service.extract_structured_data(text)

            # Generate summary
            summary = ""
            if text and len(text) > 100:
                summary = await groq_service.summarize_text(text[:3000])

            # Extract keywords
            keywords = []
            if text:
                keywords = await groq_service.extract_keywords(text[:2000])

            # Add to vector store
            if text:
                await embedding_service.initialize()
                await embedding_service.add_document(
                    doc_id=str(doc.id),
                    text=text[:5000],
                    metadata={"title": doc.title, "doc_type": doc_type, "user_id": str(doc.user_id)},
                )

            doc.extracted_text = text[:10000]
            doc.summary = summary
            doc.keywords = keywords
            doc.word_count = structured.get("word_count", 0)
            doc.page_count = ocr_result.get("pages", 1)
            doc.status = DocumentStatus.INDEXED
            doc.is_indexed = True
            doc.ocr_completed = True
            await db.commit()
            logger.info(f"Document {doc_id} processed successfully")
        except Exception as e:
            logger.error(f"Document processing failed for {doc_id}: {e}")
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = DocumentStatus.FAILED
                await db.commit()


@router.get("/documents")
async def list_documents(
    session_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(Document.user_id == current_user.id)
    if session_id:
        query = query.where(Document.session_id == session_id)
    query = query.order_by(desc(Document.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "doc_type": d.doc_type,
            "status": d.status,
            "summary": d.summary,
            "keywords": d.keywords,
            "word_count": d.word_count,
            "page_count": d.page_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id),
        "title": doc.title,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "extracted_text": doc.extracted_text,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "word_count": doc.word_count,
        "page_count": doc.page_count,
        "language": doc.language,
        "created_at": doc.created_at.isoformat(),
    }


# ─── AI Research Queries ─────────────────────────────────────────────────────

@router.post("/query")
async def research_query(
    request: AIQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute an AI research query with HyDE-enhanced RAG."""
    result = await research_agent.answer_research_query(
        query=request.query,
        use_hyde=request.use_hyde,
    )
    return {
        "query": request.query,
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "hyde_document": result.get("hyde_document"),
        "model_used": result.get("model_used", ""),
    }


@router.post("/generate-content")
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate academic content using AI."""
    content = await groq_service.generate_content(
        content_type=request.content_type,
        topic=request.topic,
        context=request.context or "",
        word_limit=request.word_limit,
    )

    # Save as draft if session_id provided
    draft = None
    if request.session_id:
        draft = Draft(
            id=uuid.uuid4(),
            user_id=current_user.id,
            session_id=request.session_id,
            title=f"AI-generated {request.content_type}: {request.topic[:50]}",
            content=content,
            draft_type=request.content_type,
            is_ai_generated=True,
            ai_prompt=request.topic,
            word_count=len(content.split()),
        )
        db.add(draft)
        await db.commit()
        await db.refresh(draft)

    return {
        "content": content,
        "content_type": request.content_type,
        "topic": request.topic,
        "word_count": len(content.split()),
        "draft_id": str(draft.id) if draft else None,
    }


# ─── Drafts ──────────────────────────────────────────────────────────────────

@router.post("/drafts", status_code=201)
async def create_draft(
    data: DraftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    draft = Draft(
        id=uuid.uuid4(),
        user_id=current_user.id,
        session_id=data.session_id,
        title=data.title,
        content=data.content,
        draft_type=data.draft_type,
        word_count=len(data.content.split()) if data.content else 0,
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return {"id": str(draft.id), "title": draft.title, "created_at": draft.created_at.isoformat()}


@router.get("/drafts")
async def list_drafts(
    session_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Draft).where(Draft.user_id == current_user.id)
    if session_id:
        query = query.where(Draft.session_id == session_id)
    query = query.order_by(desc(Draft.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    drafts = result.scalars().all()
    return [
        {"id": str(d.id), "title": d.title, "draft_type": d.draft_type, "word_count": d.word_count, "created_at": d.created_at.isoformat()}
        for d in drafts
    ]


@router.put("/drafts/{draft_id}")
async def update_draft(
    draft_id: UUID,
    data: DraftUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    for field, value in data.dict(exclude_none=True).items():
        setattr(draft, field, value)
    if data.content:
        draft.word_count = len(data.content.split())
    await db.commit()
    await db.refresh(draft)
    return {"id": str(draft.id), "title": draft.title, "updated_at": draft.updated_at.isoformat() if draft.updated_at else None}
