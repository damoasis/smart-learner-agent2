"""
租户相关ORM模型
支持多租户架构
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """租户表"""
    
    __tablename__ = "tenants"
    
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="active")
    max_learners: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    max_domains: Mapped[Optional[int]] = mapped_column(Integer, default=5)
    allowed_teaching_modes: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), 
        default=["socratic"]
    )
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 关系
    learners: Mapped[List["Learner"]] = relationship(
        "Learner", 
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.tenant_id}, name={self.tenant_name})>"


class TenantConfiguration(Base, TimestampMixin):
    """租户配置表"""
    
    __tablename__ = "tenant_configurations"
    
    config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    config_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<TenantConfiguration(id={self.config_id}, key={self.config_key})>"


class TenantUser(Base):
    """租户用户关联表"""
    
    __tablename__ = "tenant_users"
    
    mapping_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="learner")
    permissions: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp()
    )
    
    def __repr__(self) -> str:
        return f"<TenantUser(mapping_id={self.mapping_id}, role={self.role})>"
