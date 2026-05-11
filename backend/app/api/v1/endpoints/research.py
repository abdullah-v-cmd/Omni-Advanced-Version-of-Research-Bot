"""
OmniSynth - Research Sessions API Endpoints
Session management, document processing, AI queries
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, insert, update
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
    ResearchSessionCreate, ResearchSessionUpdate,
    DraftCreate, DraftUpdate,
    AIQueryRequest, ContentGenerateRequest,
)
from app.middleware.auth import get_current_user
from app.services.ocr_service import ocr_service
from app.services.groq_service import groq_service
from app.services.embedding_service import embedding_service
from app.agents.research_agent import research_agent
from loguru import logger

router = APIRouter()


def _session_to_dict(s):
    return {
        "id": str(s.id),
        "user_id": str(s.user_id),
        "title": s.title,
        "description": s.description,
        "topic": s.topic,
        "status": s.status,
        "tags": s.tags,
        "is_public": s.is_public,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _doc_to_dict(d):
    return {
        "id": str(d.id),
        "title": d.title,
        "doc_type": d.doc_type,
        "status": d.status,
        "summary": d.summary,
        "keywords": d.keywords,
        "word_count": d.word_count,
        "page_count": d.page_count,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _draft_to_dict(d):
    return {
        "id": str(d.id),
        "title": d.title,
        "draft_type": d.draft_type,
        "word_count": d.word_count,
        "is_ai_generated": d.is_ai_generated,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


# ─── Research Sessions ─────────────────────────────────────────────────────────

@router.post("/sessions", status_code=201)
async def create_session(
    data: ResearchSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session_id = uuid.uuid4()
    now = datetime.utcnow()
    await db.execute(
        insert(ResearchSession).values(
            id=session_id,
            user_id=current_user.id,
            title=data.title,
            description=data.description,
            topic=data.topic,
            tags=data.tags or [],
            status=SessionStatus.ACTIVE,
            is_public=False,
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()
    return {
        "id": str(session_id),
        "user_id": str(current_user.id),
        "title": data.title,
        "description": data.description,
        "topic": data.topic,
        "status": SessionStatus.ACTIVE,
        "tags": data.tags or [],
        "is_public": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


@router.get("/sessions")
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
    return [_session_to_dict(s) for s in result.scalars().all()]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_dict(session)


@router.put("/sessions/{session_id}")
async def update_session(
    session_id: UUID,
    data: ResearchSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Raw UPDATE — avoid ORM attribute tracking / greenlet issues
    values = data.model_dump(exclude_none=True)
    values["updated_at"] = datetime.utcnow()
    await db.execute(
        update(ResearchSession)
        .where(ResearchSession.id == session_id)
        .values(**values)
    )
    await db.commit()

    # Re-fetch updated record
    result2 = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    updated = result2.scalar_one_or_none()
    return _session_to_dict(updated) if updated else _session_to_dict(session)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == current_user.id,
        )
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
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")

    doc_type_map = {
        "pdf": DocumentType.PDF, "png": DocumentType.IMAGE, "jpg": DocumentType.IMAGE,
        "jpeg": DocumentType.IMAGE, "docx": DocumentType.DOCX, "txt": DocumentType.TXT,
    }
    doc_type = doc_type_map.get(ext, DocumentType.TXT)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{ext}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    doc_id = uuid.uuid4()
    session_uuid = uuid.UUID(session_id) if session_id else None
    now = datetime.utcnow()

    await db.execute(
        insert(Document).values(
            id=doc_id,
            user_id=current_user.id,
            session_id=session_uuid,
            title=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            doc_type=doc_type,
            status=DocumentStatus.PROCESSING,
            language=language,
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()

    background_tasks.add_task(
        process_document_background, str(doc_id), file_path, doc_type.value, language
    )

    return {
        "id": str(doc_id),
        "title": file.filename,
        "status": "processing",
        "message": "Document uploaded. Processing in background.",
    }


async def process_document_background(doc_id: str, file_path: str, doc_type: str, language: str):
    """Background task to process uploaded document — uses raw UPDATE to avoid greenlet issues."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            ocr_result = await ocr_service.process_document(file_path, doc_type, language)
            text = ocr_result.get("text", "")
            structured = await ocr_service.extract_structured_data(text)

            summary = ""
            if text and len(text) > 100:
                summary = await groq_service.summarize_text(text[:3000])

            keywords = []
            if text:
                keywords = await groq_service.extract_keywords(text[:2000])

            if text:
                await embedding_service.initialize()
                await embedding_service.add_document(
                    doc_id=str(doc.id),
                    text=text[:5000],
                    metadata={"title": doc.title, "doc_type": doc_type, "user_id": str(doc.user_id)},
                )

            # Raw UPDATE — no ORM attribute mutation
            await db.execute(
                update(Document)
                .where(Document.id == uuid.UUID(doc_id))
                .values(
                    extracted_text=text[:10000],
                    summary=summary,
                    keywords=keywords,
                    word_count=structured.get("word_count", 0),
                    page_count=ocr_result.get("pages", 1),
                    status=DocumentStatus.INDEXED,
                    is_indexed=True,
                    ocr_completed=True,
                    updated_at=datetime.utcnow(),
                )
            )
            await db.commit()
            logger.info(f"Document {doc_id} processed successfully")
        except Exception as e:
            logger.error(f"Document processing failed for {doc_id}: {e}")
            await db.execute(
                update(Document)
                .where(Document.id == uuid.UUID(doc_id))
                .values(status=DocumentStatus.FAILED, updated_at=datetime.utcnow())
            )
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
    return [_doc_to_dict(d) for d in result.scalars().all()]


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
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
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

    draft_id = None
    if request.session_id:
        new_draft_id = uuid.uuid4()
        now = datetime.utcnow()
        await db.execute(
            insert(Draft).values(
                id=new_draft_id,
                user_id=current_user.id,
                session_id=request.session_id,
                title=f"AI-generated {request.content_type}: {request.topic[:50]}",
                content=content,
                draft_type=request.content_type,
                is_ai_generated=True,
                ai_prompt=request.topic,
                word_count=len(content.split()),
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()
        draft_id = str(new_draft_id)

    return {
        "content": content,
        "content_type": request.content_type,
        "topic": request.topic,
        "word_count": len(content.split()),
        "draft_id": draft_id,
    }


# ─── Drafts ──────────────────────────────────────────────────────────────────

@router.post("/drafts", status_code=201)
async def create_draft(
    data: DraftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    draft_id = uuid.uuid4()
    now = datetime.utcnow()
    await db.execute(
        insert(Draft).values(
            id=draft_id,
            user_id=current_user.id,
            session_id=data.session_id,
            title=data.title,
            content=data.content,
            draft_type=data.draft_type,
            word_count=len(data.content.split()) if data.content else 0,
            is_ai_generated=False,
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()
    return {
        "id": str(draft_id),
        "title": data.title,
        "draft_type": data.draft_type,
        "word_count": len(data.content.split()) if data.content else 0,
        "is_ai_generated": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


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
    return [_draft_to_dict(d) for d in result.scalars().all()]


@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {
        "id": str(draft.id),
        "title": draft.title,
        "content": draft.content,
        "draft_type": draft.draft_type,
        "word_count": draft.word_count,
        "is_ai_generated": draft.is_ai_generated,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
        "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
    }


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

    values = data.model_dump(exclude_none=True)
    if "content" in values:
        values["word_count"] = len(values["content"].split())
    values["updated_at"] = datetime.utcnow()

    # Raw UPDATE — avoid ORM attribute tracking / greenlet issues
    await db.execute(
        update(Draft).where(Draft.id == draft_id).values(**values)
    )
    await db.commit()

    # Re-fetch
    result2 = await db.execute(select(Draft).where(Draft.id == draft_id))
    updated = result2.scalar_one_or_none()
    return _draft_to_dict(updated) if updated else {"id": str(draft_id), "title": draft.title}


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    await db.delete(draft)
    await db.commit()
    return {"message": "Draft deleted"}
