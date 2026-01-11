"""
KnowledgeAssessor工具集 - 知识评估相关工具函数
"""

from typing import List, Dict, Any, Optional
import json

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


@tool
def extract_key_points(
    learner_response: str,
    expected_key_points: List[str],
    llm: Optional[ChatOpenAI] = None
) -> List[str]:
    """从学习者回答中提取关键点
    
    Args:
        learner_response: 学习者的回答
        expected_key_points: 期望的关键点列表
        llm: LLM实例
    
    Returns:
        提取的关键点列表
    """
    if not llm or not learner_response:
        return []
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位教育评估专家。请从学习者的回答中提取关键点。

请返回以下JSON格式：
{{
  "key_points": ["关键点1", "关键点2", ...]
}}"""),
        ("user", """学习者回答：{learner_response}

期望的关键点参考：{expected_key_points}

请提取学习者回答中的关键点。""")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(
            learner_response=learner_response,
            expected_key_points=", ".join(expected_key_points) if expected_key_points else "无明确期望"
        ))
        result = json.loads(response.content)
        return result.get("key_points", [])
    except Exception:
        return []


@tool
def identify_misunderstandings(
    learner_response: str,
    expected_key_points: List[str],
    explanation: str
) -> List[str]:
    """识别学习者回答中的误解
    
    Args:
        learner_response: 学习者的回答
        expected_key_points: 期望的关键点
        explanation: 原始解释内容
    
    Returns:
        识别到的误解列表
    """
    if not learner_response:
        return ["未提供回答"]
    
    # 简单规则检测
    misunderstandings = []
    
    # 检查回答长度
    if len(learner_response.strip()) < 10:
        misunderstandings.append("回答过于简短")
    
    # 检查消极关键词
    negative_keywords = ["不知道", "不理解", "不懂", "不清楚", "没听懂", "不会"]
    if any(kw in learner_response for kw in negative_keywords):
        misunderstandings.append("明确表示不理解")
    
    return misunderstandings


@tool
def assess_understanding_level(
    learner_response: str,
    key_points_understood: List[str],
    misunderstandings: List[str],
    expected_key_points: List[str]
) -> str:
    """评估理解水平
    
    Args:
        learner_response: 学习者回答
        key_points_understood: 已理解的关键点
        misunderstandings: 误解列表
        expected_key_points: 期望的关键点
    
    Returns:
        "fully_understood" | "partially_understood" | "not_understood"
    """
    # 空回答或过短
    if not learner_response or len(learner_response.strip()) < 10:
        return "not_understood"
    
    # 有明显误解
    if misunderstandings and len(misunderstandings) > 0:
        critical_misunderstandings = [m for m in misunderstandings if "明确表示不理解" in m or "完全错误" in m]
        if critical_misunderstandings:
            return "not_understood"
    
    # 比较理解的关键点数量
    if expected_key_points and key_points_understood:
        understood_ratio = len(key_points_understood) / max(len(expected_key_points), 1)
        if understood_ratio >= 0.8:
            return "fully_understood"
        elif understood_ratio >= 0.5:
            return "partially_understood"
        else:
            return "not_understood"
    
    # 默认评估
    if len(learner_response.strip()) > 50:
        return "partially_understood"
    else:
        return "not_understood"


@tool
def decide_next_action(
    assessment_result: str,
    retry_count: int,
    max_retries: int
) -> str:
    """决定下一步行动
    
    Args:
        assessment_result: 评估结果 (fully_understood|partially_understood|not_understood)
        retry_count: 当前重试次数
        max_retries: 最大重试次数
    
    Returns:
        "continue" | "adaptive_followup" | "retry" | "record_gap"
    """
    # 完全理解：继续下一个主题
    if assessment_result == "fully_understood":
        return "continue"
    
    # 部分理解：提供自适应跟进
    if assessment_result == "partially_understood":
        return "adaptive_followup"
    
    # 不理解：检查重试次数
    if assessment_result == "not_understood":
        if retry_count < max_retries:
            return "retry"
        else:
            return "record_gap"
    
    # 默认继续
    return "continue"


@tool
def calibrate_confidence_level(
    assessment_result: str,
    retry_count: int
) -> str:
    """校准信心等级
    
    Args:
        assessment_result: 评估结果
        retry_count: 重试次数
    
    Returns:
        "low" | "medium" | "medium_high" | "high"
    """
    # 基于评估结果和重试次数确定信心等级
    if assessment_result == "fully_understood":
        if retry_count == 0:
            return "high"  # 首次正确
        elif retry_count == 1:
            return "medium_high"  # 第二次正确
        else:
            return "medium"  # 多次尝试后正确
    
    elif assessment_result == "partially_understood":
        if retry_count <= 1:
            return "medium"
        else:
            return "low"
    
    elif assessment_result == "not_understood":
        if retry_count >= 2:
            return "low"  # 多次尝试仍不理解
        else:
            return "medium"  # 首次或第二次不理解
    
    return "medium"
"""
KnowledgeAssessor工具集

将KnowledgeAssessor的方法提取为独立的@tool装饰函数
"""

from typing import List, Dict, Any, Optional

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def extract_key_points(
    learner_response: str,
    llm: Optional[ChatOpenAI] = None
) -> List[str]:
    """提取学习者回答中的关键点
    
    Args:
        learner_response: 学习者的回答
        llm: LLM实例
    
    Returns:
        关键点列表
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3
        )
    
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位专业的教育评估专家。请提取学习者回答中提到的关键概念和要点。

返回JSON格式：
{{
  "key_points": ["关键点1", "关键点2", "..."]
}}"""),
        ("user", f"学习者回答：{learner_response}\n\n请提取关键点。")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    try:
        import json
        result = json.loads(response.content)
        return result.get("key_points", [])
    except Exception:
        # 简单分句作为备选
        sentences = learner_response.split("。")
        return [s.strip() for s in sentences if len(s.strip()) > 5][:3]


@tool
def identify_misunderstandings(
    learner_response: str,
    expected_key_points: List[str],
    explanation: str,
    llm: Optional[ChatOpenAI] = None
) -> List[str]:
    """识别学习者回答中的误解
    
    Args:
        learner_response: 学习者的回答
        expected_key_points: 期望的关键点
        explanation: 原始解释
        llm: LLM实例
    
    Returns:
        误解列表
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3
        )
    
    from langchain_core.prompts import ChatPromptTemplate
    
    expected_text = ", ".join(expected_key_points) if expected_key_points else "无特定期望"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位专业的教育评估专家。请识别学习者回答中的误解或不准确之处。

返回JSON格式：
{{
  "misunderstandings": ["误解1", "误解2", "..."]
}}

如果没有明显误解，返回空列表。"""),
        ("user", f"""原始解释：{explanation}

期望关键点：{expected_text}

学习者回答：{learner_response}

请识别误解。""")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    try:
        import json
        result = json.loads(response.content)
        return result.get("misunderstandings", [])
    except Exception:
        return []


@tool
def assess_understanding_level(
    key_points_understood: List[str],
    misunderstandings: List[str],
    expected_key_points: List[str],
    learner_response: str
) -> Dict[str, Any]:
    """评估理解水平
    
    Args:
        key_points_understood: 学习者理解的关键点
        misunderstandings: 识别的误解
        expected_key_points: 期望的关键点
        learner_response: 学习者回答
    
    Returns:
        {
            "assessment_result": "fully_understood/partially_understood/not_understood",
            "confidence_level": "low/medium/medium_high/high",
            "assessment_details": "评估说明"
        }
    """
    # 规则评估
    
    # 1. 空回答或过短
    if not learner_response or len(learner_response.strip()) < 10:
        return {
            "assessment_result": "not_understood",
            "confidence_level": "low",
            "assessment_details": "回答过于简短，无法判断理解程度"
        }
    
    # 2. 包含"不知道"等关键词
    negative_keywords = ["不知道", "不理解", "不懂", "不清楚", "没听懂"]
    if any(kw in learner_response for kw in negative_keywords):
        return {
            "assessment_result": "not_understood",
            "confidence_level": "low",
            "assessment_details": "学习者明确表示不理解"
        }
    
    # 3. 计算覆盖率
    coverage = 0.0
    if expected_key_points:
        covered = len([kp for kp in key_points_understood if any(exp in kp for exp in expected_key_points)])
        coverage = covered / len(expected_key_points)
    else:
        # 如果没有期望关键点，基于回答长度和关键点数量判断
        coverage = min(len(key_points_understood) / 3.0, 1.0)
    
    # 4. 考虑误解数量
    has_serious_misunderstanding = len(misunderstandings) >= 2
    has_minor_misunderstanding = len(misunderstandings) == 1
    
    # 5. 综合判断
    if coverage >= 0.8 and not has_serious_misunderstanding:
        return {
            "assessment_result": "fully_understood",
            "confidence_level": "high" if coverage >= 0.9 else "medium_high",
            "assessment_details": "学习者充分理解了核心概念"
        }
    elif coverage >= 0.5 or (coverage >= 0.3 and not has_serious_misunderstanding):
        return {
            "assessment_result": "partially_understood",
            "confidence_level": "medium" if has_minor_misunderstanding else "medium_high",
            "assessment_details": "学习者理解了主要概念，但有部分细节不清楚"
        }
    else:
        return {
            "assessment_result": "not_understood",
            "confidence_level": "low" if has_serious_misunderstanding else "medium",
            "assessment_details": "学习者对概念的理解不足，需要重新讲解"
        }


@tool
def decide_next_action(
    assessment_result: str,
    retry_count: int,
    max_retries: int = 3
) -> str:
    """决定下一步行动
    
    Args:
        assessment_result: 评估结果
        retry_count: 当前重试次数
        max_retries: 最大重试次数
    
    Returns:
        "continue" | "adaptive_followup" | "retry" | "record_gap"
    """
    if assessment_result == "fully_understood":
        return "continue"
    
    elif assessment_result == "partially_understood":
        return "adaptive_followup"
    
    elif assessment_result == "not_understood":
        if retry_count < max_retries:
            return "retry"
        else:
            return "record_gap"
    
    else:
        # 未知评估结果，默认继续
        return "continue"
"""
KnowledgeAssessor工具集

将KnowledgeAssessor的方法提取为独立的@tool装饰函数
"""

from typing import List, Dict, Any, Optional

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def extract_key_points(
    learner_response: str,
    llm: Optional[Any] = None
) -> List[str]:
    """提取学习者回答中的关键点
    
    Args:
        learner_response: 学习者的回答
        llm: LLM实例
    
    Returns:
        关键点列表
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3
        )
    
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位专业的教育评估专家。请提取学习者回答中提到的关键概念和要点。

返回JSON格式：
{{
  "key_points": ["关键点1", "关键点2", "..."]
}}"""),
        ("user", f"学习者回答：{learner_response}\n\n请提取关键点。")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    try:
        import json
        result = json.loads(response.content)
        return result.get("key_points", [])
    except Exception:
        # 简单分句作为备选
        sentences = learner_response.split("。")
        return [s.strip() for s in sentences if len(s.strip()) > 5][:3]


@tool
def identify_misunderstandings(
    learner_response: str,
    expected_key_points: List[str],
    explanation: str,
    llm: Optional[Any] = None
) -> List[str]:
    """识别学习者回答中的误解
    
    Args:
        learner_response: 学习者的回答
        expected_key_points: 期望的关键点
        explanation: 原始解释
        llm: LLM实例
    
    Returns:
        误解列表
    """
    if llm is None:
        import os
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3
        )
    
    from langchain_core.prompts import ChatPromptTemplate
    
    expected_text = ", ".join(expected_key_points) if expected_key_points else "无特定期望"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位专业的教育评估专家。请识别学习者回答中的误解或不准确之处。

返回JSON格式：
{{
  "misunderstandings": ["误解1", "误解2", "..."]
}}

如果没有明显误解，返回空列表。"""),
        ("user", f"""原始解释：{explanation}

期望关键点：{expected_text}

学习者回答：{learner_response}

请识别误解。""")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    try:
        import json
        result = json.loads(response.content)
        return result.get("misunderstandings", [])
    except Exception:
        return []


@tool
def assess_understanding_level(
    key_points_understood: List[str],
    misunderstandings: List[str],
    expected_key_points: List[str],
    learner_response: str
) -> Dict[str, Any]:
    """评估理解水平
    
    Args:
        key_points_understood: 学习者理解的关键点
        misunderstandings: 识别的误解
        expected_key_points: 期望的关键点
        learner_response: 学习者回答
    
    Returns:
        {
            "assessment_result": "fully_understood/partially_understood/not_understood",
            "confidence_level": "low/medium/medium_high/high",
            "assessment_details": "评估说明"
        }
    """
    # 规则评估
    
    # 1. 空回答或过短
    if not learner_response or len(learner_response.strip()) < 10:
        return {
            "assessment_result": "not_understood",
            "confidence_level": "low",
            "assessment_details": "回答过于简短，无法判断理解程度"
        }
    
    # 2. 包含"不知道"等关键词
    negative_keywords = ["不知道", "不理解", "不懂", "不清楚", "没听懂"]
    if any(kw in learner_response for kw in negative_keywords):
        return {
            "assessment_result": "not_understood",
            "confidence_level": "low",
            "assessment_details": "学习者明确表示不理解"
        }
    
    # 3. 计算覆盖率
    coverage = 0.0
    if expected_key_points:
        covered = len([kp for kp in key_points_understood if any(exp in kp for exp in expected_key_points)])
        coverage = covered / len(expected_key_points)
    else:
        # 如果没有期望关键点，基于回答长度和关键点数量判断
        coverage = min(len(key_points_understood) / 3.0, 1.0)
    
    # 4. 考虑误解数量
    has_serious_misunderstanding = len(misunderstandings) >= 2
    has_minor_misunderstanding = len(misunderstandings) == 1
    
    # 5. 综合判断
    if coverage >= 0.8 and not has_serious_misunderstanding:
        return {
            "assessment_result": "fully_understood",
            "confidence_level": "high" if coverage >= 0.9 else "medium_high",
            "assessment_details": "学习者充分理解了核心概念"
        }
    elif coverage >= 0.5 or (coverage >= 0.3 and not has_serious_misunderstanding):
        return {
            "assessment_result": "partially_understood",
            "confidence_level": "medium" if has_minor_misunderstanding else "medium_high",
            "assessment_details": "学习者理解了主要概念，但有部分细节不清楚"
        }
    else:
        return {
            "assessment_result": "not_understood",
            "confidence_level": "low" if has_serious_misunderstanding else "medium",
            "assessment_details": "学习者对概念的理解不足，需要重新讲解"
        }


@tool
def decide_next_action(
    assessment_result: str,
    retry_count: int,
    max_retries: int = 3
) -> str:
    """决定下一步行动
    
    Args:
        assessment_result: 评估结果
        retry_count: 当前重试次数
        max_retries: 最大重试次数
    
    Returns:
        "continue" | "adaptive_followup" | "retry" | "record_gap"
    """
    if assessment_result == "fully_understood":
        return "continue"
    
    elif assessment_result == "partially_understood":
        return "adaptive_followup"
    
    elif assessment_result == "not_understood":
        if retry_count < max_retries:
            return "retry"
        else:
            return "record_gap"
    
    else:
        # 未知评估结果，默认继续
        return "continue"
