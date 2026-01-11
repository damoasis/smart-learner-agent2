"""
教学Agent统一接口

该模块定义了所有教学Agent必须实现的接口，支持多种教学模式的可插拔设计。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from backend.workflows.state import TeachingState


class LearnerProfile(BaseModel):
    """学习者档案"""
    learner_id: UUID
    native_language: str = Field(default="zh-CN", description="母语")
    learning_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="学习偏好（视觉/听觉/阅读等）"
    )
    baseline_level: str = Field(
        default="intermediate",
        description="基线水平（beginner/intermediate/advanced）"
    )
    mastered_topics: List[UUID] = Field(
        default_factory=list,
        description="已掌握的主题ID列表"
    )
    struggle_areas: List[str] = Field(
        default_factory=list,
        description="薄弱领域"
    )


class LearningHistory(BaseModel):
    """学习历史"""
    first_time_correct_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="首次正确率"
    )
    average_retry_count: float = Field(
        default=0.0,
        ge=0.0,
        description="平均重试次数"
    )
    preferred_teaching_modes: List[str] = Field(
        default_factory=list,
        description="历史表现好的教学模式"
    )
    total_learning_hours: float = Field(
        default=0.0,
        ge=0.0,
        description="总学习时长（小时）"
    )


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: UUID
    start_time: str
    current_stage: str = Field(default="initialized", description="当前阶段")
    interaction_count: int = Field(default=0, description="交互次数")


class TenantConfig(BaseModel):
    """租户配置"""
    tenant_id: UUID
    default_teaching_mode: Optional[str] = Field(
        default=None,
        description="默认教学模式"
    )
    force_teaching_mode: Optional[str] = Field(
        default=None,
        description="强制教学模式（如果设置，忽略自适应选择）"
    )
    enable_content_validation: bool = Field(
        default=True,
        description="是否启用内容验证"
    )
    enable_mnemonic_generation: bool = Field(
        default=True,
        description="是否启用记忆辅助生成"
    )


class TeachingContext(BaseModel):
    """教学场景上下文"""
    topic: Any = Field(..., description="当前主题对象（Topic模型）")
    learner_profile: LearnerProfile
    learning_history: LearningHistory
    session_info: SessionInfo
    tenant_config: TenantConfig
    
    class Config:
        arbitrary_types_allowed = True


class TeachingModeInfo(BaseModel):
    """教学模式元数据"""
    mode_id: UUID
    mode_name: str = Field(..., description="模式名称（如socratic、lecture等）")
    mode_type: str = Field(
        ...,
        description="模式类型（interactive/passive/hybrid）"
    )
    description: str = Field(..., description="模式描述")
    applicable_scenarios: List[str] = Field(
        default_factory=list,
        description="适用场景列表"
    )


class TeachingAgentInterface(ABC):
    """
    教学Agent统一接口
    
    所有教学Agent（苏格拉底式、讲授式、案例式等）必须实现此接口。
    
    核心方法：
    - teach(): 执行完整的教学逻辑
    - get_mode_info(): 返回教学模式元数据
    - is_suitable_for(): 计算对当前场景的适配度
    - generate_explanation(): 生成教学解释
    - generate_check_questions(): 生成理解检查问题
    """
    
    @abstractmethod
    def teach(self, state: TeachingState) -> TeachingState:
        """
        执行教学逻辑
        
        这是教学Agent的主入口方法，包含完整的教学循环。
        
        Args:
            state: 当前教学状态
        
        Returns:
            更新后的教学状态
        """
        pass
    
    @abstractmethod
    def get_mode_info(self) -> TeachingModeInfo:
        """
        返回教学模式元数据
        
        用于教学模式选择和展示。
        
        Returns:
            教学模式元数据对象
        """
        pass
    
    @abstractmethod
    def is_suitable_for(self, context: TeachingContext) -> float:
        """
        计算对当前场景的适配度
        
        用于帮助ConversationManager选择最合适的教学Agent。
        
        Args:
            context: 教学场景上下文
        
        Returns:
            适配度评分（0.0-1.0），越高表示越适合
        """
        pass
    
    @abstractmethod
    def generate_explanation(self, state: TeachingState) -> str:
        """
        生成教学解释
        
        每个教学模式的解释风格不同：
        - 苏格拉底式：引导式、约200字
        - 讲授式：结构化、300-500字
        
        Args:
            state: 当前教学状态（包含问题、检索到的概念）
        
        Returns:
            解释文本
        """
        pass
    
    @abstractmethod
    def generate_check_questions(self, state: TeachingState) -> List[str]:
        """
        生成理解检查问题
        
        不同模式检查方式不同：
        - 苏格拉底式：1-2个开放式问题
        - 讲授式：3-5个混合问题（开放式+选择题）
        
        Args:
            state: 当前教学状态
        
        Returns:
            问题文本列表
        """
        pass
