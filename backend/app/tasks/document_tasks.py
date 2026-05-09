"""
OmniSynth - Document Processing Celery Tasks
"""
from app.core.celery_app import celery_app
from loguru import logger


@celery_app.task(name="app.tasks.document_tasks.process_document", bind=True, max_retries=3)
def process_document(self, document_id: str, file_path: str, doc_type: str):
    """Process a document: OCR, embedding, indexing."""
    import asyncio
    try:
        asyncio.run(_process_document_async(document_id, file_path, doc_type))
    except Exception as exc:
        logger.error(f"Document processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


async def _process_document_async(document_id: str, file_path: str, doc_type: str):
    from app.core.database import AsyncSessionLocal
    from app.models.research import Document, DocumentStatus
    from app.services.ocr_service import ocr_service
    from app.services.embedding_service import embedding_service
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            return

        try:
            doc.status = DocumentStatus.PROCESSING
            await db.commit()

            # OCR extraction
            extracted = await ocr_service.extract_from_file(file_path)
            doc.extracted_text = extracted.get("text", "")
            doc.page_count = extracted.get("page_count", 0)
            doc.word_count = len(doc.extracted_text.split()) if doc.extracted_text else 0
            doc.ocr_completed = True

            # Embedding and indexing
            if doc.extracted_text:
                chunks = embedding_service.chunk_text(doc.extracted_text)
                if chunks:
                    await embedding_service.initialize()
                    ids = await embedding_service.add_documents(
                        texts=chunks,
                        metadatas=[{"document_id": document_id, "chunk": i} for i in range(len(chunks))],
                    )
                    doc.faiss_index_id = str(ids[0]) if ids else None
                    doc.is_indexed = True

            doc.status = DocumentStatus.PROCESSED
            await db.commit()
            logger.info(f"Document {document_id} processed successfully")

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            await db.commit()
            raise e
