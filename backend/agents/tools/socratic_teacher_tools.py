"""
SocraticTeacher工具集 - 苏格拉底教学相关工具函数
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.services.vector_search import VectorSearchService


@tool
def evaluate_knowledge_baseline(
    question: str,
    initial_understanding: str,
    llm: Any = None
) -> dict:
    """评估学习者知识基线水平
    
    Args:
        question: 学习者提出的问题
        initial_understanding: 学习者的初始理解
        llm: LLM实例
    
    Returns:
        {"level": "beginner/intermediate/advanced", "assessment": "评估说明"}
    """
    if not llm:
        return {
            "level": "intermediate",
            "assessment": "未提供LLM实例，默认中级水平"
        }
    
    # 构建评估prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位经验丰富的教育专家，擅长评估学习者的知识水平。
请根据学习者的问题和初始理解，评估其对该主题的知识基线水平。

评估标准：
- beginner（初学者）：对该主题几乎没有了解，需要从基础概念开始
- intermediate（中级）：了解基本概念，但缺乏深入理解或实践经验
- advanced（高级）：已有扎实的理论基础，需要高级应用或细节澄清

请只返回以下JSON格式：
{{
  "level": "beginner/intermediate/advanced",
  "assessment": "简要评估说明（1-2句话）"
}}"""),
        ("user", """学习者问题：{question}

学习者的初始理解：{initial_understanding}

请评估该学习者的知识基线水平。""")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(
            question=question,
            initial_understanding=initial_understanding or "未提供"
        ))
        result = json.loads(response.content)
        return {
            "level": result.get("level", "intermediate"),
            "assessment": result.get("assessment", "")
        }
    except Exception as e:
        return {
            "level": "intermediate",
            "assessment": f"评估出错，默认中级水平: {str(e)}"
        }


@tool
def search_related_concepts(
    question: str,
    vector_search: Any,
    tenant_id: UUID,
    topic_id: Optional[UUID] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """向量检索相关概念
    
    Args:
        question: 学习者问题
        vector_search: 向量检索服务
        tenant_id: 租户ID
        topic_id: 主题ID（可选）
        top_k: 返回结果数量
    
    Returns:
        检索到的概念列表
    """
    if not vector_search:
        return []
    
    try:
        results = vector_search.search_similar_concepts(
            query_text=question,
            tenant_id=tenant_id,
            top_k=top_k,
            similarity_threshold=0.7,
            topic_id=topic_id
        )
        
        # 转换为字典格式
        concepts = []
        for concept, similarity in results:
            concepts.append({
                "concept_id": str(concept.concept_id),
                "concept_name": concept.concept_name,
                "explanation": concept.explanation,
                "formulas": concept.formulas,
                "rules": concept.rules,
                "similarity_score": similarity
            })
        
        return concepts
    except Exception as e:
        return []


@tool
def generate_socratic_explanation(
    question: str,
    retrieved_concepts: List[Dict[str, Any]],
    baseline_level: str,
    learner_preferences: Optional[Dict[str, Any]],
    llm: Optional[ChatOpenAI] = None,
    max_length: int = 200
) -> Dict[str, Any]:
    """生成苏格拉底式解释
    
    Args:
        question: 学习者问题
        retrieved_concepts: 检索到的相关概念
        baseline_level: 知识基线水平
        learner_preferences: 学习偏好
        llm: LLM实例
        max_length: 解释最大字数
    
    Returns:
        {"explanation": "生成的解释内容"}
    """
    if not llm:
        return {"explanation": "未提供LLM实例，无法生成解释"}
    
    # 格式化概念信息
    concepts_info = ""
    if retrieved_concepts:
        info_parts = []
        for i, concept in enumerate(retrieved_concepts[:3], 1):
            parts = [f"{i}. {concept.get('concept_name', '')}"]
            if concept.get('explanation'):
                parts.append(f"   解释：{concept['explanation']}")
            if concept.get('formulas'):
                parts.append(f"   公式：{concept['formulas']}")
            info_parts.append("\n".join(parts))
        concepts_info = "\n\n".join(info_parts)
    else:
        concepts_info = "未检索到相关概念"
    
    # 构建prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位采用苏格拉底教学法的优秀教师。你的目标是通过提问和引导，
帮助学习者自己理解概念，而不是直接给出答案。

教学原则：
1. 使用简明清晰的语言（约{max_length}字）
2. 包含具体实例帮助理解
3. 避免过于技术化的术语
4. 根据学习者水平调整深度
5. 鼓励批判性思考

学习者水平：{baseline_level}
学习者偏好：{preferences}"""),
        ("user", """学习者问题：{question}

相关概念信息：
{concepts_info}

请生成一个引导性的解释，帮助学习者理解这个概念。""")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(
            question=question,
            baseline_level=baseline_level,
            preferences=str(learner_preferences or {}),
            concepts_info=concepts_info,
            max_length=max_length
        ))
        return {"explanation": response.content.strip()}
    except Exception as e:
        return {"explanation": f"生成解释失败: {str(e)}"}


@tool
def generate_comprehension_questions(
    explanation: str,
    baseline_level: str,
    llm: Optional[ChatOpenAI] = None,
    num_questions: int = 2
) -> List[Dict[str, Any]]:
    """生成理解检查问题
    
    Args:
        explanation: 刚才的解释内容
        baseline_level: 知识基线水平
        llm: LLM实例
        num_questions: 问题数量
    
    Returns:
        问题列表 [{"question_text": "...", "expected_key_points": [...]}, ...]
    """
    if not llm:
        return [{
            "question_text": "请用你自己的话解释一下你刚才学到的内容。",
            "expected_key_points": []
        }]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位教育评估专家。你需要生成{num_questions}个开放式问题，
用于检查学习者是否真正理解了刚才讲解的概念。

问题设计原则：
1. 开放式问题，不是简单的是非题
2. 考察真实理解，而非死记硬背
3. 难度适中，与学习者水平匹配
4. 鼓励学习者用自己的话解释

请返回以下JSON格式：
{{
  "questions": [
    {{
      "question_text": "问题内容",
      "expected_key_points": ["关键点1", "关键点2"]
    }}
  ]
}}"""),
        ("user", """刚才讲解的内容：
{explanation}

学习者水平：{baseline_level}

请生成{num_questions}个理解检查问题。""")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(
            explanation=explanation,
            baseline_level=baseline_level,
            num_questions=num_questions
        ))
        result = json.loads(response.content)
        questions = result.get("questions", [])
        
        # 确保返回格式正确
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                "question_text": q.get("question_text", ""),
                "expected_key_points": q.get("expected_key_points", [])
            })
        
        return formatted_questions if formatted_questions else [{
            "question_text": "请用你自己的话解释一下你刚才学到的内容。",
            "expected_key_points": []
        }]
    except Exception as e:
        return [{
            "question_text": "请用你自己的话解释一下你刚才学到的内容。",
            "expected_key_points": []
        }]


@tool
def generate_adaptive_followup(
    question: str,
    previous_explanation: str,
    learner_response: str,
    misunderstandings: List[str],
    llm: Any = None
) -> Dict[str, Any]:
    """生成自适应跟进策略
    
    Args:
        question: 原始问题
        previous_explanation: 之前的解释
        learner_response: 学习者的回答
        misunderstandings: 识别的误解列表
        llm: LLM实例
    
    Returns:
        {"strategy": "策略类型", "followup_content": "跟进内容", "reasoning": "原因"}
    """
    if not llm:
        return {
            "strategy": "澄清法",
            "followup_content": "让我换一种方式来解释这个概念...",
            "reasoning": "提供替代解释"
        }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位善于调整教学策略的教师。学习者部分理解了概念，
但还有一些误解或不清楚的地方。

请选择最合适的跟进策略：
- 类比法：用生活中的类比帮助理解
- 分解法：将复杂概念分解为更小的部分
- 重新框架：从另一个角度解释概念
- 澄清法：针对具体误解进行澄清

请返回以下JSON格式：
{{
  "strategy": "类比法/分解法/重新框架/澄清法",
  "followup_content": "具体的跟进内容（约150字）",
  "reasoning": "选择该策略的原因（1句话）"
}}"""),
        ("user", """原始问题：{question}

之前的解释：{previous_explanation}

学习者的回答：{learner_response}

识别的误解：{misunderstandings}

请提供自适应跟进建议。""")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(
            question=question,
            previous_explanation=previous_explanation,
            learner_response=learner_response,
            misunderstandings=", ".join(misunderstandings) if misunderstandings else "无明确误解"
        ))
        result = json.loads(response.content)
        return {
            "strategy": result.get("strategy", "澄清法"),
            "followup_content": result.get("followup_content", ""),
            "reasoning": result.get("reasoning", "")
        }
    except Exception as e:
        return {
            "strategy": "澄清法",
            "followup_content": "让我换一种方式来解释这个概念...",
            "reasoning": f"生成失败，使用默认策略: {str(e)}"
        }
"""
SocraticTeacher工具集

将SocraticTeacher的方法提取为独立的@tool装饰函数
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from backend.services.vector_search import VectorSearchService
from backend.workflows.state import RetrievedConcept


@tool
def evaluate_knowledge_baseline(
    question: str,
    initial_understanding: str,
    llm: Any = None
) -> dict:
    """评估学习者知识基线水平
    
    Args:
        question: 学习者提出的问题
        initial_understanding: 学习者的初始理解
        llm: LLM实例（可选）
    
    Returns:
        {"level": "beginner/intermediate/advanced", "assessment": "评估说明"}
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
    
    baseline_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位经验丰富的教育专家，擅长评估学习者的知识水平。
请根据学习者的问题和初始理解，评估其对该主题的知识基线水平。

评估标准：
- beginner（初学者）：对该主题几乎没有了解，需要从基础概念开始
- intermediate（中级）：了解基本概念，但缺乏深入理解或实践经验
- advanced（高级）：已有扎实的理论基础，需要高级应用或细节澄清

请只返回以下JSON格式：
{{
  "level": "beginner/intermediate/advanced",
  "assessment": "简要评估说明（1-2句话）"
}}"""),
        ("user", """学习者问题：{question}

学习者的初始理解：{initial_understanding}

请评估该学习者的知识基线水平。""")
    ])
    
    prompt = baseline_prompt.format_messages(
        question=question,
        initial_understanding=initial_understanding
    )
    
    response = llm.invoke(prompt)
    
    try:
        import json
        result = json.loads(response.content)
        return result
    except Exception:
        return {
            "level": "intermediate",
            "assessment": "评估解析失败，默认为中级水平"
        }


@tool
def search_related_concepts(
    query: str,
    vector_search: Any,
    tenant_id: UUID,
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """向量检索相关概念
    
    Args:
        query: 检索查询
        vector_search: 向量检索服务
        tenant_id: 租户ID
        top_k: 返回结果数量
        similarity_threshold: 相似度阈值
    
    Returns:
        相关概念列表
    """
    results = vector_search.search_concepts(
        query_text=query,
        tenant_id=tenant_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
    
    return [
        {
            "concept_id": str(result["concept_id"]),
            "concept_name": result["concept_name"],
            "explanation": result.get("explanation"),
            "formulas": result.get("formulas"),
            "rules": result.get("rules"),
            "similarity_score": result["similarity_score"]
        }
        for result in results
    ]


@tool
def generate_socratic_explanation(
    question: str,
    concepts_info: List[Dict[str, Any]],
    baseline_level: str,
    max_length: int = 200,
    preferences: Optional[Dict[str, Any]] = None,
    llm: Any = None
) -> str:
    """生成苏格拉底式解释
    
    Args:
        question: 学习者问题
        concepts_info: 相关概念信息
        baseline_level: 基线水平
        max_length: 最大字数
        preferences: 学习者偏好
        llm: LLM实例
    
    Returns:
        引导性解释文本
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7,
            max_tokens=500
        )
    
    # 构建概念信息文本
    concepts_text = "\n".join([
        f"- {c['concept_name']}: {c.get('explanation', '无说明')}"
        for c in concepts_info[:3]
    ])
    
    preferences_text = str(preferences) if preferences else "无特定偏好"
    
    explanation_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位采用苏格拉底教学法的优秀教师。你的目标是通过提问和引导，
帮助学习者自己理解概念，而不是直接给出答案。

教学原则：
1. 使用简明清晰的语言（约{max_length}字）
2. 包含具体实例帮助理解
3. 避免过于技术化的术语
4. 根据学习者水平调整深度
5. 鼓励批判性思考

学习者水平：{baseline_level}
学习者偏好：{preferences}"""),
        ("user", """学习者问题：{question}

相关概念信息：
{concepts_info}

请生成一个引导性的解释，帮助学习者理解这个概念。""")
    ])
    
    prompt = explanation_prompt.format_messages(
        max_length=max_length,
        baseline_level=baseline_level,
        preferences=preferences_text,
        question=question,
        concepts_info=concepts_text
    )
    
    response = llm.invoke(prompt)
    return response.content


@tool
def generate_comprehension_questions(
    explanation: str,
    baseline_level: str,
    num_questions: int = 2,
    llm: Any = None
) -> List[Dict[str, Any]]:
    """生成理解检查问题
    
    Args:
        explanation: 刚才讲解的内容
        baseline_level: 基线水平
        num_questions: 问题数量
        llm: LLM实例
    
    Returns:
        [{"question_text": "...", "expected_key_points": [...]}]
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
    
    comprehension_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位教育评估专家。你需要生成{num_questions}个开放式问题，
用于检查学习者是否真正理解了刚才讲解的概念。

问题设计原则：
1. 开放式问题，不是简单的是非题
2. 考察真实理解，而非死记硬背
3. 难度适中，与学习者水平匹配
4. 鼓励学习者用自己的话解释

请返回以下JSON格式：
{{
  "questions": [
    {{
      "question_text": "问题内容",
      "expected_key_points": ["关键点1", "关键点2"]
    }}
  ]
}}"""),
        ("user", """刚才讲解的内容：
{explanation}

学习者水平：{baseline_level}

请生成{num_questions}个理解检查问题。""")
    ])
    
    prompt = comprehension_prompt.format_messages(
        num_questions=num_questions,
        explanation=explanation,
        baseline_level=baseline_level
    )
    
    response = llm.invoke(prompt)
    
    try:
        import json
        result = json.loads(response.content)
        return result.get("questions", [])
    except Exception:
        return [{
            "question_text": "请用自己的话解释一下你理解到的核心概念？",
            "expected_key_points": []
        }]


@tool
def generate_adaptive_followup(
    question: str,
    previous_explanation: str,
    learner_response: str,
    misunderstandings: List[str],
    llm: Any = None
) -> Dict[str, str]:
    """生成自适应跟进策略
    
    Args:
        question: 原始问题
        previous_explanation: 之前的解释
        learner_response: 学习者的回答
        misunderstandings: 识别的误解列表
        llm: LLM实例
    
    Returns:
        {"strategy": "策略名称", "followup_content": "跟进内容", "reasoning": "原因"}
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
    
    followup_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位善于调整教学策略的教师。学习者部分理解了概念，
但还有一些误解或不清楚的地方。

请选择最合适的跟进策略：
- 类比法：用生活中的类比帮助理解
- 分解法：将复杂概念分解为更小的部分
- 重新框架：从另一个角度解释概念
- 澄清法：针对具体误解进行澄清

请返回以下JSON格式：
{{
  "strategy": "类比法/分解法/重新框架/澄清法",
  "followup_content": "具体的跟进内容（约150字）",
  "reasoning": "选择该策略的原因（1句话）"
}}"""),
        ("user", """原始问题：{question}

之前的解释：{previous_explanation}

学习者的回答：{learner_response}

识别的误解：{misunderstandings}

请提供自适应跟进建议。""")
    ])
    
    misunderstandings_text = ", ".join(misunderstandings) if misunderstandings else "无明显误解"
    
    prompt = followup_prompt.format_messages(
        question=question,
        previous_explanation=previous_explanation,
        learner_response=learner_response,
        misunderstandings=misunderstandings_text
    )
    
    response = llm.invoke(prompt)
    
    try:
        import json
        result = json.loads(response.content)
        return result
    except Exception:
        return {
            "strategy": "澄清法",
            "followup_content": "让我换一个角度来解释...",
            "reasoning": "需要进一步澄清概念"
        }
"""
SocraticTeacher工具集

将SocraticTeacher的方法提取为独立的@tool装饰函数
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from backend.services.vector_search import VectorSearchService
from backend.workflows.state import RetrievedConcept


@tool
def evaluate_knowledge_baseline(
    question: str,
    initial_understanding: str,
    llm: Any = None
) -> dict:
    """评估学习者知识基线水平
    
    Args:
        question: 学习者提出的问题
        initial_understanding: 学习者的初始理解
        llm: LLM实例（可选）
    
    Returns:
        {"level": "beginner/intermediate/advanced", "assessment": "评估说明"}
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
    
    baseline_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位经验丰富的教育专家，擅长评估学习者的知识水平。
请根据学习者的问题和初始理解，评估其对该主题的知识基线水平。

评估标准：
- beginner（初学者）：对该主题几乎没有了解，需要从基础概念开始
- intermediate（中级）：了解基本概念，但缺乏深入理解或实践经验
- advanced（高级）：已有扎实的理论基础，需要高级应用或细节澄清

请只返回以下JSON格式：
{{
  "level": "beginner/intermediate/advanced",
  "assessment": "简要评估说明（1-2句话）"
}}"""),
        ("user", """学习者问题：{question}

学习者的初始理解：{initial_understanding}

请评估该学习者的知识基线水平。""")
    ])
    
    prompt = baseline_prompt.format_messages(
        question=question,
        initial_understanding=initial_understanding
    )
    
    response = llm.invoke(prompt)
    
    try:
        import json
        result = json.loads(response.content)
        return result
    except Exception:
        return {
            "level": "intermediate",
            "assessment": "评估解析失败，默认为中级水平"
        }


@tool
def search_related_concepts(
    query: str,
    vector_search: Any,
    tenant_id: UUID,
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """向量检索相关概念
    
    Args:
        query: 检索查询
        vector_search: 向量检索服务
        tenant_id: 租户ID
        top_k: 返回结果数量
        similarity_threshold: 相似度阈值
    
    Returns:
        相关概念列表
    """
    results = vector_search.search_concepts(
        query_text=query,
        tenant_id=tenant_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
    
    return [
        {
            "concept_id": str(result["concept_id"]),
            "concept_name": result["concept_name"],
            "explanation": result.get("explanation"),
            "formulas": result.get("formulas"),
            "rules": result.get("rules"),
            "similarity_score": result["similarity_score"]
        }
        for result in results
    ]


@tool
def generate_socratic_explanation(
    question: str,
    concepts_info: List[Dict[str, Any]],
    baseline_level: str,
    max_length: int = 200,
    preferences: Optional[Dict[str, Any]] = None,
    llm: Any = None
) -> str:
    """生成苏格拉底式解释
    
    Args:
        question: 学习者问题
        concepts_info: 相关概念信息
        baseline_level: 基线水平
        max_length: 最大字数
        preferences: 学习者偏好
        llm: LLM实例
    
    Returns:
        引导性解释文本
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7,
            max_tokens=500
        )
    
    # 构建概念信息文本
    concepts_text = "\n".join([
        f"- {c['concept_name']}: {c.get('explanation', '无说明')}"
        for c in concepts_info[:3]
    ])
    
    preferences_text = str(preferences) if preferences else "无特定偏好"
    
    explanation_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位采用苏格拉底教学法的优秀教师。你的目标是通过提问和引导，
帮助学习者自己理解概念，而不是直接给出答案。

教学原则：
1. 使用简明清晰的语言（约{max_length}字）
2. 包含具体实例帮助理解
3. 避免过于技术化的术语
4. 根据学习者水平调整深度
5. 鼓励批判性思考

学习者水平：{baseline_level}
学习者偏好：{preferences}"""),
        ("user", """学习者问题：{question}

相关概念信息：
{concepts_info}

请生成一个引导性的解释，帮助学习者理解这个概念。""")
    ])
    
    prompt = explanation_prompt.format_messages(
        max_length=max_length,
        baseline_level=baseline_level,
        preferences=preferences_text,
        question=question,
        concepts_info=concepts_text
    )
    
    response = llm.invoke(prompt)
    return response.content


@tool
def generate_comprehension_questions(
    explanation: str,
    baseline_level: str,
    num_questions: int = 2,
    llm: Any = None
) -> List[Dict[str, Any]]:
    """生成理解检查问题
    
    Args:
        explanation: 刚才讲解的内容
        baseline_level: 基线水平
        num_questions: 问题数量
        llm: LLM实例
    
    Returns:
        [{"question_text": "...", "expected_key_points": [...]}]
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
    
    comprehension_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位教育评估专家。你需要生成{num_questions}个开放式问题，
用于检查学习者是否真正理解了刚才讲解的概念。

问题设计原则：
1. 开放式问题，不是简单的是非题
2. 考察真实理解，而非死记硬背
3. 难度适中，与学习者水平匹配
4. 鼓励学习者用自己的话解释

请返回以下JSON格式：
{{
  "questions": [
    {{
      "question_text": "问题内容",
      "expected_key_points": ["关键点1", "关键点2"]
    }}
  ]
}}"""),
        ("user", """刚才讲解的内容：
{explanation}

学习者水平：{baseline_level}

请生成{num_questions}个理解检查问题。""")
    ])
    
    prompt = comprehension_prompt.format_messages(
        num_questions=num_questions,
        explanation=explanation,
        baseline_level=baseline_level
    )
    
    response = llm.invoke(prompt)
    
    try:
        import json
        result = json.loads(response.content)
        return result.get("questions", [])
    except Exception:
        return [{
            "question_text": "请用自己的话解释一下你理解到的核心概念？",
            "expected_key_points": []
        }]


@tool
def generate_adaptive_followup(
    question: str,
    previous_explanation: str,
    learner_response: str,
    misunderstandings: List[str],
    llm: Any = None
) -> Dict[str, str]:
    """生成自适应跟进策略
    
    Args:
        question: 原始问题
        previous_explanation: 之前的解释
        learner_response: 学习者的回答
        misunderstandings: 识别的误解列表
        llm: LLM实例
    
    Returns:
        {"strategy": "策略名称", "followup_content": "跟进内容", "reasoning": "原因"}
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
    
    followup_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位善于调整教学策略的教师。学习者部分理解了概念，
但还有一些误解或不清楚的地方。

请选择最合适的跟进策略：
- 类比法：用生活中的类比帮助理解
- 分解法：将复杂概念分解为更小的部分
- 重新框架：从另一个角度解释概念
- 澄清法：针对具体误解进行澄清

请返回以下JSON格式：
{{
  "strategy": "类比法/分解法/重新框架/澄清法",
  "followup_content": "具体的跟进内容（约150字）",
  "reasoning": "选择该策略的原因（1句话）"
}}"""),
        ("user", """原始问题：{question}

之前的解释：{previous_explanation}

学习者的回答：{learner_response}

识别的误解：{misunderstandings}

请提供自适应跟进建议。""")
    ])
    
    misunderstandings_text = ", ".join(misunderstandings) if misunderstandings else "无明显误解"
    
    prompt = followup_prompt.format_messages(
        question=question,
        previous_explanation=previous_explanation,
        learner_response=learner_response,
        misunderstandings=misunderstandings_text
    )
    
    response = llm.invoke(prompt)
    
    try:
        import json
        result = json.loads(response.content)
        return result
    except Exception:
        return {
            "strategy": "澄清法",
            "followup_content": "让我换一个角度来解释...",
            "reasoning": "需要进一步澄清概念"
        }
