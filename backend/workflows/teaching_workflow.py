"""
Teaching workflow (主Agent工作流)

基于 LangGraph 1.x 的主教学工作流,负责在 5 个 ReAct 子Agent 之间编排:
- SocraticTeacher: 苏格拉底教学/讲解
- KnowledgeAssessor: 理解评估
- ProgressTracker: 进度追踪与分析
- ContentValidator: 内容验证
- MnemonicGenerator: 记忆辅助

主工作流本身不直接调用工具函数,而是通过各子Agent的 create_**_agent / invoke_**
进行调用,并在图中定义节点和条件路由。
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.workflows.state import TeachingState, create_initial_state
from backend.services.vector_search import VectorSearchService
from backend.agents.react import (
    create_socratic_teacher_agent,
    invoke_socratic_teacher,
    create_knowledge_assessor_agent,
    invoke_knowledge_assessor,
    create_progress_tracker_agent,
    invoke_progress_tracker,
    create_content_validator_agent,
    invoke_content_validator,
    create_mnemonic_generator_agent,
    invoke_mnemonic_generator,
)


class SocraticTeachingWorkflow:
    """主教学工作流

    - 通过意图识别节点将请求路由到不同子Agent
    - 对于学习类请求,走苏格拉底教学主路径(评估基线→检索→验证→解释→记忆辅助→理解检查)
    - 对于进度/复习/练习等请求,调用对应 ReAct 子Agent 完成任务
    """

    def __init__(
        self,
        session: Session,
        vector_search: VectorSearchService,
        llm: Optional[ChatOpenAI] = None,
    ) -> None:
        self.session = session
        self.vector_search = vector_search

        # 创建 LLM 实例
        if llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

            self.llm = ChatOpenAI(
                openai_api_key=api_key,
                base_url=base_url,
                model_name=model,
                temperature=0.7,
            )
        else:
            self.llm = llm

        # ===== 子Agent 实例 =====
        # 通过 create_**_agent 创建 ReAct 子Agent,供各节点调用
        self.socratic_agent = create_socratic_teacher_agent(
            session=session,
            vector_search=vector_search,
            llm=self.llm,
        )
        self.assessor_agent = create_knowledge_assessor_agent(
            session=session,
            llm=self.llm,
        )
        self.progress_agent = create_progress_tracker_agent(
            session=session,
            llm=self.llm,
        )
        self.validator_agent = create_content_validator_agent(
            session=session,
            llm=self.llm,
        )
        self.mnemonic_agent = create_mnemonic_generator_agent(
            session=session,
            llm=self.llm,
        )

        # 构建主工作流图
        self.workflow = self._build_workflow()

    # ====================================================================
    # 图结构定义
    # ====================================================================

    def _build_workflow(self) -> Any:
        """构建 LangGraph 工作流图并编译"""
        graph = StateGraph(TeachingState)

        # --- 节点注册 ---
        graph.add_node("initialize", self._initialize_node)
        graph.add_node("detect_intent", self._detect_intent_node)

        # 学习/讲解主路径节点(使用 Socratic / Mnemonic / ContentValidator / Assessor)
        # graph.add_node("evaluate_baseline", self._evaluate_baseline_node)
        # graph.add_node("retrieve_knowledge", self._retrieve_knowledge_node)
        # graph.add_node("validate_content", self._validate_content_node)
        # graph.add_node("generate_explanation", self._generate_explanation_node)
        # graph.add_node("generate_mnemonic", self._generate_mnemonic_node)
        # graph.add_node("create_comprehension_check", self._create_comprehension_check_node)
        # graph.add_node("wait_for_response", self._wait_for_response_node)
        # graph.add_node("assess_understanding", self._assess_understanding_node)
        # graph.add_node("adaptive_followup", self._adaptive_followup_node)
        # graph.add_node("update_progress", self._update_progress_node)
        # graph.add_node("record_gap", self._record_gap_node)

        # # 其他意图入口节点
        # graph.add_node("progress_entry", self._progress_entry_node)
        # graph.add_node("review_entry", self._review_entry_node)
        # graph.add_node("assessment_entry", self._assessment_entry_node)
        # graph.add_node("other_entry", self._other_entry_node)

        graph.add_node("finalize", self._finalize_node)

        # --- 边与条件路由 ---
        graph.set_entry_point("initialize")

        # 初始化后先做意图识别
        graph.add_edge("initialize", "detect_intent")

        # 根据意图路由到不同子Agent
        graph.add_conditional_edges(
            "detect_intent",
            self._route_by_intent,
            {
                "learn": "evaluate_baseline",      # 学习/讲解主路径
                "practice": "assessment_entry",    # 练习/评估
                "progress": "progress_entry",      # 查看进度
                "review": "review_entry",          # 复习推荐
                "other": "other_entry",            # 兜底: 回到学习路径
            },
        )

        # --- 学习主路径 ---
        graph.add_edge("evaluate_baseline", "retrieve_knowledge")

        # 是否需要验证内容
        graph.add_conditional_edges(
            "retrieve_knowledge",
            self._should_validate_content,
            {
                "validate": "validate_content",
                "skip": "generate_explanation",
            },
        )

        graph.add_edge("validate_content", "generate_explanation")

        # 是否需要记忆辅助
        graph.add_conditional_edges(
            "generate_explanation",
            self._should_generate_mnemonic,
            {
                "generate": "generate_mnemonic",
                "skip": "create_comprehension_check",
            },
        )

        graph.add_edge("generate_mnemonic", "create_comprehension_check")
        graph.add_edge("create_comprehension_check", "wait_for_response")
        graph.add_edge("wait_for_response", "assess_understanding")

        # 评估后的路由: 继续/自适应跟进/重试/记录缺口
        graph.add_conditional_edges(
            "assess_understanding",
            self._route_after_assessment,
            {
                "continue": "update_progress",
                "adaptive_followup": "adaptive_followup",
                "retry": "generate_explanation",
                "record_gap": "record_gap",
            },
        )

        graph.add_edge("adaptive_followup", "create_comprehension_check")
        graph.add_edge("update_progress", "finalize")
        graph.add_edge("record_gap", "finalize")

        # 其他入口节点统一在完成后结束
        graph.add_edge("progress_entry", "finalize")
        graph.add_edge("review_entry", "finalize")
        graph.add_edge("assessment_entry", "finalize")
        graph.add_edge("other_entry", "finalize")
        graph.add_edge("finalize", END)


        compiled_graph = graph.compile()
        compiled_graph.getgraph().print_ascii()

        return compiled_graph

    # ====================================================================
    # 节点实现
    # ====================================================================

    def _initialize_node(self, state: TeachingState) -> Dict[str, Any]:
        """初始化节点: 准备会话上下文"""
        now = datetime.now()
        return {
            "workflow_stage": "initialized",
            "timestamp": now,
        }

    # ---- 意图识别 & 路由 ------------------------------------------------

    def _detect_intent_node(self, state: TeachingState) -> Dict[str, Any]:
        """意图识别节点

        根据 question_text 将请求粗分为:
        - learn: 学习/讲解
        - practice: 做题/练习/只评估
        - progress: 查看整体进度
        - review: 复习薄弱点
        """
        question = state.question_text or ""
        if not question:
            return {"intent": "learn", "workflow_stage": "intent_detected"}

        system_prompt = (
            "你是意图识别助手。请根据用户输入判断其主要意图,"
            "并只输出一个单词: learn / practice / progress / review。\n"
            "- learn: 希望学习或讲解某个概念/问题;\n"
            "- practice: 希望做题、练习或只要评估;\n"
            "- progress: 希望查看整体学习进度或统计;\n"
            "- review: 希望复习薄弱点或需要复习建议。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        try:
            resp = self.llm.invoke(messages)
            raw = (resp.content or "").strip().lower()
        except Exception:
            raw = "learn"

        if raw not in {"learn", "practice", "progress", "review"}:
            raw = "learn"

        return {
            "intent": raw,
            "workflow_stage": "intent_detected",
        }

    def _route_by_intent(self, state: TeachingState) -> Literal[
        "learn", "practice", "progress", "review", "other"
    ]:
        intent = state.intent or "learn"
        if intent in {"learn", "practice", "progress", "review"}:
            return intent  # 与 add_conditional_edges 的 key 对应
        return "other"

    # ---- 学习主路径: 使用 Socratic / ContentValidator / Mnemonic ---------

    def _evaluate_baseline_node(self, state: TeachingState) -> Dict[str, Any]:
        """评估基线: 调用 SocraticTeacher ReAct Agent 的 evaluate_baseline 任务"""
        result = invoke_socratic_teacher(
            agent=self.socratic_agent,
            task_type="evaluate_baseline",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            initial_understanding=state.initial_understanding,
        )
        s = result.get("state", {})
        return {
            "baseline_level": s.get("baseline_level"),
            "baseline_assessment": s.get("baseline_assessment"),
            "workflow_stage": "baseline_evaluated",
        }

    def _retrieve_knowledge_node(self, state: TeachingState) -> Dict[str, Any]:
        """知识检索: 调用 SocraticTeacher 的 retrieve_knowledge 任务"""
        result = invoke_socratic_teacher(
            agent=self.socratic_agent,
            task_type="retrieve_knowledge",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            current_topic_id=state.current_topic_id,
        )
        s = result.get("state", {})
        concepts = s.get("retrieved_concepts", [])
        needs_validation = self._check_needs_validation(state, concepts)
        return {
            "retrieved_concepts": concepts,
            "needs_validation": needs_validation,
            "workflow_stage": "knowledge_retrieved",
        }

    def _validate_content_node(self, state: TeachingState) -> Dict[str, Any]:
        """内容验证: 调用 ContentValidator ReAct Agent

        - skip_validation 为 True 或 explanation 为空时直接跳过
        - 否则触发 validate_content 任务,并返回验证结果和来源
        """
        if state.skip_validation or not state.explanation:
            return {"workflow_stage": "validation_skipped"}

        result = invoke_content_validator(
            agent=self.validator_agent,
            task_type="validate_content",
            explanation=state.explanation or "",
            concept_name=state.question_text or "",
            tenant_id=str(state.tenant_id),
            concept_id=str(state.current_topic_id) if state.current_topic_id else "",
        )
        s = result.get("state", {})
        return {
            "validation_result": s.get("validation_result"),
            "verified_sources": s.get("verification_sources", []),
            "workflow_stage": "content_validated",
        }

    def _generate_explanation_node(self, state: TeachingState) -> Dict[str, Any]:
        """生成解释: 调用 SocraticTeacher 的 generate_explanation 任务"""
        result = invoke_socratic_teacher(
            agent=self.socratic_agent,
            task_type="generate_explanation",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            baseline_level=state.baseline_level,
            retrieved_concepts=state.retrieved_concepts,
            learner_preferences=state.learner_preferences,
        )
        s = result.get("state", {})
        return {
            "explanation": s.get("explanation", ""),
            "workflow_stage": "explanation_generated",
        }

    def _generate_mnemonic_node(self, state: TeachingState) -> Dict[str, Any]:
        """生成记忆辅助: 调用 MnemonicGenerator ReAct Agent

        - 当 skip_mnemonic 为 True 或已理解时直接跳过
        - 否则触发 generate_mnemonic 任务,并将生成结果追加到 mnemonic_devices
        """
        if state.skip_mnemonic or state.assessment_result == "fully_understood":
            return {"workflow_stage": "mnemonic_skipped"}

        result = invoke_mnemonic_generator(
            agent=self.mnemonic_agent,
            task_type="generate_mnemonic",
            concept_name=state.question_text or "",
            explanation=state.explanation or "",
            tenant_id=str(state.tenant_id),
            concept_id=str(state.current_topic_id) if state.current_topic_id else "",
        )
        s = result.get("state", {})
        generated = s.get("generated_mnemonic")
        recommended_strategies = s.get("recommended_strategies", [])

        devices = list(state.mnemonic_devices)
        if generated:
            devices.append(generated)

        return {
            "generated_mnemonic": generated,
            "recommended_strategy": recommended_strategies[0] if recommended_strategies else None,
            "mnemonic_devices": devices,
            "workflow_stage": "mnemonic_generated",
        }

    def _create_comprehension_check_node(self, state: TeachingState) -> Dict[str, Any]:
        """生成理解检查问题: 调用 SocraticTeacher 的 generate_questions 任务"""
        result = invoke_socratic_teacher(
            agent=self.socratic_agent,
            task_type="generate_questions",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            explanation=state.explanation or "",
            baseline_level=state.baseline_level,
        )
        s = result.get("state", {})
        return {
            "comprehension_questions": s.get("comprehension_questions", []),
            "workflow_stage": "comprehension_check_created",
        }

    def _wait_for_response_node(self, state: TeachingState) -> Dict[str, Any]:
        """等待学习者回答: 工作流在此节点暂停,交由外部继续"""
        return {"workflow_stage": "waiting_for_response"}

    # ---- 评估 & 路由: 使用 KnowledgeAssessor / Socratic ------------------

    def _assess_understanding_node(self, state: TeachingState) -> Dict[str, Any]:
        """评估理解程度: 调用 KnowledgeAssessor ReAct Agent"""
        if not state.learner_response:
            return {
                "assessment_result": "not_understood",
                "workflow_stage": "assessment_failed",
            }

        # 提取期望关键点(来自理解检查问题)
        expected_points: list[str] = []
        for q in state.comprehension_questions:
            # q 可能是 Pydantic 模型或字典
            points = getattr(q, "expected_key_points", None) or getattr(q, "get", None) and q.get("expected_key_points")
            if points:
                expected_points.extend(points)

        assess_res = invoke_knowledge_assessor(
            agent=self.assessor_agent,
            task_type="assess_understanding",
            question=state.question_text or "",
            explanation=state.explanation or "",
            learner_response=state.learner_response or "",
            expected_key_points=expected_points,
            retry_count=state.retry_count,
            max_retries=state.max_retries,
        )
        s_assess = assess_res.get("state", {})

        next_res = invoke_knowledge_assessor(
            agent=self.assessor_agent,
            task_type="recommend_next_action",
            question=state.question_text or "",
            explanation=state.explanation or "",
            learner_response=state.learner_response or "",
            assessment_result=s_assess.get("assessment_result"),
            retry_count=state.retry_count,
            max_retries=state.max_retries,
        )
        s_next = next_res.get("state", {})

        return {
            "assessment_result": s_assess.get("assessment_result"),
            "confidence_level": s_assess.get("confidence_level"),
            "assessment_details": s_assess.get("assessment_details"),
            "key_points_understood": s_assess.get("key_points_understood", []),
            "misunderstandings": s_assess.get("misunderstandings", []),
            "next_action": s_next.get("next_action"),
            "workflow_stage": "understanding_assessed",
        }

    def _adaptive_followup_node(self, state: TeachingState) -> Dict[str, Any]:
        """自适应跟进: 调用 SocraticTeacher 的 adaptive_followup 任务"""
        result = invoke_socratic_teacher(
            agent=self.socratic_agent,
            task_type="adaptive_followup",
            question=state.question_text or "",
            tenant_id=state.tenant_id,
            previous_explanation=state.explanation or "",
            learner_response=state.learner_response or "",
            misunderstandings=state.misunderstandings or [],
        )
        s = result.get("state", {})
        return {
            "explanation": s.get("explanation", state.explanation),
            "workflow_stage": "followup_generated",
        }

    def _update_progress_node(self, state: TeachingState) -> Dict[str, Any]:
        """更新进度: 调用 ProgressTracker ReAct Agent 做一次 track_progress

        具体的掌握状态更新/知识缺口记录仍然由工具层和 ProgressTracker 兼容层负责,
        此处主要用于触发一次进度刷新并在 TeachingState 中缓存部分摘要。
        """
        # 只在完全理解时刷新一次摘要
        if state.assessment_result != "fully_understood":
            return {"workflow_stage": "progress_skipped"}

        res = invoke_progress_tracker(
            agent=self.progress_agent,
            task_type="track_progress",
            learner_id=str(state.learner_id),
            tenant_id=str(state.tenant_id),
        )
        s = res.get("state", {})
        return {
            "knowledge_gaps": s.get("knowledge_gaps", []),
            "workflow_stage": "progress_updated",
        }

    def _record_gap_node(self, state: TeachingState) -> Dict[str, Any]:
        """记录知识缺口: 仅更新 TeachingState,具体持久化交给 ProgressTracker 兼容层"""
        # 这里不直接写数据库,而是标记状态,方便上层调用 ProgressTracker.record_gap
        return {"workflow_stage": "gap_recorded"}

    def _finalize_node(self, state: TeachingState) -> Dict[str, Any]:
        """终止节点"""
        return {
            "workflow_stage": "completed",
            "timestamp": datetime.now(),
        }

    # ---- 其他意图入口节点 ----------------------------------------------

    def _progress_entry_node(self, state: TeachingState) -> Dict[str, Any]:
        """进度查询意图入口: 使用 ProgressTracker ReAct Agent 生成进度摘要"""
        res = invoke_progress_tracker(
            agent=self.progress_agent,
            task_type="analyze_efficiency",
            learner_id=str(state.learner_id),
            tenant_id=str(state.tenant_id),
        )
        s = res.get("state", {})
        return {
            "learning_efficiency": s.get("efficiency_metrics"),
            "workflow_stage": "progress_overview_generated",
        }

    def _review_entry_node(self, state: TeachingState) -> Dict[str, Any]:
        """复习意图入口: 推荐需要复习的主题"""
        res = invoke_progress_tracker(
            agent=self.progress_agent,
            task_type="recommend_review",
            learner_id=str(state.learner_id),
            tenant_id=str(state.tenant_id),
        )
        s = res.get("state", {})
        return {
            "review_reminders": s.get("review_recommendations", []),
            "workflow_stage": "review_recommendations_generated",
        }

    def _assessment_entry_node(self, state: TeachingState) -> Dict[str, Any]:
        """练习/评估意图入口: 单次调用 KnowledgeAssessor 做评估"""
        assess_res = invoke_knowledge_assessor(
            agent=self.assessor_agent,
            task_type="assess_understanding",
            question=state.question_text or "",
            explanation=state.explanation or "",
            learner_response=state.learner_response or "",
            expected_key_points=[],
            retry_count=state.retry_count,
            max_retries=state.max_retries,
        )
        s = assess_res.get("state", {})
        return {
            "assessment_result": s.get("assessment_result"),
            "confidence_level": s.get("confidence_level"),
            "assessment_details": s.get("assessment_details"),
            "workflow_stage": "assessment_only_completed",
        }

    def _other_entry_node(self, state: TeachingState) -> Dict[str, Any]:
        """兜底意图: 目前直接回退为学习路径"""
        # 简单策略: 把 intent 归一为 learn, 后续由上层重新触发学习流程
        return {"intent": "learn", "workflow_stage": "fallback_to_learn"}

    # ====================================================================
    # 路由决策辅助函数
    # ====================================================================

    def _should_validate_content(self, state: TeachingState) -> Literal["validate", "skip"]:
        """决定是否需要内容验证

        简单策略:
        - skip_validation 为 True 时直接跳过
        - 解释中包含数字或"规则/公式/税率/限额"等关键词时触发验证
        """
        if state.skip_validation:
            return "skip"

        explanation = state.explanation or ""
        if not explanation:
            return "skip"

        # 关键字 & 数字检测
        keywords = ["规则", "公式", "法律", "税率", "限额", "%", "率"]
        if any(k in explanation for k in keywords):
            return "validate"

        import re

        if re.search(r"\d", explanation):
            return "validate"

        return "skip"

    def _should_generate_mnemonic(self, state: TeachingState) -> Literal["generate", "skip"]:
        """决定是否需要生成记忆辅助"""
        if state.skip_mnemonic:
            return "skip"

        explanation = state.explanation or ""
        # 简单规则: 解释较长或 assessment_result 为 not_understood 时触发
        if state.assessment_result == "not_understood":
            return "generate"
        if len(explanation) > 300:
            return "generate"
        return "skip"

    def _route_after_assessment(self, state: TeachingState) -> Literal[
        "continue", "adaptive_followup", "retry", "record_gap"
    ]:
        """评估结束后的路由决策

        - fully_understood → continue
        - partially_understood → adaptive_followup
        - not_understood 且 retry_count < max_retries → retry
        - not_understood 且已达最大重试次数 → record_gap
        """
        if state.next_action:
            # 如果 KnowledgeAssessor 已经给出建议,优先使用
            return state.next_action  # type: ignore[return-value]

        if state.assessment_result == "fully_understood":
            return "continue"
        if state.assessment_result == "partially_understood":
            return "adaptive_followup"
        if state.retry_count < state.max_retries:
            return "retry"
        return "record_gap"

    def _check_needs_validation(self, state: TeachingState, concepts: list) -> bool:
        """根据检索到的概念粗略判断是否需要验证内容"""
        for concept in concepts:
            if isinstance(concept, dict):
                if concept.get("formulas") or concept.get("rules"):
                    return True
        return False

    # ====================================================================
    # 公共接口: 供 CLI / 外部调用
    # ====================================================================

    def run(
        self,
        learner_id: UUID,
        goal_id: UUID,
        tenant_id: UUID,
        question_text: str,
        initial_understanding: Optional[str] = None,
    ) -> TeachingState:
        """执行主工作流,返回在 wait_for_response 或终止节点时的 TeachingState

        典型 CLI 使用方式:
        1. 调用 run() 获得解释和理解检查问题
        2. 获取学习者回答后调用 continue_with_response() 完成评估和路由
        """
        initial_state = create_initial_state(
            learner_id=learner_id,
            goal_id=goal_id,
            tenant_id=tenant_id,
            question_text=question_text,
            initial_understanding=initial_understanding,
        )

        result = self.workflow.invoke(initial_state)
        return TeachingState(**result)

    def continue_with_response(self, state: TeachingState, learner_response: str) -> TeachingState:
        """在获得学习者回答后继续工作流,直到评估完成"""
        state.learner_response = learner_response
        result = self.workflow.invoke(state)
        return TeachingState(**result)


def create_teaching_workflow(
    session: Session,
    vector_search: VectorSearchService,
    llm: Optional[ChatOpenAI] = None,
) -> SocraticTeachingWorkflow:
    """工厂函数: 创建主教学工作流实例"""
    return SocraticTeachingWorkflow(session=session, vector_search=vector_search, llm=llm)
