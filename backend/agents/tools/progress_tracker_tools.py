"""
ProgressTracker工具集 - 进度追踪相关工具函数
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from langchain_core.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from backend.models.session import (
    TopicMastery, KnowledgeGap, LearningSession,
    QuestionAsked, Explanation, ComprehensionCheck
)
from backend.models.topic import Topic, TopicDependency
from backend.workflows.state import TeachingState


@tool
def query_mastery_records(
    learner_id: str,
    tenant_id: str,
    session: Any,
    time_range_days: Optional[int] = None
) -> List[Dict[str, Any]]:
    """查询掌握记录"""
    from uuid import UUID as U
    
    query = select(TopicMastery).where(
        TopicMastery.learner_id == U(learner_id),
        TopicMastery.tenant_id == U(tenant_id)
    )
    
    if time_range_days:
        start = datetime.now() - timedelta(days=time_range_days)
        query = query.where(TopicMastery.created_at >= start)
    
    return [{
        "mastery_id": str(m.mastery_id),
        "topic_id": str(m.topic_id),
        "confidence_level": m.confidence_level,
        "key_points_understood": m.key_points_understood or [],
        "last_reviewed_at": m.last_reviewed_at.isoformat() if m.last_reviewed_at else None
    } for m in session.execute(query).scalars().all()]


@tool
def query_knowledge_gaps(
    learner_id: str,
    tenant_id: str,
    session: Any
) -> List[Dict[str, Any]]:
    """查询知识缺口"""
    from uuid import UUID as U
    
    query = select(KnowledgeGap).where(
        KnowledgeGap.learner_id == U(learner_id),
        KnowledgeGap.tenant_id == U(tenant_id),
        KnowledgeGap.resolution_date.is_(None)
    )
    
    return [{
        "gap_id": str(g.gap_id),
        "topic_id": str(g.topic_id),
        "severity_level": g.severity_level,
        "gap_description": g.gap_description
    } for g in session.execute(query).scalars().all()]


@tool
def calculate_efficiency_metrics(
    mastery_records: List[Dict], gaps: List[Dict]
) -> Dict[str, Any]:
    """计算学习效率指标"""
    avg_days = 0
    if mastery_records:
        total = sum(3 for _ in mastery_records)  # 简化
        avg_days = total / len(mastery_records)
    
    return {
        "average_mastery_time_days": round(avg_days, 2),
        "retry_distribution": {
            "0-1": max(0, len(mastery_records) - len(gaps)),
            "2-3": len([g for g in gaps if g["severity_level"] in ["low", "medium"]]),
            "4+": len([g for g in gaps if g["severity_level"] in ["high"]])
        },
        "learning_pace": "moderate",
        "total_mastered": len(mastery_records)
    }


@tool
def recommend_review_topics(
    mastery_records: List[Dict], session: Any, max_items: int = 5
) -> List[Dict]:
    """推荐复习主题"""
    intervals = {"low": 1, "medium": 2, "medium_high": 3, "high": 7}
    recs = []
    now = datetime.now()
    
    for r in mastery_records[:max_items]:
        conf = r.get("confidence_level", "medium")
        last = r.get("last_reviewed_at")
        if not last:
            continue
        days = (now - datetime.fromisoformat(last)).days
        if days >= intervals.get(conf, 2):
            recs.append({
                "topic_id": r["topic_id"],
                "days_since_review": days,
                "urgency_score": 0.8
            })
    
    return recs


@tool
def recommend_next_topics(
    learner_id: str, tenant_id: str, session: Any, 
    mastered_ids: List[str], max_recs: int = 3
) -> List[Dict]:
    """推荐下一步主题"""
    from uuid import UUID as U
    
    mastered = set(U(tid) for tid in mastered_ids)
    query = select(Topic).where(Topic.tenant_id == U(tenant_id))
    topics = session.execute(query).scalars().all()
    
    recs = []
    for t in topics:
        if t.topic_id not in mastered:
            recs.append({
                "topic_id": str(t.topic_id),
                "topic_name": t.topic_name,
                "recommendation_score": 0.7
            })
    
    return recs[:max_recs]


@tool
def update_mastery_state(
    learner_id: str,
    tenant_id: str,
    session: Any,
    topic_id: str,
    confidence_level: str = "medium",
    key_points: Optional[List[str]] = None
) -> Dict[str, Any]:
    """更新或创建主题掌握状态记录"""
    from uuid import UUID as U
    
    learner_uuid = U(learner_id)
    topic_uuid = U(topic_id)
    tenant_uuid = U(tenant_id)
    key_points = key_points or []
    
    # 查询是否已存在该主题的掌握记录
    existing_mastery = session.execute(
        select(TopicMastery).where(
            TopicMastery.learner_id == learner_uuid,
            TopicMastery.topic_id == topic_uuid,
            TopicMastery.tenant_id == tenant_uuid
        )
    ).scalar_one_or_none()
    
    if existing_mastery:
        # 更新现有记录
        existing_mastery.confidence_level = confidence_level
        existing_mastery.key_points_understood = key_points
        existing_mastery.last_reviewed_at = datetime.now()
        existing_mastery.updated_at = datetime.now()
        mastery_id = str(existing_mastery.mastery_id)
    else:
        # 创建新记录
        mastery_id = uuid4()
        mastery = TopicMastery(
            mastery_id=mastery_id,
            tenant_id=tenant_uuid,
            learner_id=learner_uuid,
            topic_id=topic_uuid,
            confidence_level=confidence_level,
            key_points_understood=key_points,
            last_reviewed_at=datetime.now()
        )
        session.add(mastery)
        mastery_id = str(mastery_id)
    
    session.flush()
    
    return {
        "success": True,
        "mastery_id": mastery_id,
        "message": "Mastery updated successfully"
    }


@tool
def record_knowledge_gap(
    learner_id: str,
    tenant_id: str,
    session: Any,
    topic_id: str,
    gap_description: str,
    severity_level: str = "medium",
    retry_count: int = 0
) -> Dict[str, Any]:
    """记录知识缺口"""
    from uuid import UUID as U
    
    learner_uuid = U(learner_id)
    topic_uuid = U(topic_id)
    tenant_uuid = U(tenant_id)
    
    # 查询是否已存在该主题的知识缺口
    existing_gap = session.execute(
        select(KnowledgeGap).where(
            KnowledgeGap.learner_id == learner_uuid,
            KnowledgeGap.topic_id == topic_uuid,
            KnowledgeGap.tenant_id == tenant_uuid,
            KnowledgeGap.resolution_date.is_(None)
        )
    ).scalar_one_or_none()
    
    if existing_gap:
        # 更新现有缺口
        existing_gap.gap_description = gap_description
        existing_gap.severity_level = severity_level
        existing_gap.updated_at = datetime.now()
        gap_id = str(existing_gap.gap_id)
    else:
        # 创建新缺口记录
        gap_id = uuid4()
        gap = KnowledgeGap(
            gap_id=gap_id,
            tenant_id=tenant_uuid,
            learner_id=learner_uuid,
            topic_id=topic_uuid,
            gap_description=gap_description,
            severity_level=severity_level,
            identified_date=datetime.now()
        )
        session.add(gap)
        gap_id = str(gap_id)
    
    session.flush()
    
    return {
        "success": True,
        "gap_id": gap_id,
        "message": "Knowledge gap recorded successfully"
    }


@tool
def save_question_record(
    session: Any,
    session_id: str,
    question_text: str,
    initial_understanding: Optional[str] = None
) -> Dict[str, Any]:
    """保存问题记录"""
    from uuid import UUID as U
    
    question_id = uuid4()
    question = QuestionAsked(
        question_id=question_id,
        session_id=U(session_id),
        question_text=question_text,
        initial_understanding=initial_understanding,
    )
    session.add(question)
    session.flush()
    
    return {
        "success": True,
        "question_id": str(question_id),
        "message": "Question saved successfully"
    }


@tool
def save_explanation_record(
    session: Any,
    question_id: str,
    explanation_text: str,
    teaching_method: Optional[str] = None
) -> Dict[str, Any]:
    """保存解释记录"""
    from uuid import UUID as U
    
    explanation_id = uuid4()
    explanation = Explanation(
        explanation_id=explanation_id,
        question_id=U(question_id),
        agent_explanation=explanation_text,
        teaching_method_used=teaching_method,
        clarity_rating=None
    )
    session.add(explanation)
    session.flush()
    
    return {
        "success": True,
        "explanation_id": str(explanation_id),
        "message": "Explanation saved successfully"
    }


@tool
def save_comprehension_check(
    session: Any,
    explanation_id: str,
    question_asked: str,
    learner_response: str,
    is_correct: bool,
    assessment_result: Optional[str] = None
) -> Dict[str, Any]:
    """保存理解检查记录"""
    from uuid import UUID as U
    
    check_id = uuid4()
    check = ComprehensionCheck(
        check_id=check_id,
        explanation_id=U(explanation_id),
        question_asked=question_asked,
        learner_response=learner_response,
        is_correct=is_correct,
        assessment_result=assessment_result,
        timestamp=datetime.now()
    )
    session.add(check)
    session.flush()
    
    return {
        "success": True,
        "check_id": str(check_id),
        "message": "Comprehension check saved successfully"
    }


@tool
def generate_progress_summary(
    learner_id: str,
    tenant_id: str,
    session: Any
) -> Dict[str, Any]:
    """生成学习者的总体进度摘要"""
    from uuid import UUID as U
    
    learner_uuid = U(learner_id)
    tenant_uuid = U(tenant_id)
    
    # 统计掌握的主题
    mastered_topics_query = select(TopicMastery).where(
        TopicMastery.learner_id == learner_uuid,
        TopicMastery.tenant_id == tenant_uuid
    )
    mastered_topics = session.execute(mastered_topics_query).scalars().all()
    
    # 按信心等级分组
    mastery_by_level = {
        "high": [],
        "medium_high": [],
        "medium": [],
        "low": []
    }
    
    for mastery in mastered_topics:
        level = mastery.confidence_level
        topic = session.get(Topic, mastery.topic_id)
        if topic:
            mastery_by_level[level].append({
                "topic_id": str(mastery.topic_id),
                "topic_name": topic.topic_name,
                "key_points": mastery.key_points_understood or [],
                "last_reviewed": mastery.last_reviewed_at.isoformat() if mastery.last_reviewed_at else None
            })
    
    # 统计知识缺口
    gaps_query = select(KnowledgeGap).where(
        KnowledgeGap.learner_id == learner_uuid,
        KnowledgeGap.tenant_id == tenant_uuid,
        KnowledgeGap.resolution_date.is_(None)
    ).order_by(KnowledgeGap.severity_level.desc())
    
    knowledge_gaps = session.execute(gaps_query).scalars().all()
    
    gaps_list = []
    for gap in knowledge_gaps:
        topic = session.get(Topic, gap.topic_id)
        if topic:
            gaps_list.append({
                "gap_id": str(gap.gap_id),
                "topic_id": str(gap.topic_id),
                "topic_name": topic.topic_name,
                "description": gap.gap_description,
                "severity_level": gap.severity_level,
                "identified_date": gap.identified_date.isoformat()
            })
    
    # 计算总体统计
    total_mastered = len(mastered_topics)
    high_confidence = len(mastery_by_level["high"])
    medium_high_confidence = len(mastery_by_level["medium_high"])
    total_gaps = len(knowledge_gaps)
    
    return {
        "learner_id": learner_id,
        "total_mastered_topics": total_mastered,
        "high_confidence_topics": high_confidence,
        "medium_high_confidence_topics": medium_high_confidence,
        "total_knowledge_gaps": total_gaps,
        "mastery_by_confidence_level": mastery_by_level,
        "knowledge_gaps": gaps_list,
        "generated_at": datetime.now().isoformat()
    }


@tool
def resolve_knowledge_gap(
    session: Any,
    gap_id: str,
    resolution_notes: Optional[str] = None
) -> Dict[str, Any]:
    """标记知识缺口为已解决"""
    from uuid import UUID as U
    
    gap = session.get(KnowledgeGap, U(gap_id))
    if not gap:
        return {
            "success": False,
            "message": "Knowledge gap not found"
        }
    
    gap.resolution_date = datetime.now()
    gap.resolution_notes = resolution_notes
    gap.updated_at = datetime.now()
    
    session.flush()
    
    return {
        "success": True,
        "gap_id": gap_id,
        "message": "Knowledge gap resolved successfully"
    }
