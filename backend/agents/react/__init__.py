"""
ReAct Agent模块

基于LangGraph的ReAct模式独立Agent集合。
"""

from backend.agents.react.socratic_teacher_agent import (
    create_socratic_teacher_agent,
    invoke_socratic_teacher,
    SocraticTeacherState
)

from backend.agents.react.knowledge_assessor_agent import (
    create_knowledge_assessor_agent,
    invoke_knowledge_assessor,
    KnowledgeAssessorState
)

from backend.agents.react.progress_tracker_agent import (
    create_progress_tracker_agent,
    invoke_progress_tracker,
    ProgressTrackerState
)

from backend.agents.react.content_validator_agent import (
    create_content_validator_agent,
    invoke_content_validator,
    ContentValidatorState
)

from backend.agents.react.mnemonic_generator_agent import (
    create_mnemonic_generator_agent,
    invoke_mnemonic_generator,
    MnemonicGeneratorState
)

from backend.agents.react.mnemonic_models import (
    AcronymMnemonic,
    ComparisonTableMnemonic,
    AnalogyMnemonic,
    VisualMnemonic,
    NumberPatternMnemonic
)

__all__ = [
    # SocraticTeacher
    "create_socratic_teacher_agent",
    "invoke_socratic_teacher",
    "SocraticTeacherState",
    
    # KnowledgeAssessor
    "create_knowledge_assessor_agent",
    "invoke_knowledge_assessor",
    "KnowledgeAssessorState",
    
    # ProgressTracker
    "create_progress_tracker_agent",
    "invoke_progress_tracker",
    "ProgressTrackerState",
    
    # ContentValidator
    "create_content_validator_agent",
    "invoke_content_validator",
    "ContentValidatorState",
    
    # MnemonicGenerator
    "create_mnemonic_generator_agent",
    "invoke_mnemonic_generator",
    "MnemonicGeneratorState",
    
    # Mnemonic Models
    "AcronymMnemonic",
    "ComparisonTableMnemonic",
    "AnalogyMnemonic",
    "VisualMnemonic",
    "NumberPatternMnemonic"
]
