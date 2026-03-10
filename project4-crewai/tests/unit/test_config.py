import os
import pytest
from src.core.config import Config, get_config

def test_config_loads_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("TEMPERATURE", "0.5")
    monkeypatch.setenv("CODE_EXECUTION_WORK_DIR", "/tmp/test")

    config = Config()
    assert config.api_key == "test-key"
    assert config.model == "claude-3-5-sonnet-20241022"
    assert config.temperature == 0.5
    assert config.work_dir == "/tmp/test"

def test_config_default_values(monkeypatch):
    """测试默认配置值"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # 清除其他环境变量
    for key in ["ANTHROPIC_MODEL", "TEMPERATURE", "MAX_TOKENS", "CODE_EXECUTION_WORK_DIR"]:
        monkeypatch.delenv(key, raising=False)

    config = Config()
    assert config.model == "claude-sonnet-4-20250514"
    assert config.temperature == 0.7
    assert config.max_tokens == 2000
    assert config.work_dir == "./outputs"

def test_config_requires_api_key(monkeypatch):
    """测试缺少 API key 时抛出错误"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
        Config()

def test_get_config_singleton(monkeypatch):
    """测试单例模式"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

def test_work_dir_created(monkeypatch, tmp_path):
    """测试工作目录自动创建"""
    work_dir = str(tmp_path / "outputs")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("CODE_EXECUTION_WORK_DIR", work_dir)

    config = Config()
    assert os.path.exists(work_dir)
