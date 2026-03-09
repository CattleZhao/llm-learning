"""
Tester Agent 测试
"""
import pytest
from unittest.mock import Mock, patch
from src.agents.tester import create_tester, TESTER_SYSTEM_MESSAGE


def test_tester_system_message():
    """测试 Tester 有正确的系统消息"""
    assert 'test' in TESTER_SYSTEM_MESSAGE.lower()
    assert 'pytest' in TESTER_SYSTEM_MESSAGE.lower()


def test_tester_system_message_emphasizes_coverage():
    """测试系统消息强调测试覆盖率"""
    assert 'edge' in TESTER_SYSTEM_MESSAGE.lower() or 'boundary' in TESTER_SYSTEM_MESSAGE.lower()
    assert 'normal' in TESTER_SYSTEM_MESSAGE.lower()


def test_tester_system_message_has_structure():
    """测试系统消息包含测试结构指导"""
    assert 'arrange' in TESTER_SYSTEM_MESSAGE.lower()
    assert 'act' in TESTER_SYSTEM_MESSAGE.lower()
    assert 'assert' in TESTER_SYSTEM_MESSAGE.lower()


@patch('src.agents.tester.autogen.AssistantAgent')
def test_create_tester_returns_agent(mock_assistant_agent, monkeypatch):
    """测试 create_tester 返回一个 Agent"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    mock_instance = Mock()
    mock_instance.name = "tester"
    mock_assistant_agent.return_value = mock_instance

    from src.core.config import Config
    config = Config()

    agent = create_tester(config)

    assert agent is not None
    assert agent.name == "tester"
