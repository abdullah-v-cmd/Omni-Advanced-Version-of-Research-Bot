"""
OmniSynth - Citations API Endpoints
Multi-format citation generation, management, and export
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.research import Citation, Source
from app.schemas.research import CitationCreate, CitationResponse
from app.middleware.auth import get_current_user
from app.services.citation_service import citation_service
from app.services.groq_service import groq_service
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


class CitationGenerateRequest(BaseModel):
    style: str = "APA"
    title: str
    authors: List[str] = []
    year: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    source_type: str = "article"
    session_id: Optional[UUID] = None
    save: bool = True


class AllStylesRequest(BaseModel):
    title: str
    authors: List[str] = []
    year: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None


class AIExtractRequest(BaseModel):
    text: str
    style: str = "APA"


@router.post("/generate", status_code=201)
async def generate_citation(
    request: CitationGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a properly formatted citation in specified style."""
    data = {
        "title": request.title,
        "authors": request.authors,
        "year": request.year,
        "journal": request.journal,
        "volume": request.volume,
        "issue": request.issue,
        "pages": request.pages,
        "doi": request.doi,
        "url": request.url,
        "publisher": request.publisher,
    }
    result = await citation_service.generate_citation(request.style, data)

    if request.save:
        citation = Citation(
            id=uuid.uuid4(),
            user_id=current_user.id,
            session_id=request.session_id,
            style=request.style.upper(),
            formatted_text=result["formatted"],
            bibtex=result["bibtex"],
            raw_data=data,
            is_validated=True,
        )
        db.add(citation)
        await db.commit()
        await db.refresh(citation)

        return {
            "id": str(citation.id),
            "style": result["style"],
            "formatted": result["formatted"],
            "bibtex": result["bibtex"],
            "created_at": citation.created_at.isoformat(),
        }

    return {"style": result["style"], "formatted": result["formatted"], "bibtex": result["bibtex"]}


@router.post("/generate-all-styles")
async def generate_all_styles(
    request: AllStylesRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate citation in all supported styles at once."""
    data = {
        "title": request.title,
        "authors": request.authors,
        "year": request.year,
        "journal": request.journal,
        "volume": request.volume,
        "issue": request.issue,
        "pages": request.pages,
        "doi": request.doi,
        "url": request.url,
        "publisher": request.publisher,
    }
    return await citation_service.generate_all_styles(data)


@router.post("/extract-from-text")
async def extract_citation_from_text(
    request: AIExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """Use AI to extract citation information from text and format it."""
    system_prompt = """Extract bibliographic information from the given text and return as JSON with fields:
    title, authors (list), year, journal, volume, issue, pages, doi, publisher, url.
    Return ONLY valid JSON, no other text."""
    
    messages = [{"role": "user", "content": f"Extract citation data from:\n\n{request.text[:2000]}"}]
    
    try:
        response = await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=500, temperature=0.1)
        import json
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {"title": request.text[:100], "authors": [], "year": "2024"}
        
        citation = await citation_service.generate_citation(request.style, data)
        return {"extracted_data": data, "citation": citation}
    except Exception as e:
        logger.error(f"Citation extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract citation: {str(e)}")


@router.get("/", response_model=List[CitationResponse])
async def list_citations(
    session_id: Optional[UUID] = None,
    style: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's saved citations."""
    query = select(Citation).where(Citation.user_id == current_user.id)
    if session_id:
        query = query.where(Citation.session_id == session_id)
    if style:
        query = query.where(Citation.style == style.upper())
    query = query.order_by(desc(Citation.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{citation_id}")
async def delete_citation(
    citation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved citation."""
    result = await db.execute(
        select(Citation).where(Citation.id == citation_id, Citation.user_id == current_user.id)
    )
    citation = result.scalar_one_or_none()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found")
    await db.delete(citation)
    await db.commit()
    return {"message": "Citation deleted"}


@router.get("/styles")
async def get_citation_styles():
    """Get list of supported citation styles."""
    return {
        "styles": [
            {"id": "APA", "name": "APA 7th Edition", "description": "American Psychological Association"},
            {"id": "MLA", "name": "MLA 9th Edition", "description": "Modern Language Association"},
            {"id": "IEEE", "name": "IEEE", "description": "Institute of Electrical and Electronics Engineers"},
            {"id": "Chicago", "name": "Chicago 17th", "description": "Chicago Manual of Style"},
            {"id": "Harvard", "name": "Harvard", "description": "Harvard Referencing System"},
            {"id": "Vancouver", "name": "Vancouver", "description": "Vancouver System (Biomedical)"},
        ]
    }
