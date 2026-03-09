"""
Pytest 配置和共享 fixtures
"""
import pytest
import os


def pytest_configure(config):
    """配置 pytest 标记"""
    config.addinivalue_line(
        "markers",
        "integration: 标记集成测试（可能需要 API key）"
    )
    config.addinivalue_line(
        "markers",
        "slow: 标记运行较慢的测试"
    )


@pytest.fixture
def mock_api_key(monkeypatch):
    """提供模拟 API key 的 fixture"""
    test_key = "test_key_" + "x" * 40
    monkeypatch.setenv("OPENAI_API_KEY", test_key)
    return test_key


@pytest.fixture
def temp_api_key(mock_api_key):
    """临时设置 API key 的 fixture"""
    original_key = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_KEY'] = mock_api_key
    yield mock_api_key
    if original_key:
        os.environ['OPENAI_API_KEY'] = original_key
    else:
        os.environ.pop('OPENAI_API_KEY', None)


@pytest.fixture
def mock_config(temp_api_key):
    """提供模拟配置的 fixture"""
    from src.core.config import Config
    from unittest.mock import Mock

    config = Mock()
    config.api_key = temp_api_key
    config.model = "gpt-3.5-turbo"
    config.temperature = 0.7
    config.max_tokens = 1000
    config.use_docker = False
    config.work_dir = "./outputs"
    config.max_consecutive_auto_reply = 10
    config.get_llm_config.return_value = {
        "model": "gpt-3.5-turbo",
        "api_key": temp_api_key,
        "temperature": 0.7,
        "max_tokens": 1000,
    }
    config.get_code_execution_config.return_value = {
        "work_dir": "./outputs",
        "use_docker": False,
    }

    return config
