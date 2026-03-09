"""
Coder Agent 测试
"""
import pytest
from unittest.mock import Mock, patch
from src.agents.coder import create_coder, CODER_SYSTEM_MESSAGE


def test_coder_system_message():
    """测试 Coder 有正确的系统消息"""
    assert 'python developer' in CODER_SYSTEM_MESSAGE.lower()
    assert 'type hints' in CODER_SYSTEM_MESSAGE.lower()
    assert 'pep 8' in CODER_SYSTEM_MESSAGE.lower()


def test_coder_system_message_contains_best_practices():
    """测试系统消息包含最佳实践要求"""
    assert 'docstring' in CODER_SYSTEM_MESSAGE.lower()
    assert 'error handling' in CODER_SYSTEM_MESSAGE.lower()


@patch('src.agents.coder.autogen.AssistantAgent')
def test_create_coder_returns_agent(mock_assistant_agent, monkeypatch):
    """测试 create_coder 返回一个 Agent"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "coder"
    mock_assistant_agent.return_value = mock_instance

    from src.core.config import Config
    config = Config()

    agent = create_coder(config)

    assert agent is not None
    assert agent.name == "coder"


@patch('src.agents.coder.autogen.AssistantAgent')
def test_coder_uses_config_llm(mock_assistant_agent, monkeypatch):
    """测试 Coder 使用配置中的 LLM 设置"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "coder"
    mock_instance.llm_config = {'model': 'gpt-4'}
    mock_assistant_agent.return_value = mock_instance

    from src.core.config import Config
    config = Config()
    config.model = 'gpt-4'
    config.temperature = 0.5

    create_coder(config)

    # 验证 LLM 配置被传递
    mock_assistant_agent.assert_called_once()
    call_kwargs = mock_assistant_agent.call_args[1]
    assert 'llm_config' in call_kwargs
    assert call_kwargs['llm_config']['model'] == 'gpt-4'
