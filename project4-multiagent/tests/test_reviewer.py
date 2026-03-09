"""
Reviewer Agent 测试
"""
import pytest
from unittest.mock import Mock, patch
from src.agents.reviewer import create_reviewer, REVIEWER_SYSTEM_MESSAGE


def test_reviewer_system_message():
    """测试 Reviewer 有正确的系统消息"""
    assert 'code review' in REVIEWER_SYSTEM_MESSAGE.lower()
    assert 'quality' in REVIEWER_SYSTEM_MESSAGE.lower()


def test_reviewer_system_message_contains_checklist():
    """测试系统消息包含审查清单"""
    assert 'correctness' in REVIEWER_SYSTEM_MESSAGE.lower()
    assert 'style' in REVIEWER_SYSTEM_MESSAGE.lower()
    assert 'security' in REVIEWER_SYSTEM_MESSAGE.lower()


def test_reviewer_constructive_feedback():
    """测试系统消息强调建设性反馈"""
    assert 'specific' in REVIEWER_SYSTEM_MESSAGE.lower() or 'improvement' in REVIEWER_SYSTEM_MESSAGE.lower()


@patch('src.agents.reviewer.autogen.AssistantAgent')
def test_create_reviewer_returns_agent(mock_assistant_agent, monkeypatch):
    """测试 create_reviewer 返回一个 Agent"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "reviewer"
    mock_assistant_agent.return_value = mock_instance

    from src.core.config import Config
    config = Config()

    agent = create_reviewer(config)

    assert agent is not None
    assert agent.name == "reviewer"


@patch('src.agents.reviewer.autogen.AssistantAgent')
def test_reviewer_uses_config_llm(mock_assistant_agent, monkeypatch):
    """测试 Reviewer 使用配置中的 LLM 设置"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "reviewer"
    mock_assistant_agent.return_value = mock_instance

    from src.core.config import Config
    config = Config()

    create_reviewer(config)

    # 验证 LLM 配置被传递
    mock_assistant_agent.assert_called_once()
    call_kwargs = mock_assistant_agent.call_args[1]
    assert 'llm_config' in call_kwargs
