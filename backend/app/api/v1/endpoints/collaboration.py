"""
OmniSynth - Collaboration API Endpoints
Workspaces, members, comments, real-time collaboration
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, insert, update
from typing import List, Optional, Dict
from uuid import UUID
import uuid
import json
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.collaboration import (
    CollaborationWorkspace, WorkspaceMember, WorkspaceComment,
    WorkspaceRole, Notification,
)
from app.middleware.auth import get_current_user
from loguru import logger

router = APIRouter()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workspace_id: str):
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)

    def disconnect(self, websocket: WebSocket, workspace_id: str):
        if workspace_id in self.active_connections:
            try:
                self.active_connections[workspace_id].remove(websocket)
            except ValueError:
                pass

    async def broadcast(self, message: dict, workspace_id: str):
        if workspace_id in self.active_connections:
            dead = []
            for connection in self.active_connections[workspace_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    dead.append(connection)
            for d in dead:
                try:
                    self.active_connections[workspace_id].remove(d)
                except ValueError:
                    pass


manager = ConnectionManager()


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[UUID] = None


@router.post("/workspaces", status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace_id = uuid.uuid4()
    now = datetime.utcnow()

    # Raw INSERT — avoids ORM attribute tracking / greenlet issues
    await db.execute(
        insert(CollaborationWorkspace).values(
            id=workspace_id,
            name=data.name,
            description=data.description,
            owner_id=current_user.id,
            is_public=data.is_public,
            created_at=now,
            updated_at=now,
        )
    )
    await db.execute(
        insert(WorkspaceMember).values(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=current_user.id,
            role=WorkspaceRole.OWNER,
            is_active=True,
            joined_at=now,
        )
    )
    await db.commit()
    return {
        "id": str(workspace_id),
        "name": data.name,
        "description": data.description,
        "is_public": data.is_public,
        "created_at": now.isoformat(),
    }


@router.get("/workspaces")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.is_active == True,
        )
    )
    memberships = result.scalars().all()
    workspace_ids = [m.workspace_id for m in memberships]

    workspaces = []
    for wid in workspace_ids:
        ws_result = await db.execute(
            select(CollaborationWorkspace).where(CollaborationWorkspace.id == wid)
        )
        ws = ws_result.scalar_one_or_none()
        if ws:
            workspaces.append({
                "id": str(ws.id),
                "name": ws.name,
                "description": ws.description,
                "is_public": ws.is_public,
                "created_at": ws.created_at.isoformat() if ws.created_at else None,
            })
    return workspaces


@router.get("/workspaces/{workspace_id}")
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific workspace by ID."""
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id)
    )
    ws = ws_result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check membership
    mem_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.is_active == True,
        )
    )
    if not mem_result.scalar_one_or_none() and not ws.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get members count
    members_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True,
        )
    )
    members = members_result.scalars().all()

    return {
        "id": str(ws.id),
        "name": ws.name,
        "description": ws.description,
        "is_public": ws.is_public,
        "owner_id": str(ws.owner_id),
        "member_count": len(members),
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
    }


@router.put("/workspaces/{workspace_id}")
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a workspace (owner only)."""
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id)
    )
    ws = ws_result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if ws.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can update workspace")

    values = data.model_dump(exclude_none=True)
    values["updated_at"] = datetime.utcnow()
    await db.execute(
        update(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id).values(**values)
    )
    await db.commit()
    return {"message": "Workspace updated", "id": str(workspace_id)}


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a workspace (owner only)."""
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id)
    )
    ws = ws_result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if ws.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete workspace")

    await db.delete(ws)
    await db.commit()
    return {"message": "Workspace deleted"}


@router.get("/workspaces/{workspace_id}/members")
async def list_members(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members of a workspace."""
    # Verify access
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id)
    )
    ws = ws_result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    mem_check = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.is_active == True,
        )
    )
    if not mem_check.scalar_one_or_none() and not ws.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True,
        )
    )
    members = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "user_id": str(m.user_id),
            "role": m.role,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        }
        for m in members
    ]


@router.get("/workspaces/{workspace_id}/conversations")
async def list_workspace_conversations(
    workspace_id: UUID,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List AI conversations linked to a workspace session."""
    from app.models.collaboration import AIConversation

    # Verify workspace exists and user has access
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id)
    )
    ws = ws_result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    mem_check = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.is_active == True,
        )
    )
    if not mem_check.scalar_one_or_none() and not ws.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    # AIConversation uses session_id (UUID) — query conversations whose
    # session_id matches the workspace_id (shared UUID namespace for collab).
    result = await db.execute(
        select(AIConversation)
        .where(
            AIConversation.session_id == workspace_id,
            AIConversation.is_archived == False,
        )
        .order_by(desc(AIConversation.updated_at))
        .offset(skip).limit(limit)
    )
    convs = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "model_used": c.model_used,
            "message_count": len(c.messages) if c.messages else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in convs
    ]


@router.post("/workspaces/{workspace_id}/members")
async def add_member(
    workspace_id: UUID,
    user_email: str,
    role: WorkspaceRole = WorkspaceRole.EDITOR,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify workspace ownership
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(CollaborationWorkspace.id == workspace_id)
    )
    workspace = ws_result.scalar_one_or_none()
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Find user by email
    user_result = await db.execute(select(User).where(User.email == user_email))
    target_user = user_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        insert(WorkspaceMember).values(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=target_user.id,
            role=role,
            is_active=True,
            joined_at=datetime.utcnow(),
        )
    )
    await db.commit()
    return {"message": f"Added {user_email} as {role}"}


@router.post("/workspaces/{workspace_id}/comments")
async def add_comment(
    workspace_id: UUID,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment_id = uuid.uuid4()
    now = datetime.utcnow()

    # Raw INSERT — avoids ORM attribute tracking / greenlet issues
    await db.execute(
        insert(WorkspaceComment).values(
            id=comment_id,
            workspace_id=workspace_id,
            user_id=current_user.id,
            content=data.content,
            parent_id=data.parent_id,
            created_at=now,
            updated_at=now,
        )
    )
    await db.commit()

    # Broadcast to WebSocket clients
    await manager.broadcast(
        {
            "type": "new_comment",
            "comment_id": str(comment_id),
            "user": current_user.username,
            "content": data.content[:200],
            "timestamp": now.isoformat(),
        },
        str(workspace_id),
    )

    return {"id": str(comment_id), "content": data.content, "created_at": now.isoformat()}


@router.get("/workspaces/{workspace_id}/comments")
async def get_comments(
    workspace_id: UUID,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkspaceComment)
        .where(WorkspaceComment.workspace_id == workspace_id)
        .order_by(desc(WorkspaceComment.created_at))
        .offset(skip).limit(limit)
    )
    comments = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "content": c.content,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in comments
    ]


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Raw UPDATE — avoids ORM attribute tracking / greenlet issues
    await db.execute(
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "Marked as read"}


@router.websocket("/ws/{workspace_id}")
async def workspace_websocket(websocket: WebSocket, workspace_id: str):
    """Real-time WebSocket for workspace collaboration."""
    await manager.connect(websocket, workspace_id)
    try:
        await websocket.send_text(
            json.dumps({"type": "connected", "workspace_id": workspace_id})
        )
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await manager.broadcast(
                {
                    "type": msg.get("type", "message"),
                    "content": msg.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                workspace_id,
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, workspace_id)
