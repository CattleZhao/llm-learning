"""
UserProxy Agent 测试
"""
import pytest
from unittest.mock import Mock, patch
from src.agents.user_proxy import create_user_proxy, USER_PROXY_SYSTEM_MESSAGE


def test_user_proxy_system_message():
    """测试 UserProxy 有正确的系统消息"""
    assert 'coordinate' in USER_PROXY_SYSTEM_MESSAGE.lower()
    assert 'development team' in USER_PROXY_SYSTEM_MESSAGE.lower()


@patch('src.agents.user_proxy.autogen.UserProxyAgent')
def test_create_user_proxy_returns_agent(mock_user_proxy_agent, monkeypatch):
    """测试 create_user_proxy 返回一个 Agent"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "user_proxy"
    mock_user_proxy_agent.return_value = mock_instance

    agent = create_user_proxy.__wrapped__(Mock(api_key='test', work_dir='./outputs'))

    assert agent is not None
    assert agent.name == "user_proxy"


@patch('src.agents.user_proxy.autogen.UserProxyAgent')
def test_user_proxy_has_correct_config(mock_user_proxy_agent, monkeypatch):
    """测试 UserProxy 有正确的配置"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "user_proxy"
    mock_user_proxy_agent.return_value = mock_instance

    from src.core.config import Config
    config = Config()

    create_user_proxy(config)

    # 验证调用参数
    mock_user_proxy_agent.assert_called_once()
    call_kwargs = mock_user_proxy_agent.call_args[1]
    assert call_kwargs['name'] == 'user_proxy'
    assert call_kwargs['human_input_mode'] == 'NEVER'
    assert 'code_execution_config' in call_kwargs


def test_user_proxy_system_message_content():
    """测试系统消息包含关键职责"""
    assert 'understand user requirements' in USER_PROXY_SYSTEM_MESSAGE.lower()
    assert 'coordinate' in USER_PROXY_SYSTEM_MESSAGE.lower()
    assert 'execute code' in USER_PROXY_SYSTEM_MESSAGE.lower()
