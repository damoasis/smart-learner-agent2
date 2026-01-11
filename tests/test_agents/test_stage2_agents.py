"""
阶段二新增Agent的单元测试

测试范围：
- ContentValidatorAgent
- MnemonicGeneratorAgent  
- ProgressTracker增强功能
- LectureTeachingAgent
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch


# ========================================
# ContentValidatorAgent 测试
# ========================================

class TestContentValidatorAgent:
    """ContentValidatorAgent单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def validator_agent(self, mock_session):
        """创建ContentValidator ReAct Agent实例"""
        from backend.agents.react.content_validator_agent import create_content_validator_agent
        return create_content_validator_agent(mock_session)
    
    @pytest.fixture
    def mock_llm(self):
        """模拟LLM用于工具测试"""
        return Mock()
    
    def test_should_verify_tool(self):
        """测试：should_verify_content工具函数"""
        from backend.agents.tools.content_validator_tools import should_verify_content
        
        text = "个人所得税免征额为5000元/月，税率为10%"
        result = should_verify_content.invoke({"explanation_text": text})
        
        assert isinstance(result, dict)
        assert "needs_verification" in result
        assert "verification_items" in result
        assert result["needs_verification"] is True
        assert len(result["verification_items"]) > 0
    
    def test_should_verify_with_law_keywords(self):
        """测试：包含法律关键词的内容需要验证"""
        from backend.agents.tools.content_validator_tools import should_verify_content
        
        text = "根据民法典第123条规定，合同双方应遵守诚实信用原则"
        result = should_verify_content.invoke({"explanation_text": text})
        
        assert result["needs_verification"] is True
        assert len(result["verification_items"]) > 0
    
    def test_should_skip_concept_explanation(self):
        """测试：纯概念解释可跳过验证"""
        from backend.agents.tools.content_validator_tools import should_verify_content
        
        text = "这个概念是指一种抽象的理论框架"
        result = should_verify_content.invoke({"explanation_text": text})
        
        # 纯概念解释且关键词少，应跳过
        assert result["needs_verification"] is False or len(result["verification_items"]) <= 1
    
    def test_generate_verified_explanation_tool(self):
        """测试：generate_verified_explanation工具函数"""
        from backend.agents.tools.content_validator_tools import generate_verified_explanation
        
        original = "个人所得税免征额为5000元/月"
        sources = [
            {"title": "国家税务总局", "url": "https://chinatax.gov.cn"},
            {"title": "个人所得税法", "url": "https://example.com"}
        ]
        
        enhanced = generate_verified_explanation.invoke({
            "original_explanation": original,
            "sources": sources,
            "confidence_score": 0.9
        })
        
        assert original in enhanced
        assert "来源引用" in enhanced
        assert "国家税务总局" in enhanced
        assert "置信度" in enhanced or "已验证" in enhanced


# ========================================
# MnemonicGeneratorAgent 测试
# ========================================

class TestMnemonicGeneratorAgent:
    """MnemonicGeneratorAgent单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def mock_llm(self):
        """模拟LLM"""
        return Mock()
    
    @pytest.fixture
    def generator(self, mock_session, mock_llm):
        """创建MnemonicGeneratorAgent实例"""
        from backend.agents.mnemonic_generator import MnemonicGeneratorAgent
        return MnemonicGeneratorAgent(mock_session, mock_llm)
    
    def test_select_strategy_for_list_concepts(self, generator):
        """测试：列表概念推荐缩略词策略"""
        formulas = ["Local", "Enclosing", "Global", "Built-in"]
        strategies = generator.select_mnemonic_strategy(
            "LEGB规则",
            "Python变量查找规则",
            formulas=formulas
        )
        
        assert "acronym" in strategies
    
    def test_select_strategy_for_abstract_concept(self, generator):
        """测试：抽象概念推荐类比策略"""
        strategies = generator.select_mnemonic_strategy(
            "量子纠缠原理",
            "量子纠缠是一种量子力学现象，描述粒子之间的关联",
            formulas=None
        )
        
        assert "analogy" in strategies
    
    def test_select_strategy_for_numbers(self, generator):
        """测试：包含多个数字推荐数字模式"""
        strategies = generator.select_mnemonic_strategy(
            "28-36规则",
            "住房支出不超过28%，总债务不超过36%，应急资金3-6个月",
            formulas=None
        )
        
        assert "number" in strategies
    
    def test_generate_acronym_mnemonic(self, generator):
        """测试：生成缩略词记忆"""
        # 模型从新位置导入，但也可以从旧位置导入（向后兼容）
        from backend.agents.mnemonic_generator import AcronymMnemonic
        
        concepts = ["Local", "Enclosing", "Global", "Built-in"]
        result = generator.generate_acronym_mnemonic(concepts)
        
        assert isinstance(result, AcronymMnemonic)
        assert result.acronym == "LEGB"
        assert result.full_terms == concepts
        assert len(result.memory_tip) > 0
    
    def test_generate_comparison_mnemonic(self, generator):
        """测试：生成对比表记忆"""
        from backend.agents.mnemonic_generator import ComparisonTableMnemonic
        
        concepts = ["AOTC", "LLC"]
        result = generator.generate_comparison_mnemonic(concepts, context="税收抵免")
        
        assert isinstance(result, ComparisonTableMnemonic)
        assert len(result.items) == 2
        assert "AOTC" in result.items
        assert "LLC" in result.items
    
    def test_generate_analogy_mnemonic(self, generator):
        """测试：生成类比记忆"""
        from backend.agents.mnemonic_generator import AnalogyMnemonic
        
        result = generator.generate_analogy_mnemonic(
            "支撑位和阻力位",
            "技术分析中的价格支撑和阻力概念"
        )
        
        assert isinstance(result, AnalogyMnemonic)
        assert result.abstract_concept == "支撑位和阻力位"
        assert len(result.concrete_analogy) > 0


# ========================================
# ProgressTracker 增强功能测试
# ========================================

class TestProgressTrackerEnhanced:
    """ProgressTracker增强功能单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = Mock()
        session.execute = Mock(return_value=Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=[])))))
        session.get = Mock(return_value=None)
        return session
    
    @pytest.fixture
    def tracker(self, mock_session):
        """创建ProgressTracker实例"""
        from backend.agents.react.progress_tracker_agent import ProgressTracker
        return ProgressTracker(mock_session)
    
    def test_analyze_learning_efficiency_structure(self, tracker):
        """测试：学习效率分析返回正确结构"""
        learner_id = uuid4()
        tenant_id = uuid4()
        
        result = tracker.analyze_learning_efficiency(learner_id, tenant_id, time_range_days=30)
        
        assert 'learner_id' in result
        assert 'average_mastery_time_days' in result
        assert 'first_time_correct_rate' in result
        assert 'total_learning_hours' in result
        assert 'learning_pace' in result
        assert 'weak_areas' in result
        assert 'strength_areas' in result
        assert 'improvement_suggestions' in result
        
        # 验证数值范围
        assert result['first_time_correct_rate'] >= 0
        assert result['first_time_correct_rate'] <= 1
        assert result['learning_pace'] in ['slow', 'moderate', 'fast']
    
    def test_get_review_recommendations_structure(self, tracker):
        """测试：复习提醒返回正确结构"""
        learner_id = uuid4()
        tenant_id = uuid4()
        
        result = tracker.get_review_recommendations(learner_id, tenant_id, max_items=5)
        
        assert isinstance(result, list)
        assert len(result) <= 5
        
        # 如果有结果，验证结构
        for item in result:
            assert 'topic_id' in item
            assert 'topic_name' in item
            assert 'days_since_review' in item
            assert 'urgency_score' in item
            assert 'recommended_action' in item
            assert item['urgency_score'] >= 0
            assert item['urgency_score'] <= 1
            assert item['recommended_action'] in ['quick_review', 'deep_review']
    
    def test_recommend_next_topics_structure(self, tracker):
        """测试：主题推荐返回正确结构"""
        learner_id = uuid4()
        tenant_id = uuid4()
        
        result = tracker.recommend_next_topics(
            learner_id, 
            tenant_id, 
            goal_id=uuid4(),
            max_recommendations=3
        )
        
        assert isinstance(result, list)
        assert len(result) <= 3
        
        # 如果有结果，验证结构
        for item in result:
            assert 'topic_id' in item
            assert 'topic_name' in item
            assert 'recommendation_score' in item
            assert 'recommendation_reason' in item
            assert 'prerequisite_status' in item
            assert 'estimated_difficulty' in item
            assert item['recommendation_score'] >= 0
            assert item['recommendation_score'] <= 1


# ========================================
# LectureTeachingAgent 测试
# ========================================

class TestLectureTeachingAgent:
    """LectureTeachingAgent单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def mock_llm(self):
        """模拟LLM"""
        return Mock()
    
    @pytest.fixture
    def lecture_agent(self, mock_session, mock_llm):
        """创建LectureTeachingAgent实例"""
        from backend.agents.teaching.lecture_teaching_agent import LectureTeachingAgent
        return LectureTeachingAgent(mock_session, mock_llm)
    
    def test_get_mode_info(self, lecture_agent):
        """测试：获取教学模式信息"""
        mode_info = lecture_agent.get_mode_info()
        
        assert mode_info.mode_id == "lecture"
        assert mode_info.mode_name == "讲授式教学"
        assert mode_info.mode_type == "systematic"
        assert len(mode_info.description) > 0
        assert len(mode_info.applicable_scenarios) > 0
    
    def test_is_suitable_for_new_topic(self, lecture_agent):
        """测试：新知识适配度评分"""
        from backend.agents.base.teaching_agent_interface import TeachingContext, LearnerProfile
        
        context = TeachingContext(
            topic=Mock(topic_id=uuid4(), has_complex_structure=True),
            learner_profile=LearnerProfile(
                learner_id=uuid4(),
                baseline_level="intermediate",
                mastered_topics=[],  # 空列表表示新主题
                struggle_areas=[]
            ),
            learning_history=Mock(),
            session_info=Mock(),
            tenant_config=Mock()
        )
        
        score = lecture_agent.is_suitable_for(context)
        
        assert score >= 0.0
        assert score <= 1.0
        # 新知识应该有较高适配度
        assert score >= 0.4
    
    def test_teach_method_structure(self, lecture_agent):
        """测试：teach方法返回结构"""
        from backend.workflows.state import TeachingState
        
        state = TeachingState(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4(),
            session_id=uuid4(),
            current_topic_id=uuid4(),
            question_text="什么是个人所得税？"
        )
        
        # Mock LLM响应
        mock_response = Mock()
        mock_response.content = "个人所得税是对个人所得征收的一种税..."
        lecture_agent.llm.invoke = Mock(return_value=mock_response)
        
        result_state = lecture_agent.teach(state)
        
        assert result_state.explanation is not None
        assert len(result_state.explanation) > 0


# ========================================
# 集成测试辅助函数
# ========================================

def test_all_agents_have_proper_interface():
    """测试：所有Agent都实现了正确的接口"""
    from backend.agents.teaching.socratic_teacher_adapter import SocraticTeacherAdapter
    from backend.agents.teaching.lecture_teaching_agent import LectureTeachingAgent
    from backend.agents.base.teaching_agent_interface import TeachingAgentInterface
    
    # 检查是否都实现了接口
    mock_session = Mock()
    mock_llm = Mock()
    
    socratic = SocraticTeacherAdapter(mock_session, mock_llm)
    lecture = LectureTeachingAgent(mock_session, mock_llm)
    
    assert isinstance(socratic, TeachingAgentInterface)
    assert isinstance(lecture, TeachingAgentInterface)
    
    # 检查必需方法
    assert hasattr(socratic, 'teach')
    assert hasattr(socratic, 'get_mode_info')
    assert hasattr(socratic, 'is_suitable_for')
    
    assert hasattr(lecture, 'teach')
    assert hasattr(lecture, 'get_mode_info')
    assert hasattr(lecture, 'is_suitable_for')


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
