"""
教学模式相关ORM模型
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class TeachingMode(Base):
    """教学模式定义表"""
    
    __tablename__ = "teaching_modes"
    
    mode_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    mode_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mode_type: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    applicable_scenarios: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    default_parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_system_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<TeachingMode(id={self.mode_id}, name={self.mode_name})>"


class TeachingModeConfig(Base, TimestampMixin):
    """租户教学模式配置表"""
    
    __tablename__ = "teaching_mode_configs"
    
    config_id: Mapped[UUID] = mapped_column(
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
    mode_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("teaching_modes.mode_id"),
        nullable=False,
        index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    custom_parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    domain_mapping: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    def __repr__(self) -> str:
        return f"<TeachingModeConfig(id={self.config_id}, enabled={self.enabled})>"


class DomainTeachingStrategy(Base, TimestampMixin):
    """领域教学策略表"""
    
    __tablename__ = "domain_teaching_strategies"
    
    strategy_id: Mapped[UUID] = mapped_column(
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
    primary_mode_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("teaching_modes.mode_id"),
        nullable=False
    )
    fallback_mode_ids: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    switching_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(default=0.00)
    
    def __repr__(self) -> str:
        return f"<DomainTeachingStrategy(id={self.strategy_id}, domain_id={self.domain_id})>"
