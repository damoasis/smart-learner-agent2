"""
MnemonicGenerator工具集 - 记忆辅助生成相关工具函数
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import re

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from backend.models.session import MnemonicDevice


@tool
def analyze_concept_features(
    concept_name: str, explanation: str
) -> Dict:
    """分析概念特征"""
    numbers = re.findall(r'\d+', explanation)
    return {
        "formulas_count": len(numbers),
        "has_comparison": "vs" in explanation or "对比" in explanation,
        "abstraction_level": "medium",
        "structure_type": "formula" if numbers else "relationship"
    }


@tool
def select_mnemonic_strategy(features: Dict) -> List[str]:
    """选择记忆策略"""
    strategies = []
    if features.get("formulas_count", 0) >= 3:
        strategies.append("acronym")
    if features.get("has_comparison"):
        strategies.append("comparison")
    if features.get("abstraction_level") == "high":
        strategies.append("analogy")
    return strategies or ["acronym"]


@tool
def generate_acronym(concepts: List[str]) -> Dict:
    """生成缩略词记忆"""
    import os
    from langchain_core.prompts import ChatPromptTemplate
    
    # 创建LLM实例
    llm = None
    try:
        llm = ChatOpenAI(model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    except:
        pass
    
    # 缩略词策略Prompt
    acronym_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位记忆策略专家，擅长创建易记的缩略词。

请为给定的概念列表创建缩略词记忆法。

要求：
1. 提取每个概念的首字母或关键字
2. 组合成朗朗上口的缩略词
3. 提供记忆口诀
4. 解释缩略词的含义

请以JSON格式返回，包含字段：acronym, full_terms, memory_tip, explanation"""),
        ("user", "概念列表：{concepts}")
    ])
    
    try:
        if llm:
            chain = acronym_prompt | llm
            response = chain.invoke({"concepts": ", ".join(concepts)})
            # 尝试解析LLM响应
            content = response.content if hasattr(response, 'content') else str(response)
            import json
            try:
                result = json.loads(content)
                return result
            except:
                pass
        
        # 降级处理：生成默认结果
        first_letters = ''.join([c[0] for c in concepts if c])
        return {
            "acronym": first_letters.upper(),
            "full_terms": concepts,
            "memory_tip": f"记住{first_letters.upper()}，每个字母代表一个要点",
            "explanation": f"{first_letters.upper()}分别代表：" + "、".join(concepts)
        }
    except Exception as e:
        # 错误处理
        first_letters = ''.join([c[0] for c in concepts if c])
        return {
            "acronym": first_letters.upper(),
            "full_terms": concepts,
            "memory_tip": f"记住{first_letters.upper()}",
            "explanation": "缩略词记忆"
        }


@tool
def generate_analogy(
    concept: str, explanation: str,
    learner_background: Optional[str] = None
) -> Dict:
    """生成类比记忆"""
    import os
    from langchain_core.prompts import ChatPromptTemplate
    
    # 创建LLM实例
    llm = None
    try:
        llm = ChatOpenAI(model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    except:
        pass
    
    # 类比法策略Prompt
    analogy_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位记忆策略专家，擅长用具体事物类比抽象概念。

请为抽象概念创建类比记忆法。

要求：
1. 分析概念的核心特征
2. 从日常生活寻找相似结构
3. 建立清晰的映射关系
4. 用自然语言解释类比
5. 说明类比的局限性

请以JSON格式返回，包含字段：abstract_concept, concrete_analogy, mapping, explanation, limitations"""),
        ("user", "抽象概念：{concept}\n概念解释：{explanation}\n学习者背景：{learner_background}")
    ])
    
    try:
        if llm:
            chain = analogy_prompt | llm
            response = chain.invoke({
                "concept": concept,
                "explanation": explanation,
                "learner_background": learner_background or "无特定背景"
            })
            content = response.content if hasattr(response, 'content') else str(response)
            import json
            try:
                result = json.loads(content)
                return result
            except:
                pass
        
        # 降级处理
        return {
            "abstract_concept": concept,
            "concrete_analogy": "日常生活中的类似事物",
            "mapping": {
                "抽象特征1": "具体特征1",
                "抽象特征2": "具体特征2"
            },
            "explanation": f"{concept}就像...",
            "limitations": "类比有局限性，实际情况可能更复杂"
        }
    except Exception as e:
        return {
            "abstract_concept": concept,
            "concrete_analogy": "日常类比",
            "mapping": {},
            "explanation": f"{concept}就像...",
            "limitations": "类比有局限"
        }


@tool
def generate_comparison(
    concepts: List[str], context: Optional[str] = None
) -> Dict:
    """生成对比表记忆"""
    import os
    from langchain_core.prompts import ChatPromptTemplate
    
    # 创建LLM实例
    llm = None
    try:
        llm = ChatOpenAI(model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    except:
        pass
    
    # 对比表策略Prompt
    comparison_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位记忆策略专家，擅长创建清晰的对比表格。

请为给定的概念创建对比表记忆法。

要求：
1. 识别关键对比维度
2. 提取每个概念在各维度的特征
3. 高亮关键差异
4. 提供表格标题

请以JSON格式返回，包含字段：table_title, items, dimensions (列表，每项包含name和values), key_differences"""),
        ("user", "待对比概念：{concepts}\n背景信息：{context}")
    ])
    
    try:
        if llm:
            chain = comparison_prompt | llm
            response = chain.invoke({
                "concepts": ", ".join(concepts),
                "context": context or "无"
            })
            content = response.content if hasattr(response, 'content') else str(response)
            import json
            try:
                result = json.loads(content)
                return result
            except:
                pass
        
        # 降级处理
        return {
            "table_title": f"{concepts[0]} vs {concepts[1]}对比" if len(concepts) >= 2 else "概念对比",
            "items": concepts,
            "dimensions": [
                {
                    "name": "特点",
                    "values": [f"{c}的特点" for c in concepts]
                },
                {
                    "name": "适用场景",
                    "values": [f"{c}适用场景" for c in concepts]
                }
            ],
            "key_differences": [f"{concepts[0]}与{concepts[1]}的关键区别"] if len(concepts) >= 2 else []
        }
    except Exception as e:
        return {
            "table_title": "对比表",
            "items": concepts,
            "dimensions": [],
            "key_differences": []
        }


@tool
def generate_visual(
    concept: str, concept_type: str = "flowchart"
) -> Dict:
    """生成视觉联想记忆"""
    import os
    from langchain_core.prompts import ChatPromptTemplate
    
    # 创建LLM实例
    llm = None
    try:
        llm = ChatOpenAI(model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    except:
        pass
    
    # 视觉联想策略Prompt
    visual_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位记忆策略专家，擅长创建视觉记忆辅助。

请为概念创建视觉联想记忆法。

要求：
1. 分析概念的结构（流程、层次、关系等）
2. 选择合适的视觉形式（流程图、思维导图等）
3. 生成Mermaid图表代码
4. 提供文字描述
5. 指导如何使用这个视觉记忆

请以JSON格式返回，包含字段：concept, visual_type, visual_description, key_elements, mermonic_diagram, usage_instruction"""),
        ("user", "概念：{concept}\n概念类型：{concept_type}")
    ])
    
    try:
        if llm:
            chain = visual_prompt | llm
            response = chain.invoke({
                "concept": concept,
                "concept_type": concept_type
            })
            content = response.content if hasattr(response, 'content') else str(response)
            import json
            try:
                result = json.loads(content)
                return result
            except:
                pass
        
        # 降级处理：生成简单的Mermaid流程图
        mermaid_diagram = f"""graph LR
    A[开始] --> B[{concept}]
    B --> C[理解]
    C --> D[记忆]"""
        
        return {
            "concept": concept,
            "visual_type": concept_type,
            "visual_description": f"想象{concept}的流程图",
            "key_elements": ["起点", "过程", "终点"],
            "mermonic_diagram": mermaid_diagram,
            "usage_instruction": "闭上眼睛，想象这个流程图，每个节点代表一个步骤"
        }
    except Exception as e:
        return {
            "concept": concept,
            "visual_type": concept_type,
            "visual_description": "视觉描述",
            "key_elements": [],
            "mermonic_diagram": None,
            "usage_instruction": "视觉记忆使用指导"
        }


@tool
def generate_number_pattern(
    rule_text: str
) -> Dict:
    """生成数字模式记忆"""
    import os
    from langchain_core.prompts import ChatPromptTemplate
    
    # 创建LLM实例
    llm = None
    try:
        llm = ChatOpenAI(model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    except:
        pass
    
    # 提取数字
    numbers = re.findall(r'\d+\.?\d*', rule_text)
    numbers_float = [float(n) for n in numbers]
    
    # 数字模式策略Prompt
    number_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位记忆策略专家，擅长创建数字记忆口诀。

请为包含数字的规则创建数字模式记忆法。

要求：
1. 提取所有关键数字
2. 识别数字规律（递增、对称、倍数等）
3. 创建朗朗上口的数字短语
4. 关联数字到实际意义
5. 提供使用指导

请以JSON格式返回，包含字段：numbers, pattern, memory_phrase, associations, usage_instruction"""),
        ("user", "规则内容：{rule_text}")
    ])
    
    try:
        if llm:
            chain = number_prompt | llm
            response = chain.invoke({"rule_text": rule_text})
            content = response.content if hasattr(response, 'content') else str(response)
            import json
            try:
                result = json.loads(content)
                return result
            except:
                pass
        
        # 降级处理：生成数字模式
        pattern = "-".join([str(int(n)) if n == int(n) else str(n) for n in numbers_float])
        memory_phrase = f"记住数字{pattern}"
        
        return {
            "numbers": numbers_float,
            "pattern": pattern,
            "memory_phrase": memory_phrase,
            "associations": {str(int(n) if n == int(n) else n): f"数字{n}的含义" for n in numbers_float},
            "usage_instruction": f"记住核心数字{pattern}，每个数字代表一个关键点"
        }
    except Exception as e:
        pattern = "-".join([str(int(n)) if n == int(n) else str(n) for n in numbers_float]) if numbers_float else "无数字"
        return {
            "numbers": numbers_float,
            "pattern": pattern,
            "memory_phrase": f"记住{pattern}",
            "associations": None,
            "usage_instruction": "数字模式记忆"
        }


@tool
def save_mnemonic_device(
    tenant_id: str, concept_id: str, strategy_type: str, 
    content: Dict, session: Session
) -> str:
    """保存记忆辅助"""
    from uuid import UUID as U
    
    m = MnemonicDevice(
        mnemonic_id=uuid4(),
        tenant_id=U(tenant_id),
        concept_id=U(concept_id),
        strategy_type=strategy_type,
        content=content,
        effectiveness_rating=0.8,
        usage_count=0
    )
    session.add(m)
    session.flush()
    return str(m.mnemonic_id)
