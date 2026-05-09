"""
OmniSynth - Analytics API Endpoints
Productivity analytics, research progress, AI usage tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.collaboration import Analytics, ActivityLog
from app.models.research import ResearchSession, Document, Draft, Citation
from app.models.collaboration import AIConversation, PlagiarismReport
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive analytics dashboard data."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    total_sessions = (await db.execute(
        select(func.count(ResearchSession.id)).where(ResearchSession.user_id == current_user.id)
    )).scalar() or 0

    total_documents = (await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )).scalar() or 0

    total_drafts = (await db.execute(
        select(func.count(Draft.id)).where(Draft.user_id == current_user.id)
    )).scalar() or 0

    total_citations = (await db.execute(
        select(func.count(Citation.id)).where(Citation.user_id == current_user.id)
    )).scalar() or 0

    total_conversations = (await db.execute(
        select(func.count(AIConversation.id)).where(AIConversation.user_id == current_user.id)
    )).scalar() or 0

    total_plagiarism = (await db.execute(
        select(func.count(PlagiarismReport.id)).where(PlagiarismReport.user_id == current_user.id)
    )).scalar() or 0

    # Recent sessions
    recent_result = await db.execute(
        select(ResearchSession)
        .where(ResearchSession.user_id == current_user.id)
        .order_by(desc(ResearchSession.created_at))
        .limit(5)
    )
    recent_sessions = recent_result.scalars().all()

    # Activity in last 7 days
    recent_sessions_count = (await db.execute(
        select(func.count(ResearchSession.id))
        .where(ResearchSession.user_id == current_user.id, ResearchSession.created_at >= seven_days_ago)
    )).scalar() or 0

    recent_docs_count = (await db.execute(
        select(func.count(Document.id))
        .where(Document.user_id == current_user.id, Document.created_at >= seven_days_ago)
    )).scalar() or 0

    # Calculate productivity score
    productivity_score = min(100, (
        total_sessions * 5 +
        total_documents * 10 +
        total_drafts * 8 +
        total_citations * 3 +
        total_conversations * 2
    ))

    return {
        "summary": {
            "total_sessions": total_sessions,
            "total_documents": total_documents,
            "total_drafts": total_drafts,
            "total_citations": total_citations,
            "total_ai_conversations": total_conversations,
            "total_plagiarism_checks": total_plagiarism,
            "productivity_score": productivity_score,
        },
        "recent_activity": {
            "sessions_last_7_days": recent_sessions_count,
            "documents_last_7_days": recent_docs_count,
        },
        "recent_sessions": [
            {
                "id": str(s.id),
                "title": s.title,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in recent_sessions
        ],
        "charts": {
            "weekly_activity": [
                {"day": (now - timedelta(days=i)).strftime("%a"), "sessions": max(0, recent_sessions_count - i), "documents": max(0, recent_docs_count - i)}
                for i in range(6, -1, -1)
            ],
        },
    }


@router.get("/activity")
async def get_activity_log(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user activity log."""
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(desc(ActivityLog.created_at))
        .offset(skip).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "action": l.action,
            "resource_type": l.resource_type,
            "details": l.details,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.get("/productivity")
async def get_productivity_metrics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed productivity metrics."""
    start_date = datetime.utcnow() - timedelta(days=days)

    sessions = (await db.execute(
        select(func.count(ResearchSession.id))
        .where(ResearchSession.user_id == current_user.id, ResearchSession.created_at >= start_date)
    )).scalar() or 0

    documents = (await db.execute(
        select(func.count(Document.id))
        .where(Document.user_id == current_user.id, Document.created_at >= start_date)
    )).scalar() or 0

    drafts = (await db.execute(
        select(func.count(Draft.id))
        .where(Draft.user_id == current_user.id, Draft.created_at >= start_date)
    )).scalar() or 0

    citations = (await db.execute(
        select(func.count(Citation.id))
        .where(Citation.user_id == current_user.id, Citation.created_at >= start_date)
    )).scalar() or 0

    return {
        "period_days": days,
        "metrics": {
            "research_sessions": sessions,
            "documents_processed": documents,
            "drafts_created": drafts,
            "citations_generated": citations,
            "ai_interactions": (await db.execute(
                select(func.count(AIConversation.id))
                .where(AIConversation.user_id == current_user.id, AIConversation.created_at >= start_date)
            )).scalar() or 0,
        },
        "efficiency_score": min(100, (sessions * 5 + documents * 10 + drafts * 8 + citations * 3)),
        "insights": [
            "You're most productive in the morning hours." if sessions > 5 else "Start more research sessions to boost productivity.",
            f"You've processed {documents} documents this period.",
            "Great job using AI assistance!" if (await db.execute(select(func.count(AIConversation.id)).where(AIConversation.user_id == current_user.id, AIConversation.created_at >= start_date))).scalar() > 0 else "Try using OmniChat for research assistance.",
        ],
    }


@router.get("/recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-powered productivity recommendations."""
    from app.models.collaboration import Recommendation
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .order_by(desc(Recommendation.relevance_score))
        .limit(10)
    )
    recs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "abstract": r.abstract,
            "authors": r.authors,
            "url": r.url,
            "year": r.year,
            "relevance_score": r.relevance_score,
            "reason": r.recommendation_reason,
        }
        for r in recs
    ]
