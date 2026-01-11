"""
Mnemonic数据模型

定义记忆辅助相关的Pydantic数据模型，用于类型校验和数据结构化。
这些模型从原有的mnemonic_generator.py迁移而来，供ReAct Agent使用。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AcronymMnemonic(BaseModel):
    """缩略词记忆"""
    acronym: str
    full_terms: List[str]
    memory_tip: str
    explanation: str


class ComparisonTableMnemonic(BaseModel):
    """对比表记忆"""
    table_title: str
    items: List[str]
    dimensions: List[Dict[str, Any]]
    key_differences: List[str]


class AnalogyMnemonic(BaseModel):
    """类比法记忆"""
    abstract_concept: str
    concrete_analogy: str
    mapping: Dict[str, str]
    explanation: str
    limitations: str


class VisualMnemonic(BaseModel):
    """视觉联想记忆"""
    concept: str
    visual_type: str
    visual_description: str
    key_elements: List[str]
    mermonic_diagram: Optional[str] = None
    usage_instruction: str


class NumberPatternMnemonic(BaseModel):
    """数字模式记忆"""
    numbers: List[float]
    pattern: str
    memory_phrase: str
    associations: Optional[Dict[str, str]] = None
    usage_instruction: str
