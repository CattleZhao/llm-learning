import pytest
from unittest.mock import Mock, patch
from src.core.llm_setup import create_llm, create_crewai_llm

def test_create_llm_returns_chat_anthropic(monkeypatch):
    """测试 create_llm 返回 ChatAnthropic 实例"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.core.llm_setup.ChatAnthropic') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance

        llm = create_llm(model="claude-3-5-sonnet-20241022", temperature=0.5)

        mock_chat.assert_called_once()
        assert llm == mock_instance

def test_create_llm_with_custom_params(monkeypatch):
    """测试使用自定义参数创建 LLM"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.core.llm_setup.ChatAnthropic') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance

        llm = create_llm(
            model="custom-model",
            temperature=0.9,
            max_tokens=4000
        )

        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs['model'] == "custom-model"
        assert call_kwargs['temperature'] == 0.9
        assert call_kwargs['max_tokens'] == 4000

def test_create_crewai_llm(monkeypatch):
    """测试创建 CrewAI 兼容的 LLM"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.core.llm_setup.ChatAnthropic') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance

        llm = create_crewai_llm()

        # 验证返回的是 LangChain 的 ChatAnthropic
        assert llm == mock_instance
