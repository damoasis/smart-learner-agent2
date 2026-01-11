"""
KnowledgeAssessor ReAct Agent

基于LangGraph的ReAct模式独立Agent，负责知识评估的推理与行动循环。
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal
import json

from langgraph.graph import StateGraph, END
from backend.agents.react.tool_executor import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.agents.tools.knowledge_assessor_tools import (
    extract_key_points,
    identify_misunderstandings,
    assess_understanding_level,
    decide_next_action
)


class KnowledgeAssessorState(TypedDict):
    """KnowledgeAssessor Agent状态"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    
    # 任务输入
    task_type: Literal["assess_understanding", "calibrate_confidence", "recommend_next_action"]
    question: str
    explanation: str
    learner_response: str
    
    # 评估相关
    expected_key_points: list
    comprehension_questions: list
    
    # 输出字段
    key_points_understood: list
    misunderstandings: list
    assessment_result: Optional[str]  # "fully_understood" | "partially_understood" | "not_understood"
    confidence_level: Optional[str]  # "low" | "medium" | "medium_high" | "high"
    assessment_details: Optional[str]
    next_action: Optional[str]  # "continue" | "adaptive_followup" | "retry" | "record_gap"
    
    # 控制字段
    retry_count: int
    max_retries: int
    next_step: Optional[str]  # "tools" | "end"
    result: Optional[dict]
    error: Optional[str]


def create_knowledge_assessor_agent(
    session: Session,
    llm: Optional[ChatOpenAI] = None
):
    """
    创建KnowledgeAssessor ReAct Agent
    
    Args:
        session: 数据库会话
        llm: LLM实例（可选）
    
    Returns:
        编译后的LangGraph Agent
    """
    
    # 准备工具列表
    tools = [
        extract_key_points,
        identify_misunderstandings,
        assess_understanding_level,
        decide_next_action
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
    
    def agent_node(state: KnowledgeAssessorState) -> KnowledgeAssessorState:
        """
        Agent推理节点：LLM决策下一步行动
        """
        messages = state["messages"]
        task_type = state["task_type"]
        
        # 根据任务类型构建系统提示
        system_prompts = {
            "assess_understanding": """你是一位专业的教育评估专家。你的任务是评估学习者的理解水平。

可用工具：
- extract_key_points: 从学习者回答中提取关键点
- identify_misunderstandings: 识别学习者回答中的误解
- assess_understanding_level: 评估理解水平

评估流程：
1. 使用extract_key_points从学习者回答中提取关键点
2. 使用identify_misunderstandings识别误解
3. 使用assess_understanding_level综合评估理解水平

输入信息：
- question: 原始问题
- explanation: 提供的解释
- learner_response: 学习者的回答
- expected_key_points: 期望的关键点

请按顺序使用工具完成评估。""",
            
            "calibrate_confidence": """你是一位教育评估专家。你的任务是校准学习者的信心等级。

基于评估结果和重试次数，确定合适的信心等级：
- high: 完全理解且首次正确
- medium_high: 完全理解
- medium: 部分理解或经过重试
- low: 多次尝试仍不理解

输入信息：
- assessment_result: 评估结果
- retry_count: 重试次数

请根据规则确定信心等级。""",
            
            "recommend_next_action": """你是一位教学策略专家。你的任务是决定下一步行动。

可用工具：
- decide_next_action: 根据评估结果决定下一步

决策规则：
- fully_understood: 继续下一个主题 (continue)
- partially_understood: 提供自适应跟进 (adaptive_followup)
- not_understood且未达最大重试: 重新解释 (retry)
- not_understood且达最大重试: 记录知识缺口 (record_gap)

输入信息：
- assessment_result: 评估结果
- retry_count: 当前重试次数
- max_retries: 最大重试次数

请使用工具决定下一步行动。"""
        }
        
        system_message = system_prompts.get(task_type, "你是一位评估助手。")
        
        # 如果消息列表为空，添加系统消息和任务消息
        if not messages:
            task_info = f"""任务类型: {task_type}
原始问题: {state.get('question', '')}
学习者回答: {state.get('learner_response', '')}
期望关键点: {state.get('expected_key_points', [])}
当前重试次数: {state.get('retry_count', 0)}"""
            
            messages = [
                HumanMessage(content=system_message),
                HumanMessage(content=task_info)
            ]
        
        # 调用LLM
        response = llm_with_tools.invoke(messages)
        
        # 更新消息历史
        new_messages = list(messages) + [response]
        
        return {"messages": new_messages}
    
    def tool_node(state: KnowledgeAssessorState) -> KnowledgeAssessorState:
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
            if tool_name == "extract_key_points":
                tool_args["llm"] = llm
            
            elif tool_name == "identify_misunderstandings":
                if "expected_key_points" not in tool_args:
                    tool_args["expected_key_points"] = state.get("expected_key_points", [])
                if "explanation" not in tool_args:
                    tool_args["explanation"] = state.get("explanation", "")
            
            elif tool_name == "assess_understanding_level":
                if "learner_response" not in tool_args:
                    tool_args["learner_response"] = state.get("learner_response", "")
            
            elif tool_name == "decide_next_action":
                if "retry_count" not in tool_args:
                    tool_args["retry_count"] = state.get("retry_count", 0)
                if "max_retries" not in tool_args:
                    tool_args["max_retries"] = state.get("max_retries", 3)
            
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
    
    def should_continue(state: KnowledgeAssessorState) -> str:
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
    
    def extract_result(state: KnowledgeAssessorState) -> KnowledgeAssessorState:
        """
        提取最终结果节点
        """
        messages = state["messages"]
        task_type = state["task_type"]
        
        # 从消息历史中提取所有工具结果
        tool_results = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                try:
                    result = json.loads(msg.content)
                    tool_results.append(result)
                except:
                    pass
        
        # 汇总结果
        result = {}
        error = None
        
        # 从工具结果中提取信息
        key_points_understood = []
        misunderstandings = []
        assessment_result = None
        confidence_level = None
        assessment_details = None
        next_action = None
        
        for tool_result in tool_results:
            if isinstance(tool_result, list):
                # 可能是key_points或misunderstandings
                if not key_points_understood:
                    key_points_understood = tool_result
                elif not misunderstandings:
                    misunderstandings = tool_result
            
            elif isinstance(tool_result, dict):
                if "assessment_result" in tool_result:
                    assessment_result = tool_result["assessment_result"]
                    confidence_level = tool_result.get("confidence_level")
                    assessment_details = tool_result.get("assessment_details")
                
                elif isinstance(tool_result.get("next_action"), str):
                    # decide_next_action的结果
                    next_action = tool_result.get("next_action")
            
            elif isinstance(tool_result, str):
                # decide_next_action可能直接返回字符串
                if tool_result in ["continue", "adaptive_followup", "retry", "record_gap"]:
                    next_action = tool_result
        
        # 构建结果字典
        if task_type == "assess_understanding":
            result = {
                "key_points_understood": key_points_understood,
                "misunderstandings": misunderstandings,
                "assessment_result": assessment_result,
                "confidence_level": confidence_level,
                "assessment_details": assessment_details
            }
            
            return {
                "key_points_understood": key_points_understood,
                "misunderstandings": misunderstandings,
                "assessment_result": assessment_result,
                "confidence_level": confidence_level,
                "assessment_details": assessment_details,
                "result": result,
                "error": error
            }
        
        elif task_type == "calibrate_confidence":
            # 基于评估结果校准信心
            if confidence_level:
                result = {"confidence_level": confidence_level}
            
            return {
                "confidence_level": confidence_level,
                "result": result,
                "error": error
            }
        
        elif task_type == "recommend_next_action":
            result = {"next_action": next_action}
            
            return {
                "next_action": next_action,
                "result": result,
                "error": error
            }
        
        return {"result": result, "error": error}
    
    # 构建StateGraph
    workflow = StateGraph(KnowledgeAssessorState)
    
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

    print("Knowledge Assessor Workflow Graph:")
    compile_workflow = workflow.compile()
    compile_workflow.get_graph().print_ascii()
    return compile_workflow
    


def invoke_knowledge_assessor(
    agent,
    task_type: str,
    question: str,
    explanation: str,
    learner_response: str,
    expected_key_points: Optional[list] = None,
    comprehension_questions: Optional[list] = None,
    assessment_result: Optional[str] = None,
    retry_count: int = 0,
    max_retries: int = 3
) -> dict:
    """
    调用KnowledgeAssessor Agent的便捷函数
    
    Args:
        agent: 编译后的Agent
        task_type: 任务类型
        question: 原始问题
        explanation: 提供的解释
        learner_response: 学习者回答
        expected_key_points: 期望的关键点
        comprehension_questions: 理解检查问题
        assessment_result: 评估结果（用于calibrate_confidence）
        retry_count: 重试次数
        max_retries: 最大重试次数
    
    Returns:
        包含result和error的字典
    """
    initial_state = {
        "messages": [],
        "task_type": task_type,
        "question": question,
        "explanation": explanation,
        "learner_response": learner_response,
        "expected_key_points": expected_key_points or [],
        "comprehension_questions": comprehension_questions or [],
        "key_points_understood": [],
        "misunderstandings": [],
        "assessment_result": assessment_result,
        "confidence_level": None,
        "assessment_details": None,
        "next_action": None,
        "retry_count": retry_count,
        "max_retries": max_retries,
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
