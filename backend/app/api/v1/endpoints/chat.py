"""
OmniSynth - AI Chat API Endpoints
Conversational AI with streaming, multi-turn memory, HyDE RAG
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
import uuid
import json

from app.core.database import get_db
from app.models.user import User
from app.models.collaboration import AIConversation
from app.middleware.auth import get_current_user
from app.agents.orchestrator import orchestrator
from app.services.groq_service import groq_service
from loguru import logger

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    use_hyde: bool = True
    stream: bool = False
    agent_type: Optional[str] = None
    context: Optional[dict] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = None


@router.post("/send")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to OmniSynth AI and get response."""
    conversation = None
    history = []

    if request.conversation_id:
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == request.conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation and conversation.messages:
            history = conversation.messages[-10:]  # Last 10 messages for context

    # Process with multi-agent orchestrator
    result = await orchestrator.route_and_execute(
        query=request.message,
        agent_type=request.agent_type,
        context=request.context or {},
        conversation_history=history,
    )

    answer = result.get("answer", "I couldn't generate a response. Please try again.")
    agent_used = result.get("agent", "general")
    model_used = result.get("model_used", groq_service.primary_model)

    # Update or create conversation
    new_messages = list(history) + [
        {"role": "user", "content": request.message, "timestamp": datetime.utcnow().isoformat()},
        {"role": "assistant", "content": answer, "agent": agent_used, "timestamp": datetime.utcnow().isoformat()},
    ]

    if conversation:
        conversation.messages = new_messages
        conversation.updated_at = datetime.utcnow()
        conversation.model_used = model_used
    else:
        conversation = AIConversation(
            id=uuid.uuid4(),
            user_id=current_user.id,
            title=request.message[:60] + "..." if len(request.message) > 60 else request.message,
            messages=new_messages,
            model_used=model_used,
        )
        db.add(conversation)

    await db.commit()
    await db.refresh(conversation)

    return {
        "conversation_id": str(conversation.id),
        "message": answer,
        "agent": agent_used,
        "model": model_used,
        "sources": result.get("sources", []),
        "hyde_document": result.get("hyde_document"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stream")
async def stream_message(
    message: str,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Stream AI response using Server-Sent Events."""
    async def generate():
        history = []
        yield f"data: {json.dumps({'type': 'start', 'agent': 'general'})}\n\n"
        try:
            messages = list(history) + [{"role": "user", "content": message}]
            async for chunk in groq_service.stream_generate(
                messages=messages,
                system_prompt="You are OmniSynth, an expert AI research assistant.",
            ):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's AI conversations."""
    result = await db.execute(
        select(AIConversation)
        .where(AIConversation.user_id == current_user.id, AIConversation.is_archived == False)
        .order_by(desc(AIConversation.updated_at))
        .offset(skip).limit(limit)
    )
    conversations = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "model_used": c.model_used,
            "message_count": len(c.messages) if c.messages else 0,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation with full message history."""
    result = await db.execute(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "messages": conversation.messages or [],
        "model_used": conversation.model_used,
        "created_at": conversation.created_at.isoformat(),
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    result = await db.execute(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conversation)
    await db.commit()
    return {"message": "Conversation deleted"}


@router.get("/agents")
async def list_agents():
    """Get list of available AI agents."""
    return {
        "agents": [
            {"id": k, "name": v, "description": f"Specialized {v}"}
            for k, v in orchestrator.AGENT_TYPES.items()
        ]
    }
