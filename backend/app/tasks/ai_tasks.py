"""
OmniSynth - AI Processing Celery Tasks
"""
from app.core.celery_app import celery_app
from loguru import logger


@celery_app.task(name="app.tasks.ai_tasks.generate_summary", bind=True, max_retries=2)
def generate_summary(self, document_id: str):
    """Generate AI summary for a document."""
    import asyncio
    try:
        asyncio.run(_generate_summary_async(document_id))
    except Exception as exc:
        logger.error(f"Summary generation failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


async def _generate_summary_async(document_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models.research import Document
    from app.services.groq_service import groq_service
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
        doc = result.scalar_one_or_none()
        if not doc or not doc.extracted_text:
            return
        summary = await groq_service.summarize_text(doc.extracted_text[:8000])
        keywords = await groq_service.extract_keywords(doc.extracted_text[:4000])
        doc.summary = summary
        doc.keywords = keywords
        await db.commit()
        logger.info(f"Summary generated for document {document_id}")


@celery_app.task(name="app.tasks.ai_tasks.generate_embeddings")
def generate_embeddings(texts: list, metadata: list = None):
    """Generate embeddings for a batch of texts."""
    import asyncio
    return asyncio.run(_generate_embeddings_async(texts, metadata or []))


async def _generate_embeddings_async(texts: list, metadata: list):
    from app.services.embedding_service import embedding_service
    await embedding_service.initialize()
    return await embedding_service.add_documents(texts=texts, metadatas=metadata)
