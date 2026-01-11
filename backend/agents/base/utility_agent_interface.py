"""
功能Agent统一接口

该模块定义了功能型Agent（工具型Agent）的统一接口。
功能Agent包括：ContentValidator、MnemonicGenerator、KnowledgeAssessor、ProgressTracker等。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel, Field


class CapabilityInfo(BaseModel):
    """Agent能力描述"""
    agent_name: str = Field(..., description="Agent名称")
    capabilities: List[str] = Field(
        default_factory=list,
        description="能力列表"
    )
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="输入模式定义"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="输出模式定义"
    )


class UtilityAgentInterface(ABC):
    """
    功能Agent统一接口
    
    功能Agent是工具型Agent，提供特定功能服务，可被所有教学Agent复用。
    
    核心方法：
    - execute(): 执行功能操作
    - get_capability_info(): 返回Agent能力描述
    
    示例实现：
    - ContentValidatorAgent: 内容验证、在线搜索、来源引用
    - MnemonicGeneratorAgent (ReAct): 记忆辅助生成（5种策略）
      -> 使用 backend.agents.react.mnemonic_generator_agent
    - KnowledgeAssessorAgent: 知识评估、理解水平判断
    - ProgressTrackerAgent: 进度跟踪、学习效率分析、路径推荐
    """
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行功能操作
        
        这是功能Agent的主入口方法，统一的调用接口。
        
        Args:
            input_data: 通用输入字典，具体结构由各Agent定义
        
        Returns:
            通用输出字典，具体结构由各Agent定义
        
        示例：
            # ContentValidatorAgent
            input_data = {
                "content_to_validate": "个人所得税免征额为5000元/月",
                "domain_context": "tax"
            }
            result = await validator.execute(input_data)
            # result = {
            #     "is_verified": True,
            #     "confidence_score": 0.95,
            #     "sources": [...]
            # }
            
            # MnemonicGeneratorAgent (ReAct版本)
            input_data = {
                "task_type": "generate_mnemonic",
                "concept_name": "财务健康比率",
                "explanation": "28-36规则...",
                "tenant_id": "...",
                "concept_id": "..."
            }
            # 使用: invoke_mnemonic_generator(agent, **input_data)
        """
        pass
    
    @abstractmethod
    def get_capability_info(self) -> CapabilityInfo:
        """
        返回Agent能力描述
        
        用于Agent注册、发现和文档生成。
        
        Returns:
            Agent能力信息对象
        
        示例：
            CapabilityInfo(
                agent_name="ContentValidator",
                capabilities=[
                    "online_search",
                    "content_verification",
                    "source_citation"
                ],
                input_schema={
                    "content_to_validate": "str",
                    "domain_context": "str"
                },
                output_schema={
                    "is_verified": "bool",
                    "confidence_score": "float",
                    "sources": "List[dict]"
                }
            )
        """
        pass
