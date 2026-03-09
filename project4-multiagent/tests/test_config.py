"""
配置管理模块测试
"""
import os
import pytest
from src.core.config import Config, get_config, set_config


def test_config_loads_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key_123')
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-4')

    config = Config()
    assert config.api_key == 'test_key_123'
    assert config.model == 'gpt-4'


def test_config_has_defaults(monkeypatch):
    """测试配置有合理的默认值"""
    # 清除环境变量
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('OPENAI_MODEL', raising=False)

    # 这个测试会因为没有 API key 而失败，这是预期行为
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        Config()


def test_config_default_values(monkeypatch):
    """测试配置的默认值（有 API key 时）"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    config = Config()
    assert config.model == 'gpt-4o'
    assert config.use_docker is False
    assert config.work_dir == './outputs'
    assert config.temperature == 0.7
    assert config.max_tokens == 2000


def test_config_llm_config(monkeypatch):
    """测试 LLM 配置格式正确"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-4')
    monkeypatch.setenv('TEMPERATURE', '0.5')

    config = Config()
    llm_config = config.get_llm_config()

    assert llm_config['model'] == 'gpt-4'
    assert llm_config['api_key'] == 'test_key'
    assert llm_config['temperature'] == 0.5


def test_config_code_execution_config(monkeypatch):
    """测试代码执行配置"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
    monkeypatch.setenv('CODE_EXECUTION_WORK_DIR', './test_outputs')

    config = Config()
    code_config = config.get_code_execution_config()

    assert code_config['work_dir'] == './test_outputs'
    assert code_config['use_docker'] is False


def test_get_config_singleton(monkeypatch):
    """测试 get_config 返回单例"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')

    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_set_config(monkeypatch):
    """测试 set_config 可以设置自定义配置"""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.api_key = 'custom_key'

    set_config(mock_config)
    result = get_config()

    assert result is mock_config
    assert result.api_key == 'custom_key'
