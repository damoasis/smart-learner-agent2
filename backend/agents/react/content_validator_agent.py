"""
ContentValidator ReAct Agent

基于LangGraph的ReAct模式独立Agent,负责内容验证的推理与行动循环。
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal, List
import json

from langgraph.graph import StateGraph, END
from backend.agents.react.tool_executor import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.agents.tools.content_validator_tools import (
    search_verification_sources,
    extract_web_content,
    validate_against_sources,
    save_verified_content,
    should_verify_content,
    generate_verified_explanation,
    get_authority_sources
)


class ContentValidatorState(TypedDict):
    """ContentValidator Agent状态"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    
    # 任务输入
    task_type: Literal["validate_content", "save_verified", "check_need_verification", "enhance_explanation", "query_authority_sources"]
    explanation: str
    concept_name: str
    
    # 验证相关
    tenant_id: str
    concept_id: str
    search_query: Optional[str]
    max_sources: int
    domain_tags: Optional[List[str]]
    min_trust_score: float
    
    # 输出字段
    verification_sources: list
    web_contents: list
    validation_result: Optional[dict]
    saved_content_id: Optional[str]
    should_verify_result: Optional[dict]
    enhanced_explanation: Optional[str]
    authority_sources: Optional[list]
    verified_facts: Optional[List[str]]
    conflicting_info: Optional[List[str]]
    recommendation: Optional[str]
    
    # 控制字段
    next_step: Optional[str]
    result: Optional[dict]
    error: Optional[str]


def create_content_validator_agent(
    session: Session,
    llm: Optional[ChatOpenAI] = None
):
    """
    创建ContentValidator ReAct Agent
    
    Args:
        session: 数据库会话
        llm: LLM实例（可选）
    
    Returns:
        编译后的LangGraph Agent
    """
    
    # 准备工具列表
    tools = [
        search_verification_sources,
        extract_web_content,
        validate_against_sources,
        save_verified_content,
        should_verify_content,
        generate_verified_explanation,
        get_authority_sources
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
    
    def agent_node(state: ContentValidatorState) -> ContentValidatorState:
        """Agent推理节点"""
        messages = state["messages"]
        task_type = state["task_type"]
        
        system_prompts = {
            "validate_content": """你是内容验证专家。你的任务是验证教学内容的准确性。

可用工具：
- should_verify_content: 判断内容是否需要验证
- search_verification_sources: 搜索验证来源
- extract_web_content: 提取网页内容
- validate_against_sources: 验证内容准确性

验证流程：
1. 使用should_verify_content判断是否需要验证
2. 如需验证，使用search_verification_sources搜索权威来源
3. 对每个来源使用extract_web_content提取内容
4. 使用validate_against_sources验证内容准确性

请按顺序执行验证流程。""",
            
            "save_verified": """你是内容管理专家。你的任务是保存已验证的内容。

可用工具：
- save_verified_content: 保存验证内容到数据库

请使用工具保存验证结果。""",
            
            "check_need_verification": """你是内容分析专家。你的任务是判断内容是否需要验证。

可用工具：
- should_verify_content: 判断内容是否需要验证

请使用工具分析内容。""",
            
            "enhance_explanation": """你是内容增强专家。你的任务是为解释添加来源引用。

可用工具：
- generate_verified_explanation: 生成带引用的增强解释

请使用工具增强解释内容。""",
            
            "query_authority_sources": """你是领域专家。你的任务是查询权威来源。

可用工具：
- get_authority_sources: 获取指定领域的权威来源

请使用工具查询权威来源。"""
        }
        
        system_message = system_prompts.get(task_type, "你是内容验证助手。")
        
        if not messages:
            messages = [
                HumanMessage(content=system_message),
                HumanMessage(content=f"任务: {task_type}\n概念: {state.get('concept_name')}\n内容: {state.get('explanation', '')[:200]}...")
            ]
        
        response = llm_with_tools.invoke(messages)
        new_messages = list(messages) + [response]
        
        return {"messages": new_messages}
    
    def tool_node(state: ContentValidatorState) -> ContentValidatorState:
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
            
            # 补充参数
            if tool_name == "search_verification_sources":
                if "query" not in tool_args:
                    tool_args["query"] = state.get("search_query") or state.get("concept_name")
                if "max_results" not in tool_args:
                    tool_args["max_results"] = state.get("max_sources", 3)
            
            elif tool_name == "validate_against_sources":
                if "explanation" not in tool_args:
                    tool_args["explanation"] = state.get("explanation")
                if "sources" not in tool_args:
                    tool_args["sources"] = state.get("verification_sources", [])
            
            elif tool_name == "save_verified_content":
                tool_args["session"] = session
                if "tenant_id" not in tool_args:
                    tool_args["tenant_id"] = state.get("tenant_id")
                if "concept_id" not in tool_args:
                    tool_args["concept_id"] = state.get("concept_id")
                if "content" not in tool_args:
                    tool_args["content"] = state.get("explanation")
            
            elif tool_name == "should_verify_content":
                if "explanation_text" not in tool_args:
                    tool_args["explanation_text"] = state.get("explanation")
                if "concept_name" not in tool_args:
                    tool_args["concept_name"] = state.get("concept_name")
            
            elif tool_name == "generate_verified_explanation":
                if "original_explanation" not in tool_args:
                    tool_args["original_explanation"] = state.get("explanation")
                if "sources" not in tool_args:
                    tool_args["sources"] = state.get("verification_sources", [])
                if "confidence_score" not in tool_args:
                    validation = state.get("validation_result", {})
                    tool_args["confidence_score"] = validation.get("confidence_score", 0.7)
            
            elif tool_name == "get_authority_sources":
                tool_args["session"] = session
                if "domain_tags" not in tool_args:
                    tool_args["domain_tags"] = state.get("domain_tags", [])
                if "min_trust_score" not in tool_args:
                    tool_args["min_trust_score"] = state.get("min_trust_score", 0.8)
            
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
    
    def should_continue(state: ContentValidatorState) -> str:
        """条件路由"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    def extract_result(state: ContentValidatorState) -> ContentValidatorState:
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
        
        verification_sources = []
        web_contents = []
        validation_result = None
        saved_content_id = None
        should_verify_result = None
        enhanced_explanation = None
        authority_sources = None
        
        for tool_result in tool_results:
            if isinstance(tool_result, list):
                # 可能是sources、web_contents或authority_sources
                if tool_result and "url" in str(tool_result[0]):
                    verification_sources = tool_result
                elif tool_result and "trust_score" in str(tool_result[0]):
                    authority_sources = tool_result
                else:
                    web_contents = tool_result
            
            elif isinstance(tool_result, dict):
                if "needs_verification" in tool_result:
                    should_verify_result = tool_result
                elif "is_accurate" in tool_result or "confidence" in tool_result:
                    validation_result = tool_result
            
            elif isinstance(tool_result, str):
                # 可能是saved_content_id或enhanced_explanation
                if len(tool_result) == 36 or ("-" in tool_result and len(tool_result) < 50):  # UUID格式
                    saved_content_id = tool_result
                elif len(tool_result) > 50:  # 长文本是enhanced_explanation
                    enhanced_explanation = tool_result
        
        if task_type == "validate_content":
            result = {
                "verification_sources": verification_sources,
                "validation_result": validation_result,
                "should_verify_result": should_verify_result
            }
            return {
                "verification_sources": verification_sources,
                "validation_result": validation_result,
                "should_verify_result": should_verify_result,
                "result": result,
                "error": None
            }
        
        elif task_type == "save_verified":
            result = {"saved_content_id": saved_content_id}
            return {
                "saved_content_id": saved_content_id,
                "result": result,
                "error": None
            }
        
        elif task_type == "check_need_verification":
            result = {"should_verify_result": should_verify_result}
            return {
                "should_verify_result": should_verify_result,
                "result": result,
                "error": None
            }
        
        elif task_type == "enhance_explanation":
            result = {"enhanced_explanation": enhanced_explanation}
            return {
                "enhanced_explanation": enhanced_explanation,
                "result": result,
                "error": None
            }
        
        elif task_type == "query_authority_sources":
            result = {"authority_sources": authority_sources}
            return {
                "authority_sources": authority_sources,
                "result": result,
                "error": None
            }
        
        return {"result": {}, "error": None}
    
    # 构建StateGraph
    workflow = StateGraph(ContentValidatorState)
    
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
    
    
    print("Content Validator Workflow Graph:")
    compile_workflow = workflow.compile()
    compile_workflow.get_graph().print_ascii()
    return compile_workflow


def invoke_content_validator(
    agent,
    task_type: str,
    explanation: str = "",
    concept_name: str = "",
    tenant_id: str = "",
    concept_id: str = "",
    search_query: Optional[str] = None,
    max_sources: int = 3,
    domain_tags: Optional[List[str]] = None,
    min_trust_score: float = 0.8
) -> dict:
    """调用ContentValidator Agent的便捷函数"""
    initial_state = {
        "messages": [],
        "task_type": task_type,
        "explanation": explanation,
        "concept_name": concept_name,
        "tenant_id": tenant_id,
        "concept_id": concept_id,
        "search_query": search_query,
        "max_sources": max_sources,
        "domain_tags": domain_tags or [],
        "min_trust_score": min_trust_score,
        "verification_sources": [],
        "web_contents": [],
        "validation_result": None,
        "saved_content_id": None,
        "should_verify_result": None,
        "enhanced_explanation": None,
        "authority_sources": None,
        "verified_facts": None,
        "conflicting_info": None,
        "recommendation": None,
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
