"""
主Agent工作流测试

测试主工作流的节点和路由功能
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from backend.workflows.state import TeachingState, create_initial_state
from backend.workflows.teaching_workflow import (
    SocraticTeachingWorkflow,
    create_teaching_workflow
)


@pytest.fixture
def mock_session():
    """创建模拟数据库会话"""
    session = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_vector_search():
    """创建模拟向量检索服务"""
    return Mock()


@pytest.fixture
def mock_llm():
    """创建模拟LLM"""
    llm = Mock()
    return llm


@pytest.fixture
def workflow(mock_session, mock_vector_search, mock_llm):
    """创建工作流实例"""
    return SocraticTeachingWorkflow(
        session=mock_session,
        vector_search=mock_vector_search,
        llm=mock_llm
    )


class TestWorkflowInitialization:
    """测试工作流初始化"""
    
    def test_workflow_creation(self, mock_session, mock_vector_search):
        """测试工作流可以成功创建"""
        workflow = create_teaching_workflow(mock_session, mock_vector_search)
        
        assert workflow is not None
        assert isinstance(workflow, SocraticTeachingWorkflow)
        assert workflow.session == mock_session
        assert workflow.vector_search == mock_vector_search
    
    def test_workflow_has_components(self, workflow):
        """测试工作流包含必要组件"""
        assert workflow.session is not None
        assert workflow.vector_search is not None
        assert workflow.llm is not None
    
    def test_workflow_graph_compiled(self, workflow):
        """测试工作流图已编译"""
        assert workflow.workflow is not None


class TestWorkflowNodes:
    """测试工作流各节点"""
    
    def test_initialize_node(self, workflow):
        """测试初始化节点"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4(),
            question_text="测试问题"
        )
        
        result = workflow._initialize_node(state)
        
        assert result is not None
        assert result["workflow_stage"] == "initialized"
        assert "timestamp" in result
    
    def test_wait_for_response_node(self, workflow):
        """测试等待回答节点"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        
        result = workflow._wait_for_response_node(state)
        
        assert result is not None
        assert result["workflow_stage"] == "waiting_for_response"
    
    def test_finalize_node(self, workflow):
        """测试终止节点"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        
        result = workflow._finalize_node(state)
        
        assert result is not None
        assert result["workflow_stage"] == "completed"
        assert "timestamp" in result


class TestWorkflowRouting:
    """测试工作流路由决策"""
    
    def test_should_validate_content_skip(self, workflow):
        """测试跳过内容验证"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.skip_validation = True
        state.explanation = "包含30%的数字"
        
        result = workflow._should_validate_content(state)
        
        assert result == "skip"
    
    def test_should_validate_content_with_numbers(self, workflow):
        """测试包含数字时需要验证"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.explanation = "Python在2024年占有率30%"
        
        result = workflow._should_validate_content(state)
        
        assert result == "validate"
    
    def test_should_generate_mnemonic_skip(self, workflow):
        """测试跳过记忆辅助"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.skip_mnemonic = True
        
        result = workflow._should_generate_mnemonic(state)
        
        assert result == "skip"
    
    def test_should_generate_mnemonic_long_explanation(self, workflow):
        """测试长解释需要记忆辅助"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.explanation = "这是一个很长的解释" * 50  # 超过300字
        
        result = workflow._should_generate_mnemonic(state)
        
        assert result == "generate"
    
    def test_route_after_assessment_continue(self, workflow):
        """测试完全理解时继续"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.assessment_result = "fully_understood"
        
        result = workflow._route_after_assessment(state)
        
        assert result == "continue"
    
    def test_route_after_assessment_followup(self, workflow):
        """测试部分理解时跟进"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.assessment_result = "partially_understood"
        
        result = workflow._route_after_assessment(state)
        
        assert result == "adaptive_followup"
    
    def test_route_after_assessment_retry(self, workflow):
        """测试未理解且未达最大重试时重试"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.assessment_result = "not_understood"
        state.retry_count = 1
        state.max_retries = 3
        
        result = workflow._route_after_assessment(state)
        
        assert result == "retry"
    
    def test_route_after_assessment_record_gap(self, workflow):
        """测试未理解且达最大重试时记录缺口"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        state.assessment_result = "not_understood"
        state.retry_count = 3
        state.max_retries = 3
        
        result = workflow._route_after_assessment(state)
        
        assert result == "record_gap"


class TestWorkflowIntegration:
    """测试工作流集成"""
    
    @patch("backend.workflows.teaching_workflow.evaluate_knowledge_baseline")
    @patch("backend.workflows.teaching_workflow.assess_understanding_level")
    @patch("backend.workflows.teaching_workflow.generate_progress_summary")
    def test_workflow_initialization_nodes(
        self,
        mock_progress,
        mock_assessor,
        mock_socratic,
        workflow
    ):
        """测试工作流初始化节点序列"""
        # 模拟工具函数返回
        mock_socratic.return_value = {
            "level": "intermediate",
            "assessment": "测试评估"
        }
        
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4(),
            question_text="什么是Python装饰器?"
        )
        
        # 测试初始化节点
        init_result = workflow._initialize_node(state)
        assert init_result["workflow_stage"] == "initialized"
        
        # 测试基线评估节点
        baseline_result = workflow._evaluate_baseline_node(state)
        assert baseline_result["workflow_stage"] == "baseline_evaluated"
        assert baseline_result["baseline_level"] == "intermediate"


class TestCheckNeedsValidation:
    """测试验证需求检查"""
    
    def test_check_needs_validation_with_formulas(self, workflow):
        """测试包含公式时需要验证"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        
        concepts = [
            {
                "concept_name": "测试概念",
                "formulas": ["E=mc²"]
            }
        ]
        
        result = workflow._check_needs_validation(state, concepts)
        
        assert result is True
    
    def test_check_needs_validation_with_rules(self, workflow):
        """测试包含规则时需要验证"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        
        concepts = [
            {
                "concept_name": "测试概念",
                "rules": ["规则1", "规则2"]
            }
        ]
        
        result = workflow._check_needs_validation(state, concepts)
        
        assert result is True
    
    def test_check_needs_validation_without_special_content(self, workflow):
        """测试不包含特殊内容时无需验证"""
        state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        
        concepts = [
            {
                "concept_name": "测试概念",
                "explanation": "普通解释"
            }
        ]
        
        result = workflow._check_needs_validation(state, concepts)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
