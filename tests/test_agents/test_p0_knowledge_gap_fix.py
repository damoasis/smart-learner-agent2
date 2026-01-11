"""
P0修正验证测试：KnowledgeGap字段引用

验证修正后的字段引用是否正确访问ORM模型属性
"""
import pytest
from uuid import uuid4
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base
from backend.models.session import KnowledgeGap
from backend.models.learner import Learner
from backend.models.topic import Topic
from backend.models.tenant import Tenant


@pytest.fixture
def test_db_session():
    """创建测试数据库会话"""
    # 使用内存SQLite进行快速测试
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def test_data(test_db_session):
    """创建测试数据"""
    # 创建租户
    tenant = Tenant(
        tenant_id=uuid4(),
        tenant_name="测试租户",
        admin_email="test@example.com"
    )
    test_db_session.add(tenant)
    
    # 创建学习者
    learner = Learner(
        learner_id=uuid4(),
        tenant_id=tenant.tenant_id,
        learner_name="测试学习者",
        email="learner@example.com"
    )
    test_db_session.add(learner)
    
    # 创建主题
    topic = Topic(
        topic_id=uuid4(),
        tenant_id=tenant.tenant_id,
        domain_id=uuid4(),  # 简化测试，不创建实际domain
        topic_name="测试主题",
        difficulty_level="INTERMEDIATE"
    )
    test_db_session.add(topic)
    
    # 创建知识缺口
    gap1 = KnowledgeGap(
        gap_id=uuid4(),
        tenant_id=tenant.tenant_id,
        learner_id=learner.learner_id,
        topic_id=topic.topic_id,
        severity_level="low",  # 修正后的字段名
        gap_description="测试缺口1",
        identified_date=date.today()  # 修正后的字段名
    )
    test_db_session.add(gap1)
    
    gap2 = KnowledgeGap(
        gap_id=uuid4(),
        tenant_id=tenant.tenant_id,
        learner_id=learner.learner_id,
        topic_id=topic.topic_id,
        severity_level="high",  # 修正后的字段名
        gap_description="测试缺口2",
        identified_date=date.today()  # 修正后的字段名
    )
    test_db_session.add(gap2)
    
    test_db_session.commit()
    
    return {
        "tenant": tenant,
        "learner": learner,
        "topic": topic,
        "gaps": [gap1, gap2]
    }


def test_knowledge_gap_model_fields(test_data):
    """测试KnowledgeGap模型字段定义"""
    gap = test_data["gaps"][0]
    
    # 验证字段存在且可访问
    assert hasattr(gap, "severity_level")
    assert hasattr(gap, "identified_date")
    assert gap.severity_level == "low"
    assert gap.identified_date == date.today()


def test_knowledge_gap_field_access(test_data):
    """测试KnowledgeGap字段访问（模拟conversation_manager.py L384-385）"""
    gap = test_data["gaps"][0]
    
    # 模拟原代码中的字典构建
    gap_dict = {
        "gap_id": str(gap.gap_id),
        "topic_id": str(gap.topic_id),
        "gap_description": gap.gap_description,
        "severity": gap.severity_level,  # 修正后
        "identified_at": gap.identified_date.isoformat()  # 修正后
    }
    
    # 验证字典构建成功
    assert gap_dict["severity"] == "low"
    assert gap_dict["identified_at"] == date.today().isoformat()


def test_knowledge_gap_ordering(test_db_session, test_data):
    """测试KnowledgeGap排序（模拟conversation_manager.py L376）"""
    from sqlalchemy import select
    
    tenant_id = test_data["tenant"].tenant_id
    learner_id = test_data["learner"].learner_id
    
    # 模拟原查询语句
    query = select(KnowledgeGap).where(
        KnowledgeGap.learner_id == learner_id,
        KnowledgeGap.tenant_id == tenant_id,
        KnowledgeGap.resolution_date.is_(None)
    ).order_by(KnowledgeGap.severity_level.desc())  # 修正后
    
    gaps = test_db_session.execute(query).scalars().all()
    
    # 验证查询成功且排序正确（high应在low之前）
    assert len(gaps) == 2
    assert gaps[0].severity_level == "high"
    assert gaps[1].severity_level == "low"


def test_knowledge_gap_filtering(test_db_session, test_data):
    """测试KnowledgeGap过滤（模拟progress_tracker.py L474-475）"""
    gaps = test_data["gaps"]
    
    # 模拟原代码中的过滤逻辑
    low_medium_gaps = [g for g in gaps if g.severity_level in ["low", "medium"]]  # 修正后
    high_critical_gaps = [g for g in gaps if g.severity_level in ["high", "critical"]]  # 修正后
    
    # 验证过滤成功
    assert len(low_medium_gaps) == 1
    assert len(high_critical_gaps) == 1
    assert low_medium_gaps[0].severity_level == "low"
    assert high_critical_gaps[0].severity_level == "high"


def test_knowledge_gap_repr(test_data):
    """测试KnowledgeGap的__repr__方法"""
    gap = test_data["gaps"][0]
    repr_str = repr(gap)
    
    # 验证__repr__使用正确的字段
    assert "severity_level" in repr_str or "severity=low" in repr_str


def test_no_attribute_error_on_old_fields(test_data):
    """验证旧字段名会抛出AttributeError"""
    gap = test_data["gaps"][0]
    
    # 验证旧字段名不存在
    with pytest.raises(AttributeError):
        _ = gap.severity  # 旧字段名应该不存在
    
    with pytest.raises(AttributeError):
        _ = gap.identified_at  # 旧字段名应该不存在


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
P0修正验证测试：KnowledgeGap字段引用

验证修正后的字段引用是否正确访问ORM模型属性
"""
import pytest
from uuid import uuid4
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base
from backend.models.session import KnowledgeGap
from backend.models.learner import Learner
from backend.models.topic import Topic
from backend.models.tenant import Tenant


@pytest.fixture
def test_db_session():
    """创建测试数据库会话"""
    # 使用内存SQLite进行快速测试
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def test_data(test_db_session):
    """创建测试数据"""
    # 创建租户
    tenant = Tenant(
        tenant_id=uuid4(),
        tenant_name="测试租户",
        admin_email="test@example.com"
    )
    test_db_session.add(tenant)
    
    # 创建学习者
    learner = Learner(
        learner_id=uuid4(),
        tenant_id=tenant.tenant_id,
        learner_name="测试学习者",
        email="learner@example.com"
    )
    test_db_session.add(learner)
    
    # 创建主题
    topic = Topic(
        topic_id=uuid4(),
        tenant_id=tenant.tenant_id,
        domain_id=uuid4(),  # 简化测试，不创建实际domain
        topic_name="测试主题",
        difficulty_level="INTERMEDIATE"
    )
    test_db_session.add(topic)
    
    # 创建知识缺口
    gap1 = KnowledgeGap(
        gap_id=uuid4(),
        tenant_id=tenant.tenant_id,
        learner_id=learner.learner_id,
        topic_id=topic.topic_id,
        severity_level="low",  # 修正后的字段名
        gap_description="测试缺口1",
        identified_date=date.today()  # 修正后的字段名
    )
    test_db_session.add(gap1)
    
    gap2 = KnowledgeGap(
        gap_id=uuid4(),
        tenant_id=tenant.tenant_id,
        learner_id=learner.learner_id,
        topic_id=topic.topic_id,
        severity_level="high",  # 修正后的字段名
        gap_description="测试缺口2",
        identified_date=date.today()  # 修正后的字段名
    )
    test_db_session.add(gap2)
    
    test_db_session.commit()
    
    return {
        "tenant": tenant,
        "learner": learner,
        "topic": topic,
        "gaps": [gap1, gap2]
    }


def test_knowledge_gap_model_fields(test_data):
    """测试KnowledgeGap模型字段定义"""
    gap = test_data["gaps"][0]
    
    # 验证字段存在且可访问
    assert hasattr(gap, "severity_level")
    assert hasattr(gap, "identified_date")
    assert gap.severity_level == "low"
    assert gap.identified_date == date.today()


def test_knowledge_gap_field_access(test_data):
    """测试KnowledgeGap字段访问（模拟conversation_manager.py L384-385）"""
    gap = test_data["gaps"][0]
    
    # 模拟原代码中的字典构建
    gap_dict = {
        "gap_id": str(gap.gap_id),
        "topic_id": str(gap.topic_id),
        "gap_description": gap.gap_description,
        "severity": gap.severity_level,  # 修正后
        "identified_at": gap.identified_date.isoformat()  # 修正后
    }
    
    # 验证字典构建成功
    assert gap_dict["severity"] == "low"
    assert gap_dict["identified_at"] == date.today().isoformat()


def test_knowledge_gap_ordering(test_db_session, test_data):
    """测试KnowledgeGap排序（模拟conversation_manager.py L376）"""
    from sqlalchemy import select
    
    tenant_id = test_data["tenant"].tenant_id
    learner_id = test_data["learner"].learner_id
    
    # 模拟原查询语句
    query = select(KnowledgeGap).where(
        KnowledgeGap.learner_id == learner_id,
        KnowledgeGap.tenant_id == tenant_id,
        KnowledgeGap.resolution_date.is_(None)
    ).order_by(KnowledgeGap.severity_level.desc())  # 修正后
    
    gaps = test_db_session.execute(query).scalars().all()
    
    # 验证查询成功且排序正确（high应在low之前）
    assert len(gaps) == 2
    assert gaps[0].severity_level == "high"
    assert gaps[1].severity_level == "low"


def test_knowledge_gap_filtering(test_db_session, test_data):
    """测试KnowledgeGap过滤（模拟progress_tracker.py L474-475）"""
    gaps = test_data["gaps"]
    
    # 模拟原代码中的过滤逻辑
    low_medium_gaps = [g for g in gaps if g.severity_level in ["low", "medium"]]  # 修正后
    high_critical_gaps = [g for g in gaps if g.severity_level in ["high", "critical"]]  # 修正后
    
    # 验证过滤成功
    assert len(low_medium_gaps) == 1
    assert len(high_critical_gaps) == 1
    assert low_medium_gaps[0].severity_level == "low"
    assert high_critical_gaps[0].severity_level == "high"


def test_knowledge_gap_repr(test_data):
    """测试KnowledgeGap的__repr__方法"""
    gap = test_data["gaps"][0]
    repr_str = repr(gap)
    
    # 验证__repr__使用正确的字段
    assert "severity_level" in repr_str or "severity=low" in repr_str


def test_no_attribute_error_on_old_fields(test_data):
    """验证旧字段名会抛出AttributeError"""
    gap = test_data["gaps"][0]
    
    # 验证旧字段名不存在
    with pytest.raises(AttributeError):
        _ = gap.severity  # 旧字段名应该不存在
    
    with pytest.raises(AttributeError):
        _ = gap.identified_at  # 旧字段名应该不存在


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
