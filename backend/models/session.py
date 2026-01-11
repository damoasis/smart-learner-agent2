"""

学习会话和进度追踪相关ORM模型

"""

from datetime import date, datetime

from typing import Any, Dict, List, Optional

from uuid import UUID, uuid4



from sqlalchemy import ARRAY, Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func

from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from sqlalchemy.orm import Mapped, mapped_column, relationship



from backend.models.base import Base, TimestampMixin





class LearningSession(Base):

    """学习会话表"""

    

    __tablename__ = "learning_sessions"

    

    session_id: Mapped[UUID] = mapped_column(

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

    goal_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("learning_goals.goal_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    start_time: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))

    session_format: Mapped[Optional[str]] = mapped_column(String(50))

    teaching_mode_used: Mapped[Optional[UUID]] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("teaching_modes.mode_id")

    )

    teaching_mode_switches: Mapped[Optional[List[dict]]] = mapped_column(

        ARRAY(JSONB),

        default=list

    )

    session_notes: Mapped[Optional[str]] = mapped_column(Text)

    topics_covered: Mapped[Optional[List[UUID]]] = mapped_column(

        ARRAY(PGUUID(as_uuid=True)),

        default=list

    )

    performance_summary: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    

    # 关系

    learner: Mapped["Learner"] = relationship("Learner", back_populates="learning_sessions")

    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="learning_sessions")

    questions: Mapped[List["QuestionAsked"]] = relationship(

        "QuestionAsked",

        back_populates="session",

        cascade="all, delete-orphan"

    )

    

    def __repr__(self) -> str:

        return f"<LearningSession(id={self.session_id}, start={self.start_time})>"

    

    def duration_minutes(self) -> Optional[int]:

        """计算会话时长（分钟）"""

        if self.end_time and self.start_time:

            delta = self.end_time - self.start_time

            return int(delta.total_seconds() / 60)

        return None





class QuestionAsked(Base):

    """提问记录表"""

    

    __tablename__ = "questions_asked"

    

    question_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        primary_key=True,

        default=uuid4

    )

    session_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("learning_sessions.session_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    topic_id: Mapped[Optional[UUID]] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("topics.topic_id")

    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    initial_understanding: Mapped[Optional[str]] = mapped_column(Text)

    timestamp: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    

    # 关系

    session: Mapped["LearningSession"] = relationship("LearningSession", back_populates="questions")

    explanations: Mapped[List["Explanation"]] = relationship(

        "Explanation",

        back_populates="question",

        cascade="all, delete-orphan"

    )

    

    def __repr__(self) -> str:

        return f"<QuestionAsked(id={self.question_id}, text={self.question_text[:50]})>"





class Explanation(Base):

    """解释记录表"""

    

    __tablename__ = "explanations"

    

    explanation_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        primary_key=True,

        default=uuid4

    )

    question_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("questions_asked.question_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    agent_explanation: Mapped[str] = mapped_column(Text, nullable=False)

    teaching_method_used: Mapped[Optional[str]] = mapped_column(String(100))

    teaching_agent_type: Mapped[Optional[str]] = mapped_column(String(50))

    sources_cited: Mapped[dict] = mapped_column(JSONB, default=dict)

    explanation_length_words: Mapped[Optional[int]] = mapped_column(Integer)

    clarity_rating: Mapped[Optional[Numeric]] = mapped_column(Numeric(3, 2))

    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    

    # 关系

    question: Mapped["QuestionAsked"] = relationship("QuestionAsked", back_populates="explanations")

    comprehension_checks: Mapped[List["ComprehensionCheck"]] = relationship(

        "ComprehensionCheck",

        back_populates="explanation",

        cascade="all, delete-orphan"

    )

    

    def __repr__(self) -> str:

        return f"<Explanation(id={self.explanation_id})>"





class ComprehensionCheck(Base):

    """理解检查表"""

    

    __tablename__ = "comprehension_checks"

    

    check_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        primary_key=True,

        default=uuid4

    )

    explanation_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("explanations.explanation_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    question_asked: Mapped[str] = mapped_column(Text, nullable=False)

    learner_response: Mapped[Optional[str]] = mapped_column(Text)

    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)

    assessment_result: Mapped[Optional[str]] = mapped_column(String(50))

    follow_up_needed: Mapped[bool] = mapped_column(Boolean, default=False)

    timestamp: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    

    # 关系

    explanation: Mapped["Explanation"] = relationship("Explanation", back_populates="comprehension_checks")

    

    def __repr__(self) -> str:

        return f"<ComprehensionCheck(id={self.check_id}, result={self.assessment_result})>"





class TopicMastery(Base, TimestampMixin):

    """主题掌握状态表"""

    

    __tablename__ = "topic_mastery"

    

    mastery_id: Mapped[UUID] = mapped_column(

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

    topic_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("topics.topic_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    mastery_date: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)

    confidence_level: Mapped[str] = mapped_column(String(50), nullable=False)

    key_points_understood: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))

    supporting_session_ids: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))

    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))

    review_count: Mapped[int] = mapped_column(Integer, default=0)

    teaching_modes_used: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))

    

    # 关系

    learner: Mapped["Learner"] = relationship("Learner", back_populates="topic_masteries")

    topic: Mapped["Topic"] = relationship("Topic", back_populates="topic_masteries")

    

    def __repr__(self) -> str:

        return f"<TopicMastery(id={self.mastery_id}, confidence={self.confidence_level})>"





class KnowledgeGap(Base, TimestampMixin):

    """知识缺口表"""

    

    __tablename__ = "knowledge_gaps"

    

    gap_id: Mapped[UUID] = mapped_column(

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

    topic_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("topics.topic_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    severity_level: Mapped[str] = mapped_column(String(50), nullable=False)

    gap_description: Mapped[str] = mapped_column(Text, nullable=False)

    identified_date: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)

    resolution_date: Mapped[Optional[date]] = mapped_column(Date)

    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    related_session_ids: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))

    

    # 关系

    learner: Mapped["Learner"] = relationship("Learner", back_populates="knowledge_gaps")

    topic: Mapped["Topic"] = relationship("Topic", back_populates="knowledge_gaps")

    

    def __repr__(self) -> str:

        return f"<KnowledgeGap(id={self.gap_id}, severity={self.severity_level})>"

    

    def is_resolved(self) -> bool:

        """检查是否已解决"""

        return self.resolution_date is not None





class VerifiedContent(Base, TimestampMixin):

    """已验证内容表（阶段二新增）"""

    

    __tablename__ = "verified_content"

    

    content_id: Mapped[UUID] = mapped_column(

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

    concept_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("concepts.concept_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    content_text: Mapped[str] = mapped_column(Text, nullable=False)

    sources: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)

    verification_date: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    

    def __repr__(self) -> str:

        return f"<VerifiedContent(id={self.content_id}, confidence={self.confidence_score})>"





class AuthoritySource(Base, TimestampMixin):

    """权威来源表（阶段二新增）"""

    

    __tablename__ = "authority_sources"

    

    source_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        primary_key=True,

        default=uuid4

    )

    source_name: Mapped[str] = mapped_column(String(255), nullable=False)

    base_url: Mapped[str] = mapped_column(String(500), nullable=False)

    domain_tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)

    trust_score: Mapped[float] = mapped_column(Float, nullable=False)

    last_verified: Mapped[datetime] = mapped_column(

        DateTime(timezone=False),

        server_default=func.current_timestamp(),

        nullable=False

    )

    

    def __repr__(self) -> str:

        return f"<AuthoritySource(id={self.source_id}, name={self.source_name})>"





class MnemonicDevice(Base, TimestampMixin):

    """记忆辅助设备表（阶段二新增）"""

    

    __tablename__ = "mnemonic_devices"

    

    mnemonic_id: Mapped[UUID] = mapped_column(

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

    concept_id: Mapped[UUID] = mapped_column(

        PGUUID(as_uuid=True),

        ForeignKey("concepts.concept_id", ondelete="CASCADE"),

        nullable=False,

        index=True

    )

    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    effectiveness_rating: Mapped[float] = mapped_column(Float, nullable=False)

    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    

    def __repr__(self) -> str:

        return f"<MnemonicDevice(id={self.mnemonic_id}, strategy={self.strategy_type})>"
