"""
SQLAlchemy基础模型类
提供通用的模型基类和工具函数
"""
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有ORM模型的基类"""
    pass


class TimestampMixin:
    """时间戳混入类，提供created_at和updated_at字段"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False
    )


class UUIDMixin:
    """UUID主键混入类"""
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )


def model_to_dict(obj: Any, exclude: set = None) -> Dict[str, Any]:
    """
    将SQLAlchemy模型对象转换为字典
    
    Args:
        obj: SQLAlchemy模型对象
        exclude: 要排除的字段集合
    
    Returns:
        字典表示的模型数据
    """
    exclude = exclude or set()
    result = {}
    
    for column in obj.__table__.columns:
        if column.name not in exclude:
            value = getattr(obj, column.name)
            # 处理特殊类型
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, '__str__'):
                value = str(value)
            result[column.name] = value
    
    return result
