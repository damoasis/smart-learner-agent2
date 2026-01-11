"""
MnemonicGenerator ReAct Agent

基于LangGraph的ReAct模式独立Agent,负责记忆辅助生成的推理与行动循环。
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal
import json

from langgraph.graph import StateGraph, END
from backend.agents.react.tool_executor import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.agents.tools.mnemonic_generator_tools import (
    analyze_concept_features,
    select_mnemonic_strategy,
    generate_acronym,
    generate_analogy,
    generate_comparison,
    generate_visual,
    generate_number_pattern,
    save_mnemonic_device
)


class MnemonicGeneratorState(TypedDict):
    """MnemonicGenerator Agent状态"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    
    # 任务输入
    task_type: Literal["generate_mnemonic", "save_mnemonic"]
    concept_name: str
    explanation: str
    
    # 记忆辅助相关
    tenant_id: str
    concept_id: str
    strategy_type: Optional[str]  # "acronym" | "analogy" | "comparison" | "visual" | "number"
    
    # 输出字段
    concept_features: Optional[dict]
    recommended_strategies: list
    generated_mnemonic: Optional[dict]
    saved_mnemonic_id: Optional[str]
    
    # 控制字段
    next_step: Optional[str]
    result: Optional[dict]
    error: Optional[str]


def create_mnemonic_generator_agent(
    session: Session,
    llm: Optional[ChatOpenAI] = None
):
    """
    创建MnemonicGenerator ReAct Agent
    
    Args:
        session: 数据库会话
        llm: LLM实例（可选）
    
    Returns:
        编译后的LangGraph Agent
    """
    
    # 准备工具列表
    tools = [
        analyze_concept_features,
        select_mnemonic_strategy,
        generate_acronym,
        generate_analogy,
        generate_comparison,
        generate_visual,
        generate_number_pattern,
        save_mnemonic_device
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
    
    def agent_node(state: MnemonicGeneratorState) -> MnemonicGeneratorState:
        """Agent推理节点"""
        messages = state["messages"]
        task_type = state["task_type"]
        
        system_prompts = {
            "generate_mnemonic": """你是记忆辅助生成专家。你的任务是生成有效的记忆辅助设备。

可用工具：
- analyze_concept_features: 分析概念特征
- select_mnemonic_strategy: 选择记忆策略
- generate_acronym: 生成缩略词记忆
- generate_analogy: 生成类比记忆
- generate_comparison: 生成对比表记忆
- generate_visual: 生成视觉联想记忆
- generate_number_pattern: 生成数字模式记忆

生成流程：
1. 使用analyze_concept_features分析概念特征
2. 使用select_mnemonic_strategy选择合适的记忆策略
3. 根据策略使用对应的生成工具（acronym/analogy/comparison/visual/number_pattern）

请按顺序执行生成流程。""",
            
            "save_mnemonic": """你是记忆辅助管理专家。你的任务是保存生成的记忆辅助。

可用工具：
- save_mnemonic_device: 保存记忆辅助到数据库

请使用工具保存记忆辅助。"""
        }
        
        system_message = system_prompts.get(task_type, "你是记忆辅助助手。")
        
        if not messages:
            messages = [
                HumanMessage(content=system_message),
                HumanMessage(content=f"任务: {task_type}\n概念: {state.get('concept_name')}\n解释: {state.get('explanation', '')[:200]}...")
            ]
        
        response = llm_with_tools.invoke(messages)
        new_messages = list(messages) + [response]
        
        return {"messages": new_messages}
    
    def tool_node(state: MnemonicGeneratorState) -> MnemonicGeneratorState:
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
            if tool_name == "analyze_concept_features":
                if "concept_name" not in tool_args:
                    tool_args["concept_name"] = state.get("concept_name")
                if "explanation" not in tool_args:
                    tool_args["explanation"] = state.get("explanation")
            
            elif tool_name == "select_mnemonic_strategy":
                if "features" not in tool_args:
                    tool_args["features"] = state.get("concept_features", {})
            
            elif tool_name == "generate_acronym":
                pass  # generate_acronym不再需要llm参数
            
            elif tool_name == "generate_analogy":
                if "concept" not in tool_args:
                    tool_args["concept"] = state.get("concept_name")
                if "explanation" not in tool_args:
                    tool_args["explanation"] = state.get("explanation")
                if "learner_background" not in tool_args:
                    tool_args["learner_background"] = None
            
            elif tool_name == "generate_comparison":
                if "context" not in tool_args:
                    tool_args["context"] = state.get("explanation")
            
            elif tool_name == "generate_visual":
                if "concept" not in tool_args:
                    tool_args["concept"] = state.get("concept_name")
                if "concept_type" not in tool_args:
                    tool_args["concept_type"] = "flowchart"
            
            elif tool_name == "generate_number_pattern":
                if "rule_text" not in tool_args:
                    tool_args["rule_text"] = state.get("explanation", "")
            
            elif tool_name == "save_mnemonic_device":
                tool_args["session"] = session
                if "tenant_id" not in tool_args:
                    tool_args["tenant_id"] = state.get("tenant_id")
                if "concept_id" not in tool_args:
                    tool_args["concept_id"] = state.get("concept_id")
                if "strategy_type" not in tool_args:
                    tool_args["strategy_type"] = state.get("strategy_type", "analogy")
                if "content" not in tool_args:
                    tool_args["content"] = state.get("generated_mnemonic", {})
            
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
    
    def should_continue(state: MnemonicGeneratorState) -> str:
        """条件路由"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    def extract_result(state: MnemonicGeneratorState) -> MnemonicGeneratorState:
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
        
        concept_features = None
        recommended_strategies = []
        generated_mnemonic = None
        saved_mnemonic_id = None
        
        for tool_result in tool_results:
            if isinstance(tool_result, dict):
                # 判断是哪种dict
                if "complexity" in tool_result or "num_key_points" in tool_result:
                    concept_features = tool_result
                elif "acronym" in tool_result:
                    generated_mnemonic = tool_result
                elif "abstract_concept" in tool_result and "concrete_analogy" in tool_result:
                    generated_mnemonic = tool_result
                elif "table_title" in tool_result and "dimensions" in tool_result:
                    generated_mnemonic = tool_result
                elif "visual_type" in tool_result and "mermonic_diagram" in tool_result:
                    generated_mnemonic = tool_result
                elif "pattern" in tool_result and "memory_phrase" in tool_result:
                    generated_mnemonic = tool_result
            
            elif isinstance(tool_result, list):
                # 可能是recommended_strategies
                if tool_result and isinstance(tool_result[0], str):
                    recommended_strategies = tool_result
            
            elif isinstance(tool_result, str):
                # 可能是saved_mnemonic_id
                if len(tool_result) == 36 or "-" in tool_result:  # UUID格式
                    saved_mnemonic_id = tool_result
        
        if task_type == "generate_mnemonic":
            result = {
                "concept_features": concept_features,
                "recommended_strategies": recommended_strategies,
                "generated_mnemonic": generated_mnemonic
            }
            return {
                "concept_features": concept_features,
                "recommended_strategies": recommended_strategies,
                "generated_mnemonic": generated_mnemonic,
                "result": result,
                "error": None
            }
        
        elif task_type == "save_mnemonic":
            result = {"saved_mnemonic_id": saved_mnemonic_id}
            return {
                "saved_mnemonic_id": saved_mnemonic_id,
                "result": result,
                "error": None
            }
        
        return {"result": {}, "error": None}
    
    # 构建StateGraph
    workflow = StateGraph(MnemonicGeneratorState)
    
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
    
    print("Mnemonic Generator Workflow Graph:")
    compile_workflow = workflow.compile()
    compile_workflow.get_graph().print_ascii()
    return compile_workflow


def invoke_mnemonic_generator(
    agent,
    task_type: str,
    concept_name: str,
    explanation: str,
    tenant_id: str,
    concept_id: str,
    strategy_type: Optional[str] = None
) -> dict:
    """调用MnemonicGenerator Agent的便捷函数"""
    initial_state = {
        "messages": [],
        "task_type": task_type,
        "concept_name": concept_name,
        "explanation": explanation,
        "tenant_id": tenant_id,
        "concept_id": concept_id,
        "strategy_type": strategy_type,
        "concept_features": None,
        "recommended_strategies": [],
        "generated_mnemonic": None,
        "saved_mnemonic_id": None,
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
