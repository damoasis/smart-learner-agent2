"""
数据库服务层
提供数据库CRUD操作的封装
"""
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.models.base import Base

T = TypeVar("T", bound=Base)


class DatabaseService:
    """数据库服务类，提供通用的CRUD操作"""
    
    def __init__(self, session: Session):
        """
        初始化数据库服务
        
        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session
    
    def get_by_id(self, model: Type[T], id: UUID) -> Optional[T]:
        """
        根据ID获取单个对象
        
        Args:
            model: 模型类
            id: 对象ID
        
        Returns:
            模型对象或None
        """
        return self.session.get(model, id)
    
    def get_all(self, model: Type[T], limit: int = 100, offset: int = 0) -> List[T]:
        """
        获取所有对象（分页）
        
        Args:
            model: 模型类
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            模型对象列表
        """
        stmt = select(model).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())
    
    def filter_by(self, model: Type[T], **filters) -> List[T]:
        """
        根据条件过滤查询
        
        Args:
            model: 模型类
            **filters: 过滤条件（字段名=值）
        
        Returns:
            符合条件的模型对象列表
        """
        stmt = select(model)
        for key, value in filters.items():
            if hasattr(model, key):
                stmt = stmt.where(getattr(model, key) == value)
        return list(self.session.execute(stmt).scalars().all())
    
    def create(self, obj: T) -> T:
        """
        创建新对象
        
        Args:
            obj: 模型对象
        
        Returns:
            创建后的对象
        """
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj
    
    def update_by_id(self, model: Type[T], id: UUID, **updates) -> Optional[T]:
        """
        根据ID更新对象
        
        Args:
            model: 模型类
            id: 对象ID
            **updates: 要更新的字段
        
        Returns:
            更新后的对象或None
        """
        obj = self.get_by_id(model, id)
        if obj:
            for key, value in updates.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.session.flush()
            self.session.refresh(obj)
        return obj
    
    def delete_by_id(self, model: Type[T], id: UUID) -> bool:
        """
        根据ID删除对象
        
        Args:
            model: 模型类
            id: 对象ID
        
        Returns:
            是否删除成功
        """
        obj = self.get_by_id(model, id)
        if obj:
            self.session.delete(obj)
            self.session.flush()
            return True
        return False
    
    def count(self, model: Type[T], **filters) -> int:
        """
        统计符合条件的对象数量
        
        Args:
            model: 模型类
            **filters: 过滤条件
        
        Returns:
            数量
        """
        stmt = select(model)
        for key, value in filters.items():
            if hasattr(model, key):
                stmt = stmt.where(getattr(model, key) == value)
        return len(list(self.session.execute(stmt).scalars().all()))
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()
    
    def close(self):
        """关闭会话"""
        self.session.close()


class LearnerService:
    """学习者相关的业务逻辑服务"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def get_learner_by_email(self, tenant_id: UUID, email: str):
        """根据邮箱获取学习者"""
        from backend.models import Learner
        learners = self.db.filter_by(Learner, tenant_id=tenant_id, email=email)
        return learners[0] if learners else None
    
    def get_active_learning_goal(self, learner_id: UUID):
        """获取学习者的活跃学习目标"""
        from backend.models import LearningGoal
        goals = self.db.filter_by(LearningGoal, learner_id=learner_id, status="active")
        return goals[0] if goals else None
    
    def get_learner_progress(self, learner_id: UUID) -> Dict[str, Any]:
        """
        获取学习者的学习进度
        
        Returns:
            包含掌握主题、知识缺口等的进度字典
        """
        from backend.models import TopicMastery, KnowledgeGap
        
        masteries = self.db.filter_by(TopicMastery, learner_id=learner_id)
        gaps = self.db.filter_by(KnowledgeGap, learner_id=learner_id)
        
        return {
            "total_mastered": len(masteries),
            "masteries": masteries,
            "total_gaps": len([g for g in gaps if not g.is_resolved()]),
            "gaps": gaps,
            "high_confidence": len([m for m in masteries if m.confidence_level == "high"]),
            "low_confidence": len([m for m in masteries if m.confidence_level == "low"]),
        }


class SessionService:
    """学习会话相关的业务逻辑服务"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def create_session(self, tenant_id: UUID, learner_id: UUID, goal_id: UUID, 
                      teaching_mode_id: Optional[UUID] = None):
        """创建新的学习会话"""
        from backend.models import LearningSession
        from datetime import datetime
        
        session = LearningSession(
            tenant_id=tenant_id,
            learner_id=learner_id,
            goal_id=goal_id,
            teaching_mode_used=teaching_mode_id,
            session_format="teaching"
        )
        return self.db.create(session)
    
    def end_session(self, session_id: UUID, notes: Optional[str] = None,
                   performance_summary: Optional[Dict] = None):
        """结束学习会话"""
        from backend.models import LearningSession
        from datetime import datetime
        
        updates = {"end_time": datetime.now()}
        if notes:
            updates["session_notes"] = notes
        if performance_summary:
            updates["performance_summary"] = performance_summary
        
        return self.db.update_by_id(LearningSession, session_id, **updates)
    
    def add_question(self, session_id: UUID, question_text: str, 
                    topic_id: Optional[UUID] = None,
                    initial_understanding: Optional[str] = None):
        """添加提问记录"""
        from backend.models import QuestionAsked
        
        question = QuestionAsked(
            session_id=session_id,
            topic_id=topic_id,
            question_text=question_text,
            initial_understanding=initial_understanding
        )
        return self.db.create(question)
    
    def add_explanation(self, question_id: UUID, explanation_text: str,
                       teaching_method: str = "socratic",
                       teaching_agent: str = "SocraticTeacher"):
        """添加解释记录"""
        from backend.models import Explanation
        
        explanation = Explanation(
            question_id=question_id,
            agent_explanation=explanation_text,
            teaching_method_used=teaching_method,
            teaching_agent_type=teaching_agent,
            explanation_length_words=len(explanation_text.split())
        )
        return self.db.create(explanation)
    
    def add_comprehension_check(self, explanation_id: UUID, check_question: str,
                               learner_response: Optional[str] = None,
                               assessment: Optional[str] = None):
        """添加理解检查记录"""
        from backend.models import ComprehensionCheck
        
        check = ComprehensionCheck(
            explanation_id=explanation_id,
            question_asked=check_question,
            learner_response=learner_response,
            assessment_result=assessment
        )
        return self.db.create(check)


class ProgressService:
    """进度追踪相关的业务逻辑服务"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def record_topic_mastery(self, learner_id: UUID, topic_id: UUID,
                            confidence_level: str, key_points: Optional[List[str]] = None,
                            session_id: Optional[UUID] = None):
        """记录主题掌握状态"""
        from backend.models import TopicMastery
        from datetime import date
        
        # 检查是否已存在
        existing = self.db.filter_by(TopicMastery, learner_id=learner_id, topic_id=topic_id)
        
        if existing:
            # 更新现有记录
            mastery = existing[0]
            updates = {
                "confidence_level": confidence_level,
                "review_count": mastery.review_count + 1
            }
            if key_points:
                updates["key_points_understood"] = key_points
            if session_id:
                current_sessions = mastery.supporting_session_ids or []
                if session_id not in current_sessions:
                    updates["supporting_session_ids"] = current_sessions + [session_id]
            
            return self.db.update_by_id(TopicMastery, mastery.mastery_id, **updates)
        else:
            # 创建新记录
            mastery = TopicMastery(
                learner_id=learner_id,
                topic_id=topic_id,
                confidence_level=confidence_level,
                key_points_understood=key_points,
                supporting_session_ids=[session_id] if session_id else []
            )
            return self.db.create(mastery)
    
    def record_knowledge_gap(self, learner_id: UUID, topic_id: UUID,
                            severity: str, description: str,
                            session_id: Optional[UUID] = None):
        """记录知识缺口"""
        from backend.models import KnowledgeGap
        
        gap = KnowledgeGap(
            learner_id=learner_id,
            topic_id=topic_id,
            severity_level=severity,
            gap_description=description,
            related_session_ids=[session_id] if session_id else []
        )
        return self.db.create(gap)
    
    def resolve_knowledge_gap(self, gap_id: UUID, resolution_notes: Optional[str] = None):
        """解决知识缺口"""
        from backend.models import KnowledgeGap
        from datetime import date
        
        updates = {
            "resolution_date": date.today(),
            "resolution_notes": resolution_notes
        }
        return self.db.update_by_id(KnowledgeGap, gap_id, **updates)
"""
数据库服务层
提供数据库CRUD操作的封装
"""
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.models.base import Base

T = TypeVar("T", bound=Base)


class DatabaseService:
    """数据库服务类，提供通用的CRUD操作"""
    
    def __init__(self, session: Session):
        """
        初始化数据库服务
        
        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session
    
    def get_by_id(self, model: Type[T], id: UUID) -> Optional[T]:
        """
        根据ID获取单个对象
        
        Args:
            model: 模型类
            id: 对象ID
        
        Returns:
            模型对象或None
        """
        return self.session.get(model, id)
    
    def get_all(self, model: Type[T], limit: int = 100, offset: int = 0) -> List[T]:
        """
        获取所有对象（分页）
        
        Args:
            model: 模型类
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            模型对象列表
        """
        stmt = select(model).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())
    
    def filter_by(self, model: Type[T], **filters) -> List[T]:
        """
        根据条件过滤查询
        
        Args:
            model: 模型类
            **filters: 过滤条件（字段名=值）
        
        Returns:
            符合条件的模型对象列表
        """
        stmt = select(model)
        for key, value in filters.items():
            if hasattr(model, key):
                stmt = stmt.where(getattr(model, key) == value)
        return list(self.session.execute(stmt).scalars().all())
    
    def create(self, obj: T) -> T:
        """
        创建新对象
        
        Args:
            obj: 模型对象
        
        Returns:
            创建后的对象
        """
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj
    
    def update_by_id(self, model: Type[T], id: UUID, **updates) -> Optional[T]:
        """
        根据ID更新对象
        
        Args:
            model: 模型类
            id: 对象ID
            **updates: 要更新的字段
        
        Returns:
            更新后的对象或None
        """
        obj = self.get_by_id(model, id)
        if obj:
            for key, value in updates.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.session.flush()
            self.session.refresh(obj)
        return obj
    
    def delete_by_id(self, model: Type[T], id: UUID) -> bool:
        """
        根据ID删除对象
        
        Args:
            model: 模型类
            id: 对象ID
        
        Returns:
            是否删除成功
        """
        obj = self.get_by_id(model, id)
        if obj:
            self.session.delete(obj)
            self.session.flush()
            return True
        return False
    
    def count(self, model: Type[T], **filters) -> int:
        """
        统计符合条件的对象数量
        
        Args:
            model: 模型类
            **filters: 过滤条件
        
        Returns:
            数量
        """
        stmt = select(model)
        for key, value in filters.items():
            if hasattr(model, key):
                stmt = stmt.where(getattr(model, key) == value)
        return len(list(self.session.execute(stmt).scalars().all()))
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()
    
    def close(self):
        """关闭会话"""
        self.session.close()


class LearnerService:
    """学习者相关的业务逻辑服务"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def get_learner_by_email(self, tenant_id: UUID, email: str):
        """根据邮箱获取学习者"""
        from backend.models import Learner
        learners = self.db.filter_by(Learner, tenant_id=tenant_id, email=email)
        return learners[0] if learners else None
    
    def get_active_learning_goal(self, learner_id: UUID):
        """获取学习者的活跃学习目标"""
        from backend.models import LearningGoal
        goals = self.db.filter_by(LearningGoal, learner_id=learner_id, status="active")
        return goals[0] if goals else None
    
    def get_learner_progress(self, learner_id: UUID) -> Dict[str, Any]:
        """
        获取学习者的学习进度
        
        Returns:
            包含掌握主题、知识缺口等的进度字典
        """
        from backend.models import TopicMastery, KnowledgeGap
        
        masteries = self.db.filter_by(TopicMastery, learner_id=learner_id)
        gaps = self.db.filter_by(KnowledgeGap, learner_id=learner_id)
        
        return {
            "total_mastered": len(masteries),
            "masteries": masteries,
            "total_gaps": len([g for g in gaps if not g.is_resolved()]),
            "gaps": gaps,
            "high_confidence": len([m for m in masteries if m.confidence_level == "high"]),
            "low_confidence": len([m for m in masteries if m.confidence_level == "low"]),
        }


class SessionService:
    """学习会话相关的业务逻辑服务"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def create_session(self, tenant_id: UUID, learner_id: UUID, goal_id: UUID, 
                      teaching_mode_id: Optional[UUID] = None):
        """创建新的学习会话"""
        from backend.models import LearningSession
        from datetime import datetime
        
        session = LearningSession(
            tenant_id=tenant_id,
            learner_id=learner_id,
            goal_id=goal_id,
            teaching_mode_used=teaching_mode_id,
            session_format="teaching"
        )
        return self.db.create(session)
    
    def end_session(self, session_id: UUID, notes: Optional[str] = None,
                   performance_summary: Optional[Dict] = None):
        """结束学习会话"""
        from backend.models import LearningSession
        from datetime import datetime
        
        updates = {"end_time": datetime.now()}
        if notes:
            updates["session_notes"] = notes
        if performance_summary:
            updates["performance_summary"] = performance_summary
        
        return self.db.update_by_id(LearningSession, session_id, **updates)
    
    def add_question(self, session_id: UUID, question_text: str, 
                    topic_id: Optional[UUID] = None,
                    initial_understanding: Optional[str] = None):
        """添加提问记录"""
        from backend.models import QuestionAsked
        
        question = QuestionAsked(
            session_id=session_id,
            topic_id=topic_id,
            question_text=question_text,
            initial_understanding=initial_understanding
        )
        return self.db.create(question)
    
    def add_explanation(self, question_id: UUID, explanation_text: str,
                       teaching_method: str = "socratic",
                       teaching_agent: str = "SocraticTeacher"):
        """添加解释记录"""
        from backend.models import Explanation
        
        explanation = Explanation(
            question_id=question_id,
            agent_explanation=explanation_text,
            teaching_method_used=teaching_method,
            teaching_agent_type=teaching_agent,
            explanation_length_words=len(explanation_text.split())
        )
        return self.db.create(explanation)
    
    def add_comprehension_check(self, explanation_id: UUID, check_question: str,
                               learner_response: Optional[str] = None,
                               assessment: Optional[str] = None):
        """添加理解检查记录"""
        from backend.models import ComprehensionCheck
        
        check = ComprehensionCheck(
            explanation_id=explanation_id,
            question_asked=check_question,
            learner_response=learner_response,
            assessment_result=assessment
        )
        return self.db.create(check)


class ProgressService:
    """进度追踪相关的业务逻辑服务"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def record_topic_mastery(self, learner_id: UUID, topic_id: UUID,
                            confidence_level: str, key_points: Optional[List[str]] = None,
                            session_id: Optional[UUID] = None):
        """记录主题掌握状态"""
        from backend.models import TopicMastery
        from datetime import date
        
        # 检查是否已存在
        existing = self.db.filter_by(TopicMastery, learner_id=learner_id, topic_id=topic_id)
        
        if existing:
            # 更新现有记录
            mastery = existing[0]
            updates = {
                "confidence_level": confidence_level,
                "review_count": mastery.review_count + 1
            }
            if key_points:
                updates["key_points_understood"] = key_points
            if session_id:
                current_sessions = mastery.supporting_session_ids or []
                if session_id not in current_sessions:
                    updates["supporting_session_ids"] = current_sessions + [session_id]
            
            return self.db.update_by_id(TopicMastery, mastery.mastery_id, **updates)
        else:
            # 创建新记录
            mastery = TopicMastery(
                learner_id=learner_id,
                topic_id=topic_id,
                confidence_level=confidence_level,
                key_points_understood=key_points,
                supporting_session_ids=[session_id] if session_id else []
            )
            return self.db.create(mastery)
    
    def record_knowledge_gap(self, learner_id: UUID, topic_id: UUID,
                            severity: str, description: str,
                            session_id: Optional[UUID] = None):
        """记录知识缺口"""
        from backend.models import KnowledgeGap
        
        gap = KnowledgeGap(
            learner_id=learner_id,
            topic_id=topic_id,
            severity_level=severity,
            gap_description=description,
            related_session_ids=[session_id] if session_id else []
        )
        return self.db.create(gap)
    
    def resolve_knowledge_gap(self, gap_id: UUID, resolution_notes: Optional[str] = None):
        """解决知识缺口"""
        from backend.models import KnowledgeGap
        from datetime import date
        
        updates = {
            "resolution_date": date.today(),
            "resolution_notes": resolution_notes
        }
        return self.db.update_by_id(KnowledgeGap, gap_id, **updates)
