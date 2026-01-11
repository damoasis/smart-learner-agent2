"""
讲授式教学Agent

该Agent实现系统化的知识讲解，适合快速建立知识体系。
"""

from typing import List, Optional
from uuid import UUID
import json

from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.agents.base.teaching_agent_interface import (
    TeachingAgentInterface,
    TeachingModeInfo,
    TeachingContext
)
from backend.workflows.state import TeachingState, ComprehensionQuestion
from backend.services.vector_search import VectorSearchService


class LectureTeachingAgent(TeachingAgentInterface):
    """
    讲授式教学Agent
    
    教学理念：
    - 系统化知识讲解
    - 从概览到详细的递进式结构
    - 明确的知识框架
    - 适合快速掌握知识体系
    
    与苏格拉底式的区别：
    - 互动性：低（主要讲解）vs 高（多次提问）
    - 内容结构：线性递进 vs 发散式探索
    - 适用场景：知识体系建立 vs 概念理解
    - 学习速度：较快（广度）vs 较慢（深入）
    """
    
    def __init__(
        self,
        session: Session,
        vector_search_service: VectorSearchService,
        llm: Optional[ChatOpenAI] = None,
        explanation_max_length: int = 500,
        num_comprehension_questions: int = 4
    ):
        """
        初始化讲授式教学Agent
        
        Args:
            session: SQLAlchemy数据库会话
            vector_search_service: 向量检索服务
            llm: LangChain ChatOpenAI实例，如果为None则使用默认配置
            explanation_max_length: 解释最大字数（讲授式更长）
            num_comprehension_questions: 理解检查问题数量（讲授式更多）
        """
        self.session = session
        self.vector_search = vector_search_service
        self.explanation_max_length = explanation_max_length
        self.num_comprehension_questions = num_comprehension_questions
        
        # 教学模式ID（固定UUID）
        self.mode_id = UUID("22222222-2222-2222-2222-222222222222")
        
        if llm is None:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
            temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "800"))
            
            self.llm = ChatOpenAI(
                openai_api_key=api_key,
                base_url=base_url,
                model_name=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            self.llm = llm
        
        # 初始化Prompt模板
        self._init_prompts()
    
    def _init_prompts(self):
        """初始化讲授式Prompt模板"""
        
        # 解释生成Prompt（讲授式风格）
        self.explanation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业讲师，需要系统化地讲解知识。

请按以下结构组织讲解（总字数约{max_length}字）：

1. **概述**（50字）
   - 简明介绍本次讲解的核心内容

2. **知识框架**（50-80字）
   - 列出3-5个核心要点
   - 清晰的层次结构

3. **详细讲解**（250-350字）
   - 逐个要点展开说明
   - 每个要点包含：定义 + 解释 + 具体示例
   - 使用清晰的逻辑连接

4. **关键知识点总结**（50字）
   - 总结必须记住的核心内容
   - 强调重点和难点

教学原则：
- 逻辑清晰、层次分明
- 语言准确、表达规范
- 示例具体、易于理解
- 适合学习者水平：{baseline_level}

注意：这是讲授式教学，重在系统讲解，而非提问引导。"""),
            ("user", """学习者问题：{question}

相关概念信息：
{concepts_info}

学习者水平：{baseline_level}

请生成系统化的讲解内容。""")
        ])
        
        # 理解检查问题生成Prompt（讲授式风格）
        self.comprehension_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位教育评估专家。你需要生成{num_questions}个检查问题，
用于检验学习者是否掌握了刚才讲解的知识。

问题设计要求：
1. 混合题型：
   - 2个开放式问题（考察理解和表达）
   - 2个应用题（考察实际运用）
2. 覆盖所有核心要点
3. 难度递增（从简单到复杂）
4. 符合学习者水平

请返回以下JSON格式：
{{
  "questions": [
    {{
      "question_text": "问题内容",
      "question_type": "open/application",
      "expected_key_points": ["关键点1", "关键点2"],
      "difficulty": "easy/medium/hard"
    }}
  ]
}}"""),
            ("user", """刚才讲解的内容：
{explanation}

学习者水平：{baseline_level}

请生成{num_questions}个检查问题（混合题型）。""")
        ])
    
    def get_mode_info(self) -> TeachingModeInfo:
        """
        返回讲授式教学模式元数据
        
        Returns:
            教学模式元数据对象
        """
        return TeachingModeInfo(
            mode_id=self.mode_id,
            mode_name="lecture",
            mode_type="passive",
            description="系统化知识讲解，从概览到详细的递进式结构，适合快速建立知识体系",
            applicable_scenarios=[
                "knowledge_system_building",
                "fast_learning",
                "new_topic_introduction",
                "structured_learning"
            ]
        )
    
    def is_suitable_for(self, context: TeachingContext) -> float:
        """
        计算对当前场景的适配度
        
        讲授式教学适合：
        - 新知识导入（未掌握的主题）
        - 系统性学习（复杂结构的主题）
        - 高级学习者（能快速接受信息）
        
        Args:
            context: 教学场景上下文
        
        Returns:
            适配度评分（0.0-1.0）
        """
        score = 0.0
        
        # 1. 基于主题掌握情况（权重0.4）
        if context.topic.topic_id not in context.learner_profile.mastered_topics:
            # 新知识导入，讲授式很适合
            score += 0.4
        else:
            # 已掌握的知识，讲授式不太适合（可能需要深入探讨）
            score += 0.1
        
        # 2. 基于主题结构复杂度（权重0.3）
        # 假设有复杂结构的主题更适合系统化讲解
        if hasattr(context.topic, 'has_complex_structure'):
            if context.topic.has_complex_structure:
                score += 0.3
        else:
            # 默认假设有一定复杂度
            score += 0.2
        
        # 3. 基于学习者水平（权重0.3）
        if context.learner_profile.baseline_level == "advanced":
            # 高级学习者能快速接受系统化讲解
            score += 0.3
        elif context.learner_profile.baseline_level == "intermediate":
            score += 0.2
        else:
            # 初学者可能更适合引导式学习
            score += 0.1
        
        return min(score, 1.0)
    
    def teach(self, state: TeachingState) -> TeachingState:
        """
        执行讲授式教学逻辑
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态
        """
        # 1. 检索相关知识（复用向量检索）
        state = self._retrieve_knowledge(state)
        
        # 2. 生成讲授式解释
        explanation = self.generate_explanation(state)
        state.explanation = explanation
        
        # 3. 生成理解检查问题
        questions = self.generate_check_questions(state)
        state.comprehension_questions = [
            ComprehensionQuestion(
                question_text=q,
                expected_key_points=[]
            ) for q in questions
        ]
        
        # 设置教学方法
        state.teaching_method = "lecture"
        
        return state
    
    def _retrieve_knowledge(self, state: TeachingState) -> TeachingState:
        """
        检索相关知识
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态
        """
        from backend.workflows.state import RetrievedConcept
        
        question = state.question_text or ""
        tenant_id = state.tenant_id
        
        # 使用向量检索服务搜索相关概念
        results = self.vector_search.search_similar_concepts(
            query_text=question,
            tenant_id=tenant_id,
            top_k=5,
            similarity_threshold=0.7,
            topic_id=state.current_topic_id
        )
        
        # 转换为RetrievedConcept对象
        retrieved_concepts = []
        for concept, similarity in results:
            retrieved_concepts.append(RetrievedConcept(
                concept_id=concept.concept_id,
                concept_name=concept.concept_name,
                explanation=concept.explanation,
                formulas=concept.formulas,
                rules=concept.rules,
                similarity_score=similarity
            ))
        
        state.retrieved_concepts = retrieved_concepts
        return state
    
    def generate_explanation(self, state: TeachingState) -> str:
        """
        生成讲授式解释
        
        特点：
        - 结构化（概述→框架→详细讲解→总结）
        - 长度更长（300-500字）
        - 系统化、逻辑清晰
        
        Args:
            state: 当前教学状态
        
        Returns:
            解释文本
        """
        question = state.question_text or ""
        baseline_level = state.baseline_level or "intermediate"
        
        # 构建概念信息文本
        concepts_info = self._format_concepts_info(state.retrieved_concepts)
        
        # 调用LLM生成讲授式解释
        prompt = self.explanation_prompt.format_messages(
            question=question,
            baseline_level=baseline_level,
            concepts_info=concepts_info,
            max_length=self.explanation_max_length
        )
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def generate_check_questions(self, state: TeachingState) -> List[str]:
        """
        生成理解检查问题
        
        特点：
        - 3-5个问题
        - 混合题型（开放式 + 应用题）
        - 覆盖所有核心要点
        - 难度递增
        
        Args:
            state: 当前教学状态
        
        Returns:
            问题文本列表
        """
        explanation = state.explanation or ""
        baseline_level = state.baseline_level or "intermediate"
        
        # 调用LLM生成问题
        prompt = self.comprehension_prompt.format_messages(
            explanation=explanation,
            baseline_level=baseline_level,
            num_questions=self.num_comprehension_questions
        )
        
        response = self.llm.invoke(prompt)
        
        # 解析响应
        try:
            result = json.loads(response.content)
            questions = result.get("questions", [])
            
            question_texts = []
            for q in questions:
                question_text = q.get("question_text", "")
                question_type = q.get("question_type", "")
                # 可以添加题型标识
                if question_type == "application":
                    question_text = f"[应用题] {question_text}"
                question_texts.append(question_text)
            
            return question_texts if question_texts else self._generate_fallback_questions()
        except Exception as e:
            # 如果解析失败，生成默认问题
            return self._generate_fallback_questions()
    
    def _generate_fallback_questions(self) -> List[str]:
        """生成备用问题（当LLM解析失败时）"""
        return [
            "请用自己的话总结刚才学到的核心知识点。",
            "请举一个实际应用这些知识的例子。",
            "这些知识中哪个部分你觉得最重要？为什么？",
            "如果要向他人解释这个概念，你会怎么说？"
        ]
    
    def _format_concepts_info(self, concepts) -> str:
        """
        格式化概念信息为文本
        
        Args:
            concepts: 检索到的概念列表
        
        Returns:
            格式化的概念信息文本
        """
        if not concepts:
            return "未检索到相关概念"
        
        info_parts = []
        for i, concept in enumerate(concepts, 1):
            parts = [f"{i}. {concept.concept_name}"]
            
            if concept.explanation:
                parts.append(f"   解释：{concept.explanation}")
            
            if concept.formulas:
                parts.append(f"   公式：{concept.formulas}")
            
            if concept.rules:
                parts.append(f"   规则：{concept.rules}")
            
            parts.append(f"   相似度：{concept.similarity_score:.2f}")
            
            info_parts.append("\n".join(parts))
        
        return "\n\n".join(info_parts)


def create_lecture_teaching_agent(
    session: Session,
    vector_search_service: VectorSearchService,
    llm: Optional[ChatOpenAI] = None
) -> LectureTeachingAgent:
    """
    工厂函数：创建讲授式教学Agent实例
    
    Args:
        session: SQLAlchemy数据库会话
        vector_search_service: 向量检索服务
        llm: LangChain ChatOpenAI实例（可选）
    
    Returns:
        LectureTeachingAgent实例
    """
    return LectureTeachingAgent(session, vector_search_service, llm)
