"""
主题和概念相关ORM模型
包含向量检索支持
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from backend.models.base import Base, TimestampMixin


class KnowledgeDomain(Base):
    """知识领域表"""
    
    __tablename__ = "knowledge_domains"
    
    domain_id: Mapped[UUID] = mapped_column(
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
    goal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("learning_goals.goal_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    domain_code: Mapped[Optional[str]] = mapped_column(String(20))
    domain_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_percentage: Mapped[Optional[Numeric]] = mapped_column(Numeric(5, 2))
    total_topics: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    recommended_teaching_mode: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("teaching_modes.mode_id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        nullable=False
    )
    
    # 关系
    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="knowledge_domains")
    topics: Mapped[List["Topic"]] = relationship(
        "Topic",
        back_populates="domain",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeDomain(id={self.domain_id}, name={self.domain_name})>"


class Topic(Base):
    """主题表"""
    
    __tablename__ = "topics"
    
    topic_id: Mapped[UUID] = mapped_column(
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
    domain_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_domains.domain_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    topic_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_materials: Mapped[dict] = mapped_column(JSONB, default=dict)
    estimated_learning_time_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))
    recommended_teaching_mode: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("teaching_modes.mode_id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        nullable=False
    )
    
    # 关系
    domain: Mapped["KnowledgeDomain"] = relationship("KnowledgeDomain", back_populates="topics")
    concepts: Mapped[List["Concept"]] = relationship(
        "Concept",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    topic_masteries: Mapped[List["TopicMastery"]] = relationship(
        "TopicMastery",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    knowledge_gaps: Mapped[List["KnowledgeGap"]] = relationship(
        "KnowledgeGap",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Topic(id={self.topic_id}, name={self.topic_name})>"


class Concept(Base, TimestampMixin):
    """概念表（包含向量embedding）"""
    
    __tablename__ = "concepts"
    
    concept_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    concept_name: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    formulas: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    rules: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    common_pitfalls: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    exam_tips: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    # 向量embedding字段（用于语义检索）
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    
    # 关系
    topic: Mapped["Topic"] = relationship("Topic", back_populates="concepts")
    
    def __repr__(self) -> str:
        return f"<Concept(id={self.concept_id}, name={self.concept_name})>"
    
    def has_embedding(self) -> bool:
        """检查是否有向量embedding"""
        return self.embedding is not None


class TopicDependency(Base):
    """主题依赖关系表"""
    
    __tablename__ = "topic_dependencies"
    
    dependency_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    prerequisite_topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dependent_topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dependency_type: Mapped[str] = mapped_column(String(50))
    strength: Mapped[Numeric] = mapped_column(Numeric(3, 2), default=0.50)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<TopicDependency(prerequisite={self.prerequisite_topic_id}, dependent={self.dependent_topic_id})>"
