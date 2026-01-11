"""
学习者相关ORM模型
包含学习者、学习目标等
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Learner(Base, TimestampMixin):
    """学习者表"""
    
    __tablename__ = "learners"
    
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    native_language: Mapped[str] = mapped_column(String(50), default="en")
    learning_preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 关系
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="learners")
    learning_goals: Mapped[List["LearningGoal"]] = relationship(
        "LearningGoal",
        back_populates="learner",
        cascade="all, delete-orphan"
    )
    learning_sessions: Mapped[List["LearningSession"]] = relationship(
        "LearningSession",
        back_populates="learner",
        cascade="all, delete-orphan"
    )
    topic_masteries: Mapped[List["TopicMastery"]] = relationship(
        "TopicMastery",
        back_populates="learner",
        cascade="all, delete-orphan"
    )
    knowledge_gaps: Mapped[List["KnowledgeGap"]] = relationship(
        "KnowledgeGap",
        back_populates="learner",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Learner(id={self.learner_id}, name={self.name})>"


class LearningGoal(Base, TimestampMixin):
    """学习目标表"""
    
    __tablename__ = "learning_goals"
    
    goal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("learners.learner_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    goal_type: Mapped[str] = mapped_column(String(50), default="exam")
    goal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="active")
    preferred_teaching_mode: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("teaching_modes.mode_id")
    )
    goal_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 关系
    learner: Mapped["Learner"] = relationship("Learner", back_populates="learning_goals")
    knowledge_domains: Mapped[List["KnowledgeDomain"]] = relationship(
        "KnowledgeDomain",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    learning_sessions: Mapped[List["LearningSession"]] = relationship(
        "LearningSession",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<LearningGoal(id={self.goal_id}, name={self.goal_name})>"
