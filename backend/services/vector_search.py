"""
向量检索服务模块

该模块提供基于pgvector的语义相似度搜索功能，用于根据学习者的问题检索相关概念。
"""

from typing import List, Optional, Tuple
from uuid import UUID
import os

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings

from backend.models.topic import Concept


class VectorSearchService:
    """
    向量检索服务类
    
    使用OpenAI Embeddings生成问题的向量表示，然后在PostgreSQL中
    使用pgvector扩展执行余弦相似度搜索，返回最相关的概念。
    """
    
    def __init__(self, session: Session, embedding_model: Optional[OpenAIEmbeddings] = None):
        """
        初始化向量检索服务
        
        Args:
            session: SQLAlchemy数据库会话
            embedding_model: OpenAI嵌入模型实例，如果为None则使用默认配置
        """
        self.session = session
        
        if embedding_model is None:
            # 使用默认配置创建OpenAI Embeddings实例
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            if not api_key:
                raise ValueError("OPENAI_API_KEY环境变量未设置")
            
            self.embedding_model = OpenAIEmbeddings(
                openai_api_key=api_key,
                openai_api_base=base_url,
                model="text-embedding-ada-002"  # 1536维向量
            )
        else:
            self.embedding_model = embedding_model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本的向量embedding
        
        Args:
            text: 待转换的文本
            
        Returns:
            1536维的向量列表
        """
        embedding = self.embedding_model.embed_query(text)
        return embedding
    
    def search_similar_concepts(
        self,
        query_text: str,
        tenant_id: UUID,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        topic_id: Optional[UUID] = None
    ) -> List[Tuple[Concept, float]]:
        """
        根据问题文本搜索相似的概念
        
        Args:
            query_text: 学习者提出的问题
            tenant_id: 租户ID（用于多租户隔离）
            top_k: 返回最相关的前k个概念，默认5
            similarity_threshold: 相似度阈值（0-1），默认0.7，低于此值的结果将被过滤
            topic_id: 可选的主题ID，如果提供则只在该主题下搜索
            
        Returns:
            包含(Concept对象, 相似度分数)的元组列表，按相似度降序排列
        """
        # 生成问题的向量
        query_embedding = self.generate_embedding(query_text)
        
        # 构建SQL查询
        # 使用pgvector的<=>操作符计算余弦距离（距离越小越相似）
        # 余弦相似度 = 1 - 余弦距离
        query = select(
            Concept,
            (1 - Concept.embedding.cosine_distance(query_embedding)).label("similarity")
        ).where(
            Concept.tenant_id == tenant_id,
            Concept.embedding.isnot(None)  # 只搜索有embedding的概念
        )
        
        # 如果指定了主题，则过滤
        if topic_id:
            query = query.where(Concept.topic_id == topic_id)
        
        # 按相似度降序排列，限制返回数量
        query = query.order_by(
            (1 - Concept.embedding.cosine_distance(query_embedding)).desc()
        ).limit(top_k)
        
        # 执行查询
        results = self.session.execute(query).all()
        
        # 过滤低于阈值的结果
        filtered_results = [
            (concept, similarity)
            for concept, similarity in results
            if similarity >= similarity_threshold
        ]
        
        return filtered_results
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成多个文本的向量embedding
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表，每个向量对应一个文本
        """
        embeddings = self.embedding_model.embed_documents(texts)
        return embeddings
    
    def update_concept_embedding(self, concept_id: UUID, text: str) -> None:
        """
        更新概念的向量embedding
        
        Args:
            concept_id: 概念ID
            text: 用于生成embedding的文本（通常是概念名称+解释）
        """
        # 查询概念
        concept = self.session.get(Concept, concept_id)
        if not concept:
            raise ValueError(f"概念ID {concept_id} 不存在")
        
        # 生成embedding
        embedding = self.generate_embedding(text)
        
        # 更新概念
        concept.embedding = embedding
        self.session.flush()
    
    def batch_update_concept_embeddings(
        self,
        concepts: List[Concept],
        generate_text_func: Optional[callable] = None
    ) -> int:
        """
        批量更新多个概念的向量embedding
        
        Args:
            concepts: 概念对象列表
            generate_text_func: 可选的函数，用于从概念生成文本。
                               如果为None，则使用"概念名称 + 解释"作为默认文本
            
        Returns:
            成功更新的概念数量
        """
        if not concepts:
            return 0
        
        # 生成文本列表
        if generate_text_func:
            texts = [generate_text_func(c) for c in concepts]
        else:
            # 默认使用概念名称和解释
            texts = [
                f"{c.concept_name}. {c.explanation or ''}"
                for c in concepts
            ]
        
        # 批量生成embeddings
        embeddings = self.batch_generate_embeddings(texts)
        
        # 更新每个概念
        updated_count = 0
        for concept, embedding in zip(concepts, embeddings):
            concept.embedding = embedding
            updated_count += 1
        
        self.session.flush()
        return updated_count
    
    def get_concept_statistics(self, tenant_id: UUID) -> dict:
        """
        获取向量检索相关的统计信息
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            包含统计信息的字典
        """
        # 总概念数
        total_concepts = self.session.query(func.count(Concept.concept_id)).filter(
            Concept.tenant_id == tenant_id
        ).scalar()
        
        # 有embedding的概念数
        concepts_with_embedding = self.session.query(func.count(Concept.concept_id)).filter(
            Concept.tenant_id == tenant_id,
            Concept.embedding.isnot(None)
        ).scalar()
        
        # 没有embedding的概念数
        concepts_without_embedding = total_concepts - concepts_with_embedding
        
        # 计算覆盖率
        coverage_rate = (concepts_with_embedding / total_concepts * 100) if total_concepts > 0 else 0
        
        return {
            "total_concepts": total_concepts,
            "concepts_with_embedding": concepts_with_embedding,
            "concepts_without_embedding": concepts_without_embedding,
            "embedding_coverage_rate": round(coverage_rate, 2)
        }


def create_vector_search_service(session: Session) -> VectorSearchService:
    """
    工厂函数：创建向量检索服务实例
    
    Args:
        session: SQLAlchemy数据库会话
        
    Returns:
        VectorSearchService实例
    """
    return VectorSearchService(session)
