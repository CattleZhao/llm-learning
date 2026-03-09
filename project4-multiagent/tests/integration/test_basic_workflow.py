"""
集成测试 - 基础工作流

这些测试验证多个组件之间的集成。
需要实际的 API key 才能运行。
"""
import pytest
import os
from unittest.mock import Mock, patch
from src.core import get_config, create_orchestrator


@pytest.mark.integration
def test_orchestrator_initialization_with_real_config(temp_api_key):
    """测试使用真实配置初始化编排器"""
    config = get_config()

    # 创建所有 agent 的 mock
    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        orchestrator = create_orchestrator(config)

        assert orchestrator is not None
        assert orchestrator.user_proxy is not None
        assert orchestrator.coder is not None
        assert orchestrator.reviewer is not None
        assert orchestrator.tester is not None


@pytest.mark.integration
def test_orchestrator_agent_list(mock_config):
    """测试编排器的 agent 列表"""
    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        from src.core.orchestrator import CodeDevelopmentOrchestrator

        orchestrator = CodeDevelopmentOrchestrator(mock_config)

        agents = orchestrator.agents
        assert len(agents) == 4
        assert all(agent is not None for agent in agents)


@pytest.mark.integration
def test_get_agent_by_name_works(mock_config):
    """测试通过名称获取 agent"""
    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        from src.core.orchestrator import CodeDevelopmentOrchestrator

        orchestrator = CodeDevelopmentOrchestrator(mock_config)

        # 测试获取存在的 agent
        coder = orchestrator.get_agent_by_name('coder')
        assert coder is not None
        assert coder.name == 'coder'

        # 测试获取不存在的 agent
        none_agent = orchestrator.get_agent_by_name('nonexistent')
        assert none_agent is None


@pytest.mark.integration
def test_config_requires_api_key():
    """测试配置需要 API key"""
    # 临时移除 API key
    original_key = os.environ.get('OPENAI_API_KEY')
    if original_key:
        del os.environ['OPENAI_API_KEY']

    try:
        from src.core.config import Config
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Config()
    finally:
        # 恢复 API key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
