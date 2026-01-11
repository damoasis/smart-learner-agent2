"""
ProgressTracker ReAct Agent

基于LangGraph的ReAct模式独立Agent,负责进度追踪与推荐的推理与行动循环。
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal, Any
from uuid import UUID
import json

from langgraph.graph import StateGraph, END
from backend.agents.react.tool_executor import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.agents.tools.progress_tracker_tools import (
    query_mastery_records,
    query_knowledge_gaps,
    calculate_efficiency_metrics,
    recommend_review_topics,
    recommend_next_topics,
    update_mastery_state,
    record_knowledge_gap,
    save_question_record,
    save_explanation_record,
    save_comprehension_check,
    generate_progress_summary,
    resolve_knowledge_gap
)
from backend.workflows.state import TeachingState
from backend.models.session import TopicMastery, KnowledgeGap, LearningSession
from backend.models.topic import Topic, TopicDependency


class ProgressTrackerState(TypedDict):
    """ProgressTracker Agent状态"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    
    # 任务输入
    task_type: Literal["track_progress", "recommend_review", "recommend_next", "analyze_efficiency"]
    learner_id: str
    tenant_id: str
    
    # 进度查询相关
    time_range_days: Optional[int]
    mastered_topics: list
    
    # 输出字段
    mastery_records: list
    knowledge_gaps: list
    efficiency_metrics: Optional[dict]
    review_recommendations: list
    next_recommendations: list
    
    # 控制字段
    next_step: Optional[str]
    result: Optional[dict]
    error: Optional[str]


def create_progress_tracker_agent(
    session: Session,
    llm: Optional[ChatOpenAI] = None
):
    """
    创建ProgressTracker ReAct Agent
    
    Args:
        session: 数据库会话
        llm: LLM实例（可选）
    
    Returns:
        编译后的LangGraph Agent
    """
    
    # 准备工具列表
    tools = [
        query_mastery_records,
        query_knowledge_gaps,
        calculate_efficiency_metrics,
        recommend_review_topics,
        recommend_next_topics,
        update_mastery_state,
        record_knowledge_gap,
        save_question_record,
        save_explanation_record,
        save_comprehension_check,
        generate_progress_summary,
        resolve_knowledge_gap
    ]
    
    # 创建LLM实例
    if llm is None:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        llm = ChatOpenAI(
            openai_api_key=api_key,
            base_url=base_url,
            model_name=model,
            temperature=0.7
        )
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 创建工具执行器
    tool_executor = ToolExecutor(tools)
    
    def agent_node(state: ProgressTrackerState) -> ProgressTrackerState:
        """Agent推理节点"""
        messages = state["messages"]
        task_type = state["task_type"]
        
        system_prompts = {
            "track_progress": """你是学习进度追踪专家。你的任务是追踪学习者的学习进度。

可用工具：
- query_mastery_records: 查询掌握记录
- query_knowledge_gaps: 查询知识缺口

请使用工具查询学习者的进度数据。""",
            
            "recommend_review": """你是复习推荐专家。你的任务是推荐需要复习的主题。

可用工具：
- recommend_review_topics: 推荐复习主题

请基于掌握记录推荐需要复习的主题。""",
            
            "recommend_next": """你是学习路径规划专家。你的任务是推荐下一步学习主题。

可用工具：
- recommend_next_topics: 推荐下一步主题

请基于已掌握主题推荐下一步学习内容。""",
            
            "analyze_efficiency": """你是学习效率分析专家。你的任务是分析学习效率。

可用工具：
- calculate_efficiency_metrics: 计算效率指标

请基于掌握记录和知识缺口计算学习效率指标。"""
        }
        
        system_message = system_prompts.get(task_type, "你是进度追踪助手。")
        
        if not messages:
            messages = [
                HumanMessage(content=system_message),
                HumanMessage(content=f"任务: {task_type}\n学习者: {state.get('learner_id')}")
            ]
        
        response = llm_with_tools.invoke(messages)
        new_messages = list(messages) + [response]
        
        return {"messages": new_messages}
    
    def tool_node(state: ProgressTrackerState) -> ProgressTrackerState:
        """工具执行节点"""
        messages = state["messages"]
        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        
        if not tool_calls:
            return {"next_step": "end"}
        
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 补充Session依赖
            tool_args["session"] = session
            
            # 补充其他必需参数
            if "learner_id" not in tool_args:
                tool_args["learner_id"] = state["learner_id"]
            if "tenant_id" not in tool_args:
                tool_args["tenant_id"] = state["tenant_id"]
            
            if tool_name == "query_mastery_records" and "time_range_days" not in tool_args:
                tool_args["time_range_days"] = state.get("time_range_days")
            
            elif tool_name == "recommend_next_topics" and "mastered_ids" not in tool_args:
                tool_args["mastered_ids"] = [str(t) for t in state.get("mastered_topics", [])]
            
            elif tool_name == "recommend_review_topics" and "mastery_records" not in tool_args:
                tool_args["mastery_records"] = state.get("mastery_records", [])
            
            elif tool_name == "calculate_efficiency_metrics":
                if "mastery_records" not in tool_args:
                    tool_args["mastery_records"] = state.get("mastery_records", [])
                if "gaps" not in tool_args:
                    tool_args["gaps"] = state.get("knowledge_gaps", [])
            
            try:
                result = tool_executor.invoke(tool_call)
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False, default=str),
                        tool_call_id=tool_call["id"]
                    )
                )
            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=f"工具执行错误: {str(e)}",
                        tool_call_id=tool_call["id"]
                    )
                )
        
        new_messages = list(messages) + tool_messages
        return {"messages": new_messages, "next_step": "agent"}
    
    def should_continue(state: ProgressTrackerState) -> str:
        """条件路由"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    def extract_result(state: ProgressTrackerState) -> ProgressTrackerState:
        """提取结果"""
        messages = state["messages"]
        task_type = state["task_type"]
        
        tool_results = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                try:
                    result = json.loads(msg.content)
                    tool_results.append(result)
                except:
                    pass
        
        result = {}
        mastery_records = []
        knowledge_gaps = []
        efficiency_metrics = None
        review_recommendations = []
        next_recommendations = []
        
        for tool_result in tool_results:
            if isinstance(tool_result, list):
                # 判断是哪种列表
                if tool_result and "concept_id" in str(tool_result[0]):
                    mastery_records = tool_result
                elif tool_result and "gap_id" in str(tool_result[0]):
                    knowledge_gaps = tool_result
                elif tool_result and ("topic_id" in str(tool_result[0]) or "topic_name" in str(tool_result[0])):
                    if not review_recommendations:
                        review_recommendations = tool_result
                    else:
                        next_recommendations = tool_result
            
            elif isinstance(tool_result, dict):
                if "mastery_rate" in tool_result or "avg_attempts" in tool_result:
                    efficiency_metrics = tool_result
        
        if task_type == "track_progress":
            result = {
                "mastery_records": mastery_records,
                "knowledge_gaps": knowledge_gaps
            }
            return {
                "mastery_records": mastery_records,
                "knowledge_gaps": knowledge_gaps,
                "result": result,
                "error": None
            }
        
        elif task_type == "recommend_review":
            result = {"review_recommendations": review_recommendations}
            return {
                "review_recommendations": review_recommendations,
                "result": result,
                "error": None
            }
        
        elif task_type == "recommend_next":
            result = {"next_recommendations": next_recommendations}
            return {
                "next_recommendations": next_recommendations,
                "result": result,
                "error": None
            }
        
        elif task_type == "analyze_efficiency":
            result = {"efficiency_metrics": efficiency_metrics}
            return {
                "efficiency_metrics": efficiency_metrics,
                "result": result,
                "error": None
            }
        
        return {"result": result, "error": None}
    
    # 构建StateGraph
    workflow = StateGraph(ProgressTrackerState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("extract_result", extract_result)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": "extract_result"}
    )
    
    workflow.add_edge("tools", "agent")
    workflow.add_edge("extract_result", END)
    
    print("Progress Tracker Workflow Graph:")
    compile_workflow = workflow.compile()
    compile_workflow.get_graph().print_ascii()
    return compile_workflow


def invoke_progress_tracker(
    agent,
    task_type: str,
    learner_id: str,
    tenant_id: str,
    time_range_days: Optional[int] = None,
    mastered_topics: Optional[list] = None
) -> dict:
    """调用ProgressTracker Agent的便捷函数"""
    initial_state = {
        "messages": [],
        "task_type": task_type,
        "learner_id": learner_id,
        "tenant_id": tenant_id,
        "time_range_days": time_range_days,
        "mastered_topics": mastered_topics or [],
        "mastery_records": [],
        "knowledge_gaps": [],
        "efficiency_metrics": None,
        "review_recommendations": [],
        "next_recommendations": [],
        "next_step": None,
        "result": None,
        "error": None
    }
    
    final_state = agent.invoke(initial_state)
    
    return {
        "result": final_state.get("result"),
        "error": final_state.get("error"),
        "state": final_state
    }


class ProgressTracker:
    """
    进度追踪Agent (兼容层)
    
    职责：
    - 更新主题掌握状态
    - 记录知识缺口
    - 更新学习会话记录
    - 维护学习历史
    - 生成进度摘要
    """
    
    def __init__(self, session: Session):
        """
        初始化进度追踪Agent
        
        Args:
            session: SQLAlchemy数据库会话
        """
        self.session = session
    
    def update_mastery(self, state: TeachingState) -> TeachingState:
        """
        更新或创建主题掌握状态记录
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态
        """
        if not state.current_topic_id:
            state.error_message = "无法更新掌握状态：未指定主题ID"
            return state
        
        result = update_mastery_state.invoke({
            "learner_id": str(state.learner_id),
            "tenant_id": str(state.tenant_id),
            "session": self.session,
            "topic_id": str(state.current_topic_id),
            "confidence_level": state.confidence_level or "medium",
            "key_points": state.key_points_understood or []
        })
        
        state.workflow_stage = "mastery_updated"
        return state
    
    def record_gap(self, state: TeachingState) -> TeachingState:
        """
        记录知识缺口
        
        当学习者多次尝试后仍然无法理解某个概念时，记录为知识缺口
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态
        """
        if not state.current_topic_id:
            state.error_message = "无法记录知识缺口：未指定主题ID"
            return state
        
        # 构建缺口描述
        gap_description = self._generate_gap_description(state)
        
        # 确定严重程度
        severity = self._determine_gap_severity(state)
        
        result = record_knowledge_gap.invoke({
            "learner_id": str(state.learner_id),
            "tenant_id": str(state.tenant_id),
            "session": self.session,
            "topic_id": str(state.current_topic_id),
            "gap_description": gap_description,
            "severity_level": severity,
            "retry_count": state.retry_count
        })
        
        state.workflow_stage = "gap_recorded"
        return state
    
    def save_session_data(self, state: TeachingState) -> TeachingState:
        """
        保存会话相关的所有数据（问题、解释、理解检查）
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态（包含question_id, explanation_id, check_id）
        """
        if not state.session_id:
            state.error_message = "无法保存会话数据：会话ID未设置"
            return state
        
        # 1. 保存问题记录
        if state.question_text and not state.question_id:
            result = save_question_record.invoke({
                "session": self.session,
                "session_id": str(state.session_id),
                "question_text": state.question_text,
                "initial_understanding": state.initial_understanding
            })
            state.question_id = UUID(result["question_id"])
        
        # 2. 保存解释记录
        if state.explanation and state.question_id and not state.explanation_id:
            result = save_explanation_record.invoke({
                "session": self.session,
                "question_id": str(state.question_id),
                "explanation_text": state.explanation,
                "teaching_method": state.teaching_method
            })
            state.explanation_id = UUID(result["explanation_id"])
        
        # 3. 保存理解检查记录
        if state.learner_response and state.explanation_id and not state.check_id:
            # 构建理解检查问题文本
            check_question = "\n".join([
                q.question_text for q in state.comprehension_questions
            ])
            
            result = save_comprehension_check.invoke({
                "session": self.session,
                "explanation_id": str(state.explanation_id),
                "question_asked": check_question,
                "learner_response": state.learner_response,
                "is_correct": (state.assessment_result == "fully_understood"),
                "assessment_result": state.assessment_details
            })
            state.check_id = UUID(result["check_id"])
        
        state.workflow_stage = "session_data_saved"
        return state
    
    def generate_progress_summary(self, learner_id: UUID, tenant_id: UUID) -> dict:
        """
        生成学习者的总体进度摘要
        
        Args:
            learner_id: 学习者ID
            tenant_id: 租户ID
        
        Returns:
            包含进度信息的字典
        """
        return generate_progress_summary.invoke({
            "learner_id": str(learner_id),
            "tenant_id": str(tenant_id),
            "session": self.session
        })
    
    def resolve_knowledge_gap(self, gap_id: UUID, resolution_notes: Optional[str] = None) -> bool:
        """
        标记知识缺口为已解决
        
        Args:
            gap_id: 知识缺口ID
            resolution_notes: 解决方案说明（可选）
        
        Returns:
            是否成功解决
        """
        result = resolve_knowledge_gap.invoke({
            "session": self.session,
            "gap_id": str(gap_id),
            "resolution_notes": resolution_notes
        })
        return result.get("success", False)
    
    def _generate_gap_description(self, state: TeachingState) -> str:
        """
        生成知识缺口描述
        
        Args:
            state: 当前教学状态
        
        Returns:
            缺口描述文本
        """
        parts = []
        
        if state.question_text:
            parts.append(f"问题：{state.question_text}")
        
        if state.misunderstandings:
            misunderstandings = ", ".join(state.misunderstandings)
            parts.append(f"误解：{misunderstandings}")
        
        parts.append(f"经过{state.retry_count}次尝试后仍未理解")
        
        return " | ".join(parts)
    
    def _determine_gap_severity(self, state: TeachingState) -> str:
        """
        确定知识缺口的严重程度
        
        Args:
            state: 当前教学状态
        
        Returns:
            严重程度（low/medium/high/critical）
        """
        retry_count = state.retry_count
        
        if retry_count >= 3:
            return "high"
        elif retry_count >= 2:
            return "medium"
        else:
            return "low"
    
    # 阶段二增强功能（保持向后兼容）
    def analyze_learning_efficiency(self, learner_id: UUID, tenant_id: UUID, time_range_days: Optional[int] = None) -> dict:
        """分析学习效率（调用工具实现）"""
        mastery_records = query_mastery_records.invoke({
            "learner_id": str(learner_id),
            "tenant_id": str(tenant_id),
            "session": self.session,
            "time_range_days": time_range_days
        })
        
        gaps = query_knowledge_gaps.invoke({
            "learner_id": str(learner_id),
            "tenant_id": str(tenant_id),
            "session": self.session
        })
        
        return calculate_efficiency_metrics.invoke({
            "mastery_records": mastery_records,
            "gaps": gaps
        })
    
    def get_review_recommendations(self, learner_id: UUID, tenant_id: UUID, max_items: int = 5) -> list:
        """获取复习推荐（调用工具实现）"""
        mastery_records = query_mastery_records.invoke({
            "learner_id": str(learner_id),
            "tenant_id": str(tenant_id),
            "session": self.session
        })
        
        return recommend_review_topics.invoke({
            "mastery_records": mastery_records,
            "session": self.session,
            "max_items": max_items
        })
    
    def recommend_next_topics(self, learner_id: UUID, tenant_id: UUID, goal_id: Optional[UUID] = None, max_recommendations: int = 3) -> list:
        """推荐下一步学习主题（调用工具实现）"""
        from sqlalchemy import select
        
        mastered_query = select(TopicMastery).where(
            TopicMastery.learner_id == learner_id,
            TopicMastery.tenant_id == tenant_id,
            TopicMastery.confidence_level.in_(["high", "medium_high"])
        )
        mastered_topics = [
            str(m.topic_id) for m in self.session.execute(mastered_query).scalars().all()
        ]
        
        return recommend_next_topics.invoke({
            "learner_id": str(learner_id),
            "tenant_id": str(tenant_id),
            "session": self.session,
            "mastered_ids": mastered_topics,
            "max_recs": max_recommendations
        })


def create_progress_tracker(session: Session) -> ProgressTracker:
    """
    工厂函数：创建进度追踪Agent实例
    
    Args:
        session: SQLAlchemy数据库会话
    
    Returns:
        ProgressTracker实例
    """
    return ProgressTracker(session)


def update_mastery_from_state(session: Session, state_data: dict) -> dict:
    """根据TeachingState字典更新主题掌握状态，返回更新后的state字典。"""
    state = TeachingState(**state_data)
    tracker = ProgressTracker(session)
    updated_state = tracker.update_mastery(state)
    return updated_state.dict()


def record_gap_from_state(session: Session, state_data: dict) -> dict:
    """根据TeachingState字典记录知识缺口，返回更新后的state字典。"""
    state = TeachingState(**state_data)
    tracker = ProgressTracker(session)
    updated_state = tracker.record_gap(state)
    return updated_state.dict()


def save_session_data_from_state(session: Session, state_data: dict) -> dict:
    """根据TeachingState字典保存会话数据，返回更新后的state字典。"""
    state = TeachingState(**state_data)
    tracker = ProgressTracker(session)
    updated_state = tracker.save_session_data(state)
    return updated_state.dict()
