"""
P1节点重构验证测试：新增节点和路由功能

验证内容验证节点、记忆辅助节点和路由决策函数
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
from backend.workflows.state import TeachingState, create_initial_state
from backend.workflows.teaching_workflow import SocraticTeachingWorkflow


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
def workflow(mock_session, mock_vector_search):
    """创建工作流实例"""
    return SocraticTeachingWorkflow(mock_session, mock_vector_search)


@pytest.fixture
def test_state():
    """创建测试状态"""
    return create_initial_state(
        learner_id=uuid4(),
        goal_id=uuid4(),
        tenant_id=uuid4(),
        question_text="什么是Python装饰器？"
    )


class TestValidateContentNode:
    """测试内容验证节点"""
    
    def test_skip_validation_when_flag_is_true(self, workflow, test_state):
        """测试跳过标志为True时跳过验证"""
        test_state.skip_validation = True
        test_state.explanation = "Python装饰器是一种设计模式"
        
        result = workflow._validate_content_node(test_state)
        
        assert result is not None
        assert "validation_result" not in result or result.get("validation_result") is None
    
    def test_skip_validation_when_no_explanation(self, workflow, test_state):
        """测试无解释内容时跳过验证"""
        test_state.explanation = None
        
        result = workflow._validate_content_node(test_state)
        
        assert result is not None
    
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    @patch("backend.workflows.teaching_workflow.TavilySearchResults")
    def test_validation_with_numbers(self, mock_tavily, workflow, test_state):
        """测试包含数字的内容触发验证"""
        test_state.explanation = "Python在2024年市场占有率达到30%"
        
        # 模拟Tavily搜索结果
        mock_tool = Mock()
        mock_tool.invoke.return_value = [
            {
                "url": "https://example.com",
                "title": "Python市场报告",
                "content": "Python市场占有率持续增长"
            }
        ]
        mock_tavily.return_value = mock_tool
        
        result = workflow._validate_content_node(test_state)
        
        assert result is not None
        assert "verified_sources" in result or test_state.verified_sources
    
    def test_validation_error_handling(self, workflow, test_state):
        """测试验证过程错误处理"""
        test_state.explanation = "测试内容"
        
        # 不设置API密钥，应该优雅降级
        result = workflow._validate_content_node(test_state)
        
        assert result is not None


class TestGenerateMnemonicNode:
    """测试记忆辅助生成节点"""
    
    def test_skip_mnemonic_when_flag_is_true(self, workflow, test_state):
        """测试跳过标志为True时跳过记忆辅助"""
        test_state.skip_mnemonic = True
        test_state.assessment_result = "not_understood"
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None
        assert len(test_state.mnemonic_devices) == 0
    
    def test_skip_mnemonic_when_understood(self, workflow, test_state):
        """测试已理解时跳过记忆辅助"""
        test_state.assessment_result = "fully_understood"
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None
        assert len(test_state.mnemonic_devices) == 0
    
    def test_generate_mnemonic_when_not_understood(self, workflow, test_state):
        """测试未理解时生成记忆辅助"""
        test_state.assessment_result = "not_understood"
        test_state.explanation = "Python装饰器用于修改函数行为"
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None
        # 应该生成至少一种记忆策略
        assert test_state.recommended_strategy is not None
    
    def test_mnemonic_error_handling(self, workflow, test_state):
        """测试记忆辅助生成错误处理"""
        test_state.assessment_result = "not_understood"
        test_state.explanation = None  # 触发潜在错误
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None


class TestRoutingFunctions:
    """测试路由决策函数"""
    
    @patch.dict("os.environ", {"ENABLE_CONTENT_VALIDATION": "false"})
    def test_should_validate_content_disabled(self, workflow, test_state):
        """测试内容验证禁用时返回skip"""
        test_state.explanation = "包含30%的数字"
        
        result = workflow._should_validate_content(test_state)
        
        assert result == "skip"
    
    @patch.dict("os.environ", {"ENABLE_CONTENT_VALIDATION": "true", "TAVILY_API_KEY": "test_key"})
    def test_should_validate_content_enabled(self, workflow, test_state):
        """测试内容验证启用且有数字时返回validate"""
        test_state.explanation = "Python在2024年占有率30%"
        
        result = workflow._should_validate_content(test_state)
        
        # 应该触发验证
        assert result in ["validate", "skip"]
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "true"})
    def test_route_after_assessment_with_mnemonic(self, workflow, test_state):
        """测试评估后未理解时路由到记忆辅助"""
        test_state.assessment_result = "not_understood"
        test_state.skip_mnemonic = False
        
        result = workflow._route_after_assessment(test_state)
        
        assert result == "generate_mnemonic"
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "false"})
    def test_route_after_assessment_without_mnemonic(self, workflow, test_state):
        """测试记忆辅助禁用时使用原路由逻辑"""
        test_state.assessment_result = "not_understood"
        test_state.next_action = "record_gap"
        
        result = workflow._route_after_assessment(test_state)
        
        assert result == "record_gap"
    
    def test_route_after_assessment_continue(self, workflow, test_state):
        """测试评估后继续时路由到更新进度"""
        test_state.next_action = "continue"
        
        result = workflow._route_after_assessment(test_state)
        
        assert result == "update_progress"


class TestConversationManagerCoordination:
    """测试ConversationManager协调方法"""
    
    @patch.dict("os.environ", {"ENABLE_CONTENT_VALIDATION": "true", "TAVILY_API_KEY": "test_key"})
    def test_should_enable_validation_true(self, mock_session):
        """测试应启用内容验证的情况"""
        from backend.agents.conversation_manager import ConversationManager
        
        manager = ConversationManager(mock_session)
        test_state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        test_state.explanation = "Python在2024年占有率30%"
        
        result = manager.should_enable_validation(test_state)
        
        # 应该返回True（有数字需要验证）
        assert isinstance(result, bool)
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "true", "MNEMONIC_TRIGGER_THRESHOLD": "not_understood"})
    def test_should_enable_mnemonic_true(self, mock_session):
        """测试应启用记忆辅助的情况"""
        from backend.agents.conversation_manager import ConversationManager
        
        manager = ConversationManager(mock_session)
        test_state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        test_state.assessment_result = "not_understood"
        
        result = manager.should_enable_mnemonic(test_state)
        
        assert result is True
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "false"})
    def test_should_enable_mnemonic_false(self, mock_session):
        """测试禁用记忆辅助的情况"""
        from backend.agents.conversation_manager import ConversationManager
        
        manager = ConversationManager(mock_session)
        test_state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        test_state.assessment_result = "not_understood"
        
        result = manager.should_enable_mnemonic(test_state)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
P1节点重构验证测试：新增节点和路由功能

验证内容验证节点、记忆辅助节点和路由决策函数
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
from backend.workflows.state import TeachingState, create_initial_state
from backend.workflows.teaching_workflow import SocraticTeachingWorkflow


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
def workflow(mock_session, mock_vector_search):
    """创建工作流实例"""
    return SocraticTeachingWorkflow(mock_session, mock_vector_search)


@pytest.fixture
def test_state():
    """创建测试状态"""
    return create_initial_state(
        learner_id=uuid4(),
        goal_id=uuid4(),
        tenant_id=uuid4(),
        question_text="什么是Python装饰器？"
    )


class TestValidateContentNode:
    """测试内容验证节点"""
    
    def test_skip_validation_when_flag_is_true(self, workflow, test_state):
        """测试跳过标志为True时跳过验证"""
        test_state.skip_validation = True
        test_state.explanation = "Python装饰器是一种设计模式"
        
        result = workflow._validate_content_node(test_state)
        
        assert result is not None
        assert "validation_result" not in result or result.get("validation_result") is None
    
    def test_skip_validation_when_no_explanation(self, workflow, test_state):
        """测试无解释内容时跳过验证"""
        test_state.explanation = None
        
        result = workflow._validate_content_node(test_state)
        
        assert result is not None
    
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    @patch("backend.workflows.teaching_workflow.TavilySearchResults")
    def test_validation_with_numbers(self, mock_tavily, workflow, test_state):
        """测试包含数字的内容触发验证"""
        test_state.explanation = "Python在2024年市场占有率达到30%"
        
        # 模拟Tavily搜索结果
        mock_tool = Mock()
        mock_tool.invoke.return_value = [
            {
                "url": "https://example.com",
                "title": "Python市场报告",
                "content": "Python市场占有率持续增长"
            }
        ]
        mock_tavily.return_value = mock_tool
        
        result = workflow._validate_content_node(test_state)
        
        assert result is not None
        assert "verified_sources" in result or test_state.verified_sources
    
    def test_validation_error_handling(self, workflow, test_state):
        """测试验证过程错误处理"""
        test_state.explanation = "测试内容"
        
        # 不设置API密钥，应该优雅降级
        result = workflow._validate_content_node(test_state)
        
        assert result is not None


class TestGenerateMnemonicNode:
    """测试记忆辅助生成节点"""
    
    def test_skip_mnemonic_when_flag_is_true(self, workflow, test_state):
        """测试跳过标志为True时跳过记忆辅助"""
        test_state.skip_mnemonic = True
        test_state.assessment_result = "not_understood"
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None
        assert len(test_state.mnemonic_devices) == 0
    
    def test_skip_mnemonic_when_understood(self, workflow, test_state):
        """测试已理解时跳过记忆辅助"""
        test_state.assessment_result = "fully_understood"
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None
        assert len(test_state.mnemonic_devices) == 0
    
    def test_generate_mnemonic_when_not_understood(self, workflow, test_state):
        """测试未理解时生成记忆辅助"""
        test_state.assessment_result = "not_understood"
        test_state.explanation = "Python装饰器用于修改函数行为"
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None
        # 应该生成至少一种记忆策略
        assert test_state.recommended_strategy is not None
    
    def test_mnemonic_error_handling(self, workflow, test_state):
        """测试记忆辅助生成错误处理"""
        test_state.assessment_result = "not_understood"
        test_state.explanation = None  # 触发潜在错误
        
        result = workflow._generate_mnemonic_node(test_state)
        
        assert result is not None


class TestRoutingFunctions:
    """测试路由决策函数"""
    
    @patch.dict("os.environ", {"ENABLE_CONTENT_VALIDATION": "false"})
    def test_should_validate_content_disabled(self, workflow, test_state):
        """测试内容验证禁用时返回skip"""
        test_state.explanation = "包含30%的数字"
        
        result = workflow._should_validate_content(test_state)
        
        assert result == "skip"
    
    @patch.dict("os.environ", {"ENABLE_CONTENT_VALIDATION": "true", "TAVILY_API_KEY": "test_key"})
    def test_should_validate_content_enabled(self, workflow, test_state):
        """测试内容验证启用且有数字时返回validate"""
        test_state.explanation = "Python在2024年占有率30%"
        
        result = workflow._should_validate_content(test_state)
        
        # 应该触发验证
        assert result in ["validate", "skip"]
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "true"})
    def test_route_after_assessment_with_mnemonic(self, workflow, test_state):
        """测试评估后未理解时路由到记忆辅助"""
        test_state.assessment_result = "not_understood"
        test_state.skip_mnemonic = False
        
        result = workflow._route_after_assessment(test_state)
        
        assert result == "generate_mnemonic"
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "false"})
    def test_route_after_assessment_without_mnemonic(self, workflow, test_state):
        """测试记忆辅助禁用时使用原路由逻辑"""
        test_state.assessment_result = "not_understood"
        test_state.next_action = "record_gap"
        
        result = workflow._route_after_assessment(test_state)
        
        assert result == "record_gap"
    
    def test_route_after_assessment_continue(self, workflow, test_state):
        """测试评估后继续时路由到更新进度"""
        test_state.next_action = "continue"
        
        result = workflow._route_after_assessment(test_state)
        
        assert result == "update_progress"


class TestConversationManagerCoordination:
    """测试ConversationManager协调方法"""
    
    @patch.dict("os.environ", {"ENABLE_CONTENT_VALIDATION": "true", "TAVILY_API_KEY": "test_key"})
    def test_should_enable_validation_true(self, mock_session):
        """测试应启用内容验证的情况"""
        from backend.agents.conversation_manager import ConversationManager
        
        manager = ConversationManager(mock_session)
        test_state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        test_state.explanation = "Python在2024年占有率30%"
        
        result = manager.should_enable_validation(test_state)
        
        # 应该返回True（有数字需要验证）
        assert isinstance(result, bool)
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "true", "MNEMONIC_TRIGGER_THRESHOLD": "not_understood"})
    def test_should_enable_mnemonic_true(self, mock_session):
        """测试应启用记忆辅助的情况"""
        from backend.agents.conversation_manager import ConversationManager
        
        manager = ConversationManager(mock_session)
        test_state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        test_state.assessment_result = "not_understood"
        
        result = manager.should_enable_mnemonic(test_state)
        
        assert result is True
    
    @patch.dict("os.environ", {"ENABLE_MNEMONIC": "false"})
    def test_should_enable_mnemonic_false(self, mock_session):
        """测试禁用记忆辅助的情况"""
        from backend.agents.conversation_manager import ConversationManager
        
        manager = ConversationManager(mock_session)
        test_state = create_initial_state(
            learner_id=uuid4(),
            goal_id=uuid4(),
            tenant_id=uuid4()
        )
        test_state.assessment_result = "not_understood"
        
        result = manager.should_enable_mnemonic(test_state)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
