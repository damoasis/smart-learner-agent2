"""数据库连接和会话管理"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator
import uuid

from backend.config.settings import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 检查连接是否有效
    pool_recycle=3600,  # 1小时后回收连接
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    用于FastAPI的Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context(tenant_id: str = None):
    """
    获取数据库会话的上下文管理器
    自动设置租户ID（如果启用RLS）
    
    Args:
        tenant_id: 租户ID，如果为None则使用默认租户ID
    
    Usage:
        with get_db_context(tenant_id="xxx") as db:
            # 执行数据库操作
            pass
    """
    db = SessionLocal()
    try:
        # 如果启用了RLS，设置当前租户ID
        if settings.enable_rls:
            actual_tenant_id = tenant_id or settings.default_tenant_id
            db.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": actual_tenant_id}
            )
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def set_tenant_context(db: Session, tenant_id: str):
    """
    为已存在的数据库会话设置租户上下文
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
    """
    if settings.enable_rls:
        db.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )


def init_db():
    """
    初始化数据库
    创建所有表（开发环境使用，生产环境应使用Alembic迁移）
    """
    # 导入所有模型以确保它们被注册到Base.metadata
    # from backend.models import ...
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True，否则返回False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False


def get_uuid() -> str:
    """
    生成UUID字符串
    
    Returns:
        str: UUID字符串
    """
    return str(uuid.uuid4())
"""数据库连接和会话管理"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator
import uuid

from backend.config.settings import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 检查连接是否有效
    pool_recycle=3600,  # 1小时后回收连接
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    用于FastAPI的Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context(tenant_id: str = None):
    """
    获取数据库会话的上下文管理器
    自动设置租户ID（如果启用RLS）
    
    Args:
        tenant_id: 租户ID，如果为None则使用默认租户ID
    
    Usage:
        with get_db_context(tenant_id="xxx") as db:
            # 执行数据库操作
            pass
    """
    db = SessionLocal()
    try:
        # 如果启用了RLS，设置当前租户ID
        if settings.enable_rls:
            actual_tenant_id = tenant_id or settings.default_tenant_id
            db.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": actual_tenant_id}
            )
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def set_tenant_context(db: Session, tenant_id: str):
    """
    为已存在的数据库会话设置租户上下文
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
    """
    if settings.enable_rls:
        db.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )


def init_db():
    """
    初始化数据库
    创建所有表（开发环境使用，生产环境应使用Alembic迁移）
    """
    # 导入所有模型以确保它们被注册到Base.metadata
    # from backend.models import ...
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True，否则返回False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False


def get_uuid() -> str:
    """
    生成UUID字符串
    
    Returns:
        str: UUID字符串
    """
    return str(uuid.uuid4())
