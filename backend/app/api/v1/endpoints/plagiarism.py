"""
OmniSynth - Plagiarism Detection API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
import uuid
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.collaboration import PlagiarismReport
from app.middleware.auth import get_current_user
from app.services.plagiarism_service import plagiarism_service

router = APIRouter()


class PlagiarismCheckRequest(BaseModel):
    text: str
    document_id: Optional[UUID] = None
    detailed: bool = True


@router.post("/check")
async def check_plagiarism(
    request: PlagiarismCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check text for plagiarism and originality."""
    if len(request.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Text too short for plagiarism check (minimum 30 characters)")

    if request.detailed:
        report_data = await plagiarism_service.get_detailed_report(request.text)
    else:
        report_data = await plagiarism_service.check_plagiarism(
            request.text, str(request.document_id) if request.document_id else None
        )

    # Save report
    report = PlagiarismReport(
        id=uuid.uuid4(),
        user_id=current_user.id,
        document_id=request.document_id,
        original_text=request.text[:5000],
        overall_score=report_data.get("overall_score", 0),
        plagiarism_percentage=report_data.get("plagiarism_percentage", 0),
        matches=report_data.get("matches", []),
        report_data=report_data,
        status="completed",
    )
    db.add(report)
    await db.commit()

    return {
        "id": str(report.id),
        "overall_score": report.overall_score,
        "plagiarism_percentage": report.plagiarism_percentage,
        "matches": report.matches,
        "details": report_data.get("details", {}),
        "writing_metrics": report_data.get("writing_metrics", {}),
        "summary": report_data.get("summary", ""),
        "recommendation": report_data.get("recommendation", ""),
        "status": "completed",
        "created_at": report.created_at.isoformat(),
    }


@router.get("/reports")
async def list_plagiarism_reports(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's plagiarism check history."""
    result = await db.execute(
        select(PlagiarismReport)
        .where(PlagiarismReport.user_id == current_user.id)
        .order_by(desc(PlagiarismReport.created_at))
        .offset(skip)
        .limit(limit)
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "overall_score": r.overall_score,
            "plagiarism_percentage": r.plagiarism_percentage,
            "text_preview": r.original_text[:100] + "..." if len(r.original_text) > 100 else r.original_text,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_plagiarism_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific plagiarism report."""
    result = await db.execute(
        select(PlagiarismReport).where(
            PlagiarismReport.id == report_id,
            PlagiarismReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": str(report.id),
        "overall_score": report.overall_score,
        "plagiarism_percentage": report.plagiarism_percentage,
        "matches": report.matches,
        "report_data": report.report_data,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
    }
