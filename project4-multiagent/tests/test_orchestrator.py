"""
Orchestrator 测试
"""
import pytest
from unittest.mock import Mock, patch
from src.core.orchestrator import (
    CodeDevelopmentOrchestrator,
    create_orchestrator,
)


def test_orchestrator_has_all_agents():
    """测试编排器包含所有 4 个 Agent"""
    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        # 创建 mock agent 实例
        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        from src.core.config import Config

        config = Mock()
        config.api_key = 'test_key'
        config.get_llm_config.return_value = {}
        config.get_code_execution_config.return_value = {}
        config.max_consecutive_auto_reply = 10
        config.work_dir = './outputs'

        orchestrator = create_orchestrator(config)

        assert orchestrator.user_proxy is not None
        assert orchestrator.coder is not None
        assert orchestrator.reviewer is not None
        assert orchestrator.tester is not None


def test_orchestrator_agents_property():
    """测试 agents 属性返回所有 Agent"""
    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        from src.core.config import Config

        config = Mock()
        config.api_key = 'test_key'
        config.get_llm_config.return_value = {}
        config.get_code_execution_config.return_value = {}
        config.max_consecutive_auto_reply = 10
        config.work_dir = './outputs'

        orchestrator = create_orchestrator(config)

        agents = orchestrator.agents
        assert len(agents) == 4


def test_get_agent_by_name():
    """测试通过名称获取 Agent"""
    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        from src.core.config import Config

        config = Mock()
        config.api_key = 'test_key'
        config.get_llm_config.return_value = {}
        config.get_code_execution_config.return_value = {}
        config.max_consecutive_auto_reply = 10
        config.work_dir = './outputs'

        orchestrator = create_orchestrator(config)

        coder = orchestrator.get_agent_by_name('coder')
        assert coder is not None
        assert coder.name == 'coder'

        none_agent = orchestrator.get_agent_by_name('nonexistent')
        assert none_agent is None
