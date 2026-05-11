"""
OmniSynth - OCR API Endpoints
Multi-engine OCR: PDF, images, DOCX extraction
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, insert, update
from typing import Optional
from uuid import UUID
import uuid, os, aiofiles
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.research import Document, DocumentType, DocumentStatus
from app.middleware.auth import get_current_user
from app.services.ocr_service import ocr_service
from app.services.groq_service import groq_service
from app.services.embedding_service import embedding_service
from loguru import logger

router = APIRouter()


@router.post("/upload")
async def upload_and_extract(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    language: str = Form("en"),
    extract_tables: bool = Form(True),
    generate_summary: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file and extract text via OCR."""
    filename = file.filename or "document.txt"
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    # Save file
    doc_id = uuid.uuid4()
    upload_path = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, f"{doc_id}.{ext}")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Determine doc type
    type_map = {
        "pdf": DocumentType.PDF,
        "png": DocumentType.IMAGE,
        "jpg": DocumentType.IMAGE,
        "jpeg": DocumentType.IMAGE,
        "docx": DocumentType.DOCX,
        "txt": DocumentType.TXT,
    }
    doc_type = type_map.get(ext, DocumentType.TXT)

    # Create document record using raw INSERT
    session_uuid = uuid.UUID(session_id) if session_id else None
    now = datetime.utcnow()
    await db.execute(
        insert(Document).values(
            id=doc_id,
            user_id=current_user.id,
            session_id=session_uuid,
            title=filename,
            original_filename=filename,
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

    # Extract text
    try:
        result = await ocr_service.extract_from_file(file_path, language)
        extracted_text = result.get("text", "")
        page_count = result.get("page_count", 1)
        word_count = len(extracted_text.split()) if extracted_text else 0

        summary = None
        keywords = None
        faiss_index_id = None
        is_indexed = False

        # Generate summary if requested
        if generate_summary and extracted_text:
            summary = await groq_service.summarize_text(extracted_text[:6000])
            keywords = await groq_service.extract_keywords(extracted_text[:3000])

        # Index embeddings
        if extracted_text:
            chunks = embedding_service.chunk_text(extracted_text)
            if chunks:
                await embedding_service.initialize()
                ids = await embedding_service.add_documents(
                    texts=chunks,
                    metadatas=[{"document_id": str(doc_id), "chunk": i} for i in range(len(chunks))],
                )
                faiss_index_id = str(ids[0]) if ids else None
                is_indexed = True

        # Raw UPDATE — avoids ORM attribute tracking / greenlet issues
        await db.execute(
            update(Document)
            .where(Document.id == doc_id)
            .values(
                extracted_text=extracted_text[:10000] if extracted_text else None,
                page_count=page_count,
                word_count=word_count,
                ocr_completed=True,
                summary=summary,
                keywords=keywords,
                faiss_index_id=faiss_index_id,
                is_indexed=is_indexed,
                status=DocumentStatus.PROCESSED,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()

        return {
            "id": str(doc_id),
            "title": filename,
            "filename": filename,
            "file_size": len(content),
            "doc_type": doc_type,
            "status": DocumentStatus.PROCESSED,
            "word_count": word_count,
            "page_count": page_count,
            "is_indexed": is_indexed,
            "summary": summary,
            "keywords": keywords,
            "extracted_text_preview": extracted_text[:500] if extracted_text else "",
            "created_at": now.isoformat(),
        }
    except Exception as e:
        # Raw UPDATE on failure — avoids ORM greenlet issues
        await db.execute(
            update(Document)
            .where(Document.id == doc_id)
            .values(status=DocumentStatus.FAILED, updated_at=datetime.utcnow())
        )
        await db.commit()
        logger.error(f"OCR processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all processed documents."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(desc(Document.created_at))
        .offset(skip).limit(limit)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "filename": d.original_filename,
            "doc_type": d.doc_type,
            "status": d.status,
            "word_count": d.word_count,
            "page_count": d.page_count,
            "is_indexed": d.is_indexed,
            "summary": d.summary,
            "keywords": d.keywords,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details with extracted text."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id),
        "title": doc.title,
        "filename": doc.original_filename,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "extracted_text": doc.extracted_text,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "word_count": doc.word_count,
        "page_count": doc.page_count,
        "language": doc.language,
        "is_indexed": doc.is_indexed,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


@router.post("/extract-text")
async def extract_text_only(
    file: UploadFile = File(...),
    language: str = Form("en"),
    current_user: User = Depends(get_current_user),
):
    """Extract text from a file without saving to DB."""
    content = await file.read()
    filename = file.filename or "document.txt"
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await ocr_service.extract_from_file(tmp_path, language)
        return {
            "text": result.get("text", ""),
            "word_count": len(result.get("text", "").split()),
            "page_count": result.get("page_count", 1),
            "method": result.get("method", "auto"),
        }
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
