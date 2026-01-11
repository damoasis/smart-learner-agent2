"""
SQLAlchemy ORM数据模型
映射数据库表结构
"""
from backend.models.base import Base, TimestampMixin, UUIDMixin, model_to_dict
from backend.models.tenant import Tenant, TenantConfiguration, TenantUser
from backend.models.learner import Learner, LearningGoal
from backend.models.topic import KnowledgeDomain, Topic, Concept, TopicDependency
from backend.models.session import (
    LearningSession,
    QuestionAsked,
    Explanation,
    ComprehensionCheck,
    TopicMastery,
    KnowledgeGap,
    VerifiedContent,
    AuthoritySource,
    MnemonicDevice,
)
from backend.models.teaching_mode import (
    TeachingMode,
    TeachingModeConfig,
    DomainTeachingStrategy,
)

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "model_to_dict",
    # Tenant models
    "Tenant",
    "TenantConfiguration",
    "TenantUser",
    # Learner models
    "Learner",
    "LearningGoal",
    # Knowledge structure models
    "KnowledgeDomain",
    "Topic",
    "Concept",
    "TopicDependency",
    # Session models
    "LearningSession",
    "QuestionAsked",
    "Explanation",
    "ComprehensionCheck",
    "TopicMastery",
    "KnowledgeGap",
    "VerifiedContent",
    "AuthoritySource",
    "MnemonicDevice",
    # Teaching mode models
    "TeachingMode",
    "TeachingModeConfig",
    "DomainTeachingStrategy",
]
