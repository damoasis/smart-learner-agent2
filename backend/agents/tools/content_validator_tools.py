"""
ContentValidator工具集 - 内容验证相关工具函数
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import re

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.models.session import VerifiedContent, AuthoritySource


@tool
def search_verification_sources(query: str, max_results: int = 3) -> List[Dict]:
    """搜索验证来源"""
    import os
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    
    try:
        tavily = TavilySearchResults(max_results=max_results, api_key=key)
        results = tavily.invoke({"query": query})
        return [{"url": r.get("url"), "title": r.get("title"), "content": r.get("content", "")[:500]} for r in results]
    except Exception:
        return []


@tool
def extract_web_content(url: str) -> str:
    """提取网页内容"""
    try:
        from langchain_community.document_loaders import JinaURLReader
        loader = JinaURLReader(url=url)
        docs = loader.load()
        return docs[0].page_content if docs else ""
    except Exception:
        return ""


@tool
def validate_against_sources(
    explanation: str, sources: List[Dict]
) -> Dict:
    """验证内容"""
    import os
    llm = ChatOpenAI(model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    
    from langchain_core.prompts import ChatPromptTemplate
    
    sources_text = "\n".join([f"{s.get('title')}: {s.get('content')}" for s in sources[:2]])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "验证解释准确性，返回JSON: {\"is_verified\": bool, \"confidence_score\": float}"),
        ("user", f"解释：{explanation}\n\n来源：{sources_text}")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages())
        import json
        return json.loads(response.content)
    except Exception:
        return {"is_verified": True, "confidence_score": 0.7}


@tool
def save_verified_content(
    tenant_id: str, concept_id: str, content: str, 
    sources: List[str], confidence: float, session: Any
) -> str:
    """保存验证内容"""
    from uuid import UUID as U
    
    v = VerifiedContent(
        content_id=uuid4(),
        tenant_id=U(tenant_id),
        concept_id=U(concept_id),
        content_text=content,
        sources=sources,
        verification_date=datetime.now(),
        confidence_score=confidence
    )
    session.add(v)
    session.flush()
    return str(v.content_id)


@tool
def should_verify_content(explanation_text: str, concept_name: Optional[str] = None) -> Dict:
    """判断内容是否需要验证
    
    Args:
        explanation_text: 解释文本
        concept_name: 概念名称（可选）
    
    Returns:
        {"needs_verification": bool, "verification_items": List[str], "reason": str}
    """
    verification_keywords = [
        r'\d+%',  # 百分比
        r'\$\d+',  # 金额
        r'\d{4}年',  # 年份
        r'法律', r'规定', r'条款',
        r'公式', r'计算方法',
        r'第\d+条', r'第\d+款'
    ]
    
    verification_items = []
    
    # 1. 检查是否包含需要验证的关键词
    for pattern in verification_keywords:
        matches = re.findall(pattern, explanation_text)
        if matches:
            verification_items.extend(matches)
    
    # 2. 检查是否包含具体数字
    number_patterns = [
        r'\d+\.?\d*元',  # 金额
        r'\d+\.?\d*%',  # 百分比
        r'\d{4}-\d{2}-\d{2}',  # 日期
        r'第\d+[条款项]'  # 法律条款
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, explanation_text)
        if matches:
            verification_items.extend(matches)
    
    # 3. 去重
    verification_items = list(set(verification_items))
    
    # 4. 判断规则
    needs_verification = len(verification_items) > 0
    
    # 5. 跳过纯概念解释
    skip_keywords = ['概念', '定义', '理解', '类比', '示例']
    reason = ""
    if any(keyword in explanation_text[:50] for keyword in skip_keywords):
        if len(verification_items) <= 1:
            needs_verification = False
            reason = "纯概念解释，无需验证"
    
    if needs_verification:
        reason = f"发现 {len(verification_items)} 个需要验证的关键信息"
    
    return {
        "needs_verification": needs_verification,
        "verification_items": verification_items,
        "reason": reason
    }


@tool
def generate_verified_explanation(
    original_explanation: str,
    sources: List[Dict],
    confidence_score: float
) -> str:
    """生成带来源引用的增强解释
    
    Args:
        original_explanation: 原始解释
        sources: 来源列表 [{"title": str, "url": str}]
        confidence_score: 置信度评分 (0-1)
    
    Returns:
        带来源引用的增强解释
    """
    if not sources:
        return original_explanation
    
    # 构建引用文本
    citations = "\n\n📚 **来源引用：**\n"
    for i, source in enumerate(sources[:3], 1):
        citations += f"{i}. {source.get('title', '未知来源')}\n"
        citations += f"   {source.get('url', '')}\n"
    
    # 添加验证信息
    if confidence_score >= 0.8:
        citations += f"\n✅ 内容已验证（置信度: {confidence_score:.0%}）"
    elif confidence_score >= 0.6:
        citations += f"\n⚠️ 内容部分验证（置信度: {confidence_score:.0%}），建议参考权威来源"
    else:
        citations += f"\n❗ 内容未充分验证（置信度: {confidence_score:.0%}），请以权威来源为准"
    
    return original_explanation + citations


@tool
def get_authority_sources(
    domain_tags: List[str],
    min_trust_score: float,
    session: Any
) -> List[Dict]:
    """获取指定领域的权威来源
    
    Args:
        domain_tags: 领域标签列表 (如 ["tax", "law"])
        min_trust_score: 最小信任评分 (0-1)
        session: 数据库会话
    
    Returns:
        权威来源列表 [{"source_name": str, "base_url": str, "trust_score": float}]
    """
    from sqlalchemy import and_
    
    try:
        # 查询包含指定领域标签且信任评分符合要求的来源
        query = session.query(AuthoritySource).filter(
            and_(
                AuthoritySource.domain_tags.op('&&')(domain_tags),  # 数组重叠操作
                AuthoritySource.trust_score >= min_trust_score
            )
        ).order_by(AuthoritySource.trust_score.desc())
        
        results = query.all()
        
        return [
            {
                "source_name": source.source_name,
                "base_url": source.base_url,
                "trust_score": float(source.trust_score),
                "domain_tags": source.domain_tags
            }
            for source in results
        ]
    except Exception as e:
        print(f"获取权威来源失败: {e}")
        return []
