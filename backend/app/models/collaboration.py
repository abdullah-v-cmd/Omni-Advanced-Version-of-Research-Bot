"""
OmniSynth - Collaboration Models
Workspaces, members, notifications, activity logs
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum, ForeignKey, Integer, JSON, Float
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# Cross-database UUID type
class UUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(str(value))
            except (ValueError, AttributeError):
                pass
        return value


class WorkspaceRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    COLLABORATION = "collaboration"
    AI_COMPLETE = "ai_complete"
    MENTION = "mention"


class CollaborationWorkspace(Base):
    __tablename__ = "collaboration_workspaces"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_public = Column(Boolean, default=False)
    max_members = Column(Integer, default=10)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    comments = relationship("WorkspaceComment", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(), ForeignKey("collaboration_workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.VIEWER)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    workspace = relationship("CollaborationWorkspace", back_populates="members")


class WorkspaceComment(Base):
    __tablename__ = "workspace_comments"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(), ForeignKey("collaboration_workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(UUID(), ForeignKey("workspace_comments.id"), nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("CollaborationWorkspace", back_populates="comments")
    replies = relationship("WorkspaceComment", backref="parent", remote_side="[WorkspaceComment.id]")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.INFO)
    is_read = Column(Boolean, default=False)
    action_url = Column(String(500), nullable=True)
    notif_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(), nullable=True)
    title = Column(String(500), nullable=True)
    messages = Column(JSON, nullable=True)
    model_used = Column(String(100), nullable=True)
    total_tokens = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")


class PlagiarismReport(Base):
    __tablename__ = "plagiarism_reports"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    original_text = Column(Text, nullable=False)
    overall_score = Column(Integer, default=0)
    plagiarism_percentage = Column(Integer, default=0)
    matches = Column(JSON, nullable=True)
    report_data = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="plagiarism_reports")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    research_hours = Column(Integer, default=0)
    documents_processed = Column(Integer, default=0)
    ai_queries = Column(Integer, default=0)
    citations_generated = Column(Integer, default=0)
    drafts_created = Column(Integer, default=0)
    productivity_score = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    analytics_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="analytics")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="activity_logs")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)
    url = Column(String(2000), nullable=True)
    doi = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    relevance_score = Column(Integer, default=0)
    recommendation_reason = Column(Text, nullable=True)
    is_bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
