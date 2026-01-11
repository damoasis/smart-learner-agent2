"""
Agent基础接口层

该模块定义了所有Agent的统一接口，支持可插拔的架构设计。
"""

from backend.agents.base.teaching_agent_interface import (
    TeachingAgentInterface,
    TeachingModeInfo,
    TeachingContext,
    LearnerProfile,
    LearningHistory,
    SessionInfo,
    TenantConfig
)

from backend.agents.base.utility_agent_interface import (
    UtilityAgentInterface,
    CapabilityInfo
)

__all__ = [
    # 教学Agent接口
    "TeachingAgentInterface",
    "TeachingModeInfo",
    "TeachingContext",
    "LearnerProfile",
    "LearningHistory",
    "SessionInfo",
    "TenantConfig",
    
    # 功能Agent接口
    "UtilityAgentInterface",
    "CapabilityInfo",
]
