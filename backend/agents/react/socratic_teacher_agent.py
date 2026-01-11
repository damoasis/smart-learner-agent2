"""
SocraticTeacher ReAct Agent

基于LangGraph的ReAct模式独立Agent，负责苏格拉底教学的推理与行动循环。
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal
from uuid import UUID
import json

from langgraph.graph import StateGraph, END
from backend.agents.react.tool_executor import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.agents.tools.socratic_teacher_tools import (
    evaluate_knowledge_baseline,
    search_related_concepts,
    generate_socratic_explanation,
    generate_comprehension_questions,
    generate_adaptive_followup
)
from backend.services.vector_search import VectorSearchService


class SocraticTeacherState(TypedDict):
    """SocraticTeacher Agent状态"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    
    # 任务输入
    task_type: Literal["evaluate_baseline", "retrieve_knowledge", "generate_explanation", 
                       "generate_questions", "adaptive_followup"]
    question: str
    initial_understanding: Optional[str]
    
    # 基线评估相关
    baseline_level: Optional[str]
    baseline_assessment: Optional[str]
    
    # 知识检索相关
    tenant_id: UUID
    current_topic_id: Optional[UUID]
    retrieved_concepts: list
    
    # 解释生成相关
    explanation: Optional[str]
    learner_preferences: Optional[dict]
    
    # 理解检查相关
    comprehension_questions: list
    
    # 自适应跟进相关
    previous_explanation: Optional[str]
    learner_response: Optional[str]
    misunderstandings: list
    
    # 控制字段
    next_step: Optional[str]  # "tools" | "end"
    result: Optional[dict]
    error: Optional[str]


def create_socratic_teacher_agent(
    session: Session,
    vector_search: VectorSearchService,
    llm: Optional[ChatOpenAI] = None
):
    """
    创建SocraticTeacher ReAct Agent
    
    Args:
        session: 数据库会话
        vector_search: 向量检索服务
        llm: LLM实例（可选）
    
    Returns:
        编译后的LangGraph Agent
    """
    
    # 准备工具列表
    tools = [
        evaluate_knowledge_baseline,
        search_related_concepts,
        generate_socratic_explanation,
        generate_comprehension_questions,
        generate_adaptive_followup
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
    
    def agent_node(state: SocraticTeacherState) -> SocraticTeacherState:
        """
        Agent推理节点：LLM决策下一步行动
        """
        messages = state["messages"]
        task_type = state["task_type"]
        
        # 根据任务类型构建系统提示
        system_prompts = {
            "evaluate_baseline": """你是一位经验丰富的教育专家。你的任务是评估学习者的知识基线水平。

可用工具：
- evaluate_knowledge_baseline: 评估学习者知识基线

输入信息：
- question: 学习者提出的问题
- initial_understanding: 学习者的初始理解

请使用工具评估基线水平，返回包含level和assessment的结果。""",
            
            "retrieve_knowledge": """你是一位知识检索专家。你的任务是根据问题检索相关概念。

可用工具：
- search_related_concepts: 向量检索相关概念

输入信息：
- question: 学习者提出的问题
- tenant_id: 租户ID
- current_topic_id: 当前主题ID（可选）

请使用工具检索相关概念。""",
            
            "generate_explanation": """你是一位采用苏格拉底教学法的优秀教师。你的任务是生成引导性解释。

可用工具：
- generate_socratic_explanation: 生成苏格拉底式解释

输入信息：
- question: 学习者问题
- retrieved_concepts: 检索到的相关概念
- baseline_level: 知识基线水平
- learner_preferences: 学习偏好

请生成约200字的引导性解释。""",
            
            "generate_questions": """你是一位教育评估专家。你的任务是生成理解检查问题。

可用工具：
- generate_comprehension_questions: 生成理解检查问题

输入信息：
- explanation: 刚才的解释内容
- baseline_level: 知识基线水平

请生成1-2个开放式理解检查问题。""",
            
            "adaptive_followup": """你是一位善于调整教学策略的教师。你的任务是提供自适应跟进。

可用工具：
- generate_adaptive_followup: 生成自适应跟进策略

输入信息：
- question: 原始问题
- previous_explanation: 之前的解释
- learner_response: 学习者的回答
- misunderstandings: 识别的误解

请生成自适应跟进策略和内容。"""
        }
        
        system_message = system_prompts.get(task_type, "你是一位教学助手。")
        
        # 如果消息列表为空，添加系统消息和任务消息
        if not messages:
            messages = [
                HumanMessage(content=system_message),
                HumanMessage(content=f"任务类型: {task_type}\n问题: {state.get('question', '')}")
            ]
        
        # 调用LLM
        response = llm_with_tools.invoke(messages)
        
        # 更新消息历史
        new_messages = list(messages) + [response]
        
        return {"messages": new_messages}
    
    def tool_node(state: SocraticTeacherState) -> SocraticTeacherState:
        """
        工具执行节点：执行LLM选择的工具
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # 获取工具调用
        tool_calls = getattr(last_message, "tool_calls", [])
        
        if not tool_calls:
            return {"next_step": "end"}
        
        # 执行所有工具调用
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 根据工具名称补充依赖参数
            if tool_name == "search_related_concepts":
                tool_args["vector_search"] = vector_search
                tool_args["tenant_id"] = state["tenant_id"]
                if state.get("current_topic_id"):
                    tool_args["topic_id"] = state["current_topic_id"]
            
            elif tool_name == "evaluate_knowledge_baseline":
                tool_args["llm"] = llm
            
            elif tool_name == "generate_socratic_explanation":
                tool_args["llm"] = llm
            
            elif tool_name == "generate_comprehension_questions":
                tool_args["llm"] = llm
            
            elif tool_name == "generate_adaptive_followup":
                tool_args["llm"] = llm
            
            # 执行工具
            try:
                result = tool_executor.invoke(tool_call)
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
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
        
        # 更新消息历史
        new_messages = list(messages) + tool_messages
        
        return {"messages": new_messages, "next_step": "agent"}
    
    def should_continue(state: SocraticTeacherState) -> str:
        """
        条件路由：决定是继续调用工具还是结束
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # 如果最后一条消息包含工具调用，继续到工具节点
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # 否则结束
        return "end"
    
    def extract_result(state: SocraticTeacherState) -> SocraticTeacherState:
        """
        提取最终结果节点
        """
        messages = state["messages"]
        task_type = state["task_type"]
        
        # 从消息历史中提取结果
        result = {}
        error = None
        
        # 查找最后的工具消息
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                try:
                    tool_result = json.loads(msg.content)
                    result = tool_result
                    break
                except:
                    error = f"无法解析工具结果: {msg.content}"
        
        # 根据任务类型更新state
        if task_type == "evaluate_baseline":
            if "level" in result:
                return {
                    "baseline_level": result["level"],
                    "baseline_assessment": result.get("assessment", ""),
                    "result": result,
                    "error": error
                }
        
        elif task_type == "retrieve_knowledge":
            if isinstance(result, list):
                return {
                    "retrieved_concepts": result,
                    "result": result,
                    "error": error
                }
        
        elif task_type == "generate_explanation":
            if isinstance(result, str):
                return {
                    "explanation": result,
                    "result": {"explanation": result},
                    "error": error
                }
        
        elif task_type == "generate_questions":
            if isinstance(result, list):
                return {
                    "comprehension_questions": result,
                    "result": result,
                    "error": error
                }
        
        elif task_type == "adaptive_followup":
            if "strategy" in result:
                return {
                    "explanation": result.get("followup_content", ""),
                    "result": result,
                    "error": error
                }
        
        return {"result": result, "error": error}
    
    # 构建StateGraph
    workflow = StateGraph(SocraticTeacherState)
    
    # 添加节点
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("extract_result", extract_result)
    
    # 设置入口点
    workflow.set_entry_point("agent")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": "extract_result"
        }
    )
    
    # 工具节点总是返回agent继续推理
    workflow.add_edge("tools", "agent")
    
    # 提取结果后结束
    workflow.add_edge("extract_result", END)

    print("Socratic Teacher Workflow Graph:")
    compile_workflow = workflow.compile()
    compile_workflow.get_graph().print_ascii()
    return compile_workflow



def invoke_socratic_teacher(
    agent,
    task_type: str,
    question: str,
    tenant_id: UUID,
    initial_understanding: Optional[str] = None,
    baseline_level: Optional[str] = None,
    retrieved_concepts: Optional[list] = None,
    explanation: Optional[str] = None,
    previous_explanation: Optional[str] = None,
    learner_response: Optional[str] = None,
    misunderstandings: Optional[list] = None,
    learner_preferences: Optional[dict] = None,
    current_topic_id: Optional[UUID] = None
) -> dict:
    """
    调用SocraticTeacher Agent的便捷函数
    
    Args:
        agent: 编译后的Agent
        task_type: 任务类型
        question: 学习者问题
        tenant_id: 租户ID
        其他参数根据task_type提供
    
    Returns:
        包含result和error的字典
    """
    initial_state = {
        "messages": [],
        "task_type": task_type,
        "question": question,
        "tenant_id": tenant_id,
        "initial_understanding": initial_understanding,
        "baseline_level": baseline_level,
        "retrieved_concepts": retrieved_concepts or [],
        "explanation": explanation,
        "previous_explanation": previous_explanation,
        "learner_response": learner_response,
        "misunderstandings": misunderstandings or [],
        "learner_preferences": learner_preferences,
        "current_topic_id": current_topic_id,
        "comprehension_questions": [],
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
