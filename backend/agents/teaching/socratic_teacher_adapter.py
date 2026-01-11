"""
苏格拉底教学Agent适配器

该适配器包装现有的SocraticTeacher，使其实现TeachingAgentInterface接口。
采用适配器模式，不修改原有SocraticTeacher的实现，保持阶段一代码的稳定性。
"""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from backend.agents.base.teaching_agent_interface import (
    TeachingAgentInterface,
    TeachingModeInfo,
    TeachingContext
)
from backend.agents.react import (
    create_socratic_teacher_agent,
    invoke_socratic_teacher,
)
from backend.workflows.state import TeachingState
from backend.services.vector_search import VectorSearchService


class SocraticTeacherAdapter(TeachingAgentInterface):
    """
    苏格拉底教学Agent适配器
    
    该适配器包装现有的SocraticTeacher，实现TeachingAgentInterface接口。
    
    职责：
    - 实现TeachingAgentInterface接口
    - 委托核心教学逻辑给内部SocraticTeacher
    - 提供适配度评估和模式元数据
    """
    
    def __init__(
        self,
        session: Session,
        vector_search_service: VectorSearchService
    ):
        """
        初始化苏格拉底教学适配器
        
        Args:
            session: SQLAlchemy数据库会话
            vector_search_service: 向量检索服务
        """
        self.session = session
        self.vector_search = vector_search_service
        
        # 使用SocraticTeacher ReAct Agent
        self.agent = create_socratic_teacher_agent(
            session=session,
            vector_search=vector_search_service,
        )
        
        # 教学模式ID（固定UUID）
        self.mode_id = UUID("11111111-1111-1111-1111-111111111111")
    
    def get_mode_info(self) -> TeachingModeInfo:
        """
        返回苏格拉底教学模式元数据
        
        Returns:
            教学模式元数据对象
        """
        return TeachingModeInfo(
            mode_id=self.mode_id,
            mode_name="socratic",
            mode_type="interactive",
            description="通过提问引导学习者思考，帮助其自己理解概念",
            applicable_scenarios=[
                "concept_learning",
                "critical_thinking",
                "deep_understanding"
            ]
        )
    
    def is_suitable_for(self, context: TeachingContext) -> float:
        """
        计算对当前场景的适配度
        
        苏格拉底教学适合：
        - 初级和中级学习者（需要引导）
        - 需要批判性思维的主题
        - 历史上该模式表现良好的学习者
        
        Args:
            context: 教学场景上下文
        
        Returns:
            适配度评分（0.0-1.0）
        """
        score = 0.0
        
        # 1. 基于学习者水平（权重0.4）
        if context.learner_profile.baseline_level in ["beginner", "intermediate"]:
            score += 0.4
        elif context.learner_profile.baseline_level == "advanced":
            score += 0.2  # 高级学习者也可以用，但不如讲授式
        
        # 2. 基于主题特性（权重0.3）
        if hasattr(context.topic, 'requires_critical_thinking'):
            if context.topic.requires_critical_thinking:
                score += 0.3
        else:
            # 默认假设需要一定的思考
            score += 0.2
        
        # 3. 基于学习历史（权重0.3）
        if "socratic" in context.learning_history.preferred_teaching_modes:
            score += 0.3
        
        return min(score, 1.0)
    
    def teach(self, state: TeachingState) -> TeachingState:
        """
        执行苏格拉底教学逻辑（基于ReAct Agent）
        
        使用SocraticTeacher ReAct Agent按顺序执行：
        - 评估基线
        - 检索相关知识
        - 生成解释
        - 生成理解检查问题
        """
        # 1. 评估知识基线
        baseline_result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="evaluate_baseline",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            initial_understanding=state.initial_understanding,
        )
        if baseline_result.get("result"):
            res = baseline_result["result"]
            state.baseline_level = res.get("level")
            state.baseline_assessment = res.get("assessment")
        
        # 2. 检索相关知识
        retrieve_result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="retrieve_knowledge",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            current_topic_id=state.current_topic_id,
        )
        if retrieve_result.get("result"):
            state.retrieved_concepts = retrieve_result["result"].get("concepts", [])
        
        # 3. 生成解释
        explanation_result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="generate_explanation",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            baseline_level=state.baseline_level,
            retrieved_concepts=state.retrieved_concepts,
            learner_preferences=state.learner_preferences,
        )
        if explanation_result.get("result"):
            state.explanation = explanation_result["result"].get("explanation")
        
        # 4. 生成理解检查问题
        questions_result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="generate_questions",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            explanation=state.explanation,
            baseline_level=state.baseline_level,
        )
        if questions_result.get("result"):
            state.comprehension_questions = questions_result["result"]
        
        state.teaching_method = "socratic"
        
        return state
    
    def generate_explanation(self, state: TeachingState) -> str:
        """
        生成苏格拉底式解释
        
        特点：
        - 简明清晰（约200字）
        - 包含引导性问题
        - 鼓励批判性思考
        
        Args:
            state: 当前教学状态
        
        Returns:
            解释文本
        """
        result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="generate_explanation",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            baseline_level=state.baseline_level,
            retrieved_concepts=state.retrieved_concepts,
            learner_preferences=state.learner_preferences,
        )
        if result.get("result"):
            state.explanation = result["result"].get("explanation")
        return state.explanation
    
    def generate_check_questions(self, state: TeachingState) -> List[str]:
        """
        生成理解检查问题
        
        特点：
        - 1-2个开放式问题
        - 考察真实理解
        - 鼓励用自己的话解释
        
        Args:
            state: 当前教学状态
        
        Returns:
            问题文本列表
        """
        result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="generate_questions",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            explanation=state.explanation,
            baseline_level=state.baseline_level,
        )
        if result.get("result"):
            state.comprehension_questions = result["result"]
        return [q.question_text for q in state.comprehension_questions]
    
    def adaptive_follow_up(self, state: TeachingState) -> TeachingState:
        """
        自适应跟进
        
        当学习者部分理解时，选择合适的跟进策略。
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态
        """
        result = invoke_socratic_teacher(
            agent=self.agent,
            task_type="adaptive_followup",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            previous_explanation=state.explanation,
            learner_response=state.learner_response,
            misunderstandings=state.misunderstandings,
        )
        if result.get("result") and result["result"].get("followup_content"):
            state.explanation = result["result"]["followup_content"]
        return state


def create_socratic_teacher_adapter(
    session: Session,
    vector_search_service: VectorSearchService
) -> SocraticTeacherAdapter:
    """
    工厂函数：创建苏格拉底教学适配器实例
    
    Args:
        session: SQLAlchemy数据库会话
        vector_search_service: 向量检索服务
    
    Returns:
        SocraticTeacherAdapter实例
    """
    return SocraticTeacherAdapter(session, vector_search_service)
