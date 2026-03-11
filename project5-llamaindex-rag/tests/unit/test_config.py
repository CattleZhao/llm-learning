import os
import pytest
from src.config import Settings, get_settings, reset_settings

@pytest.fixture(autouse=True)
def reset_settings_before_each_test():
    """在每个测试前重置设置"""
    reset_settings()
    yield

def test_settings_load_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://test.anthropic.com")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("CHUNK_SIZE", "256")

    settings = get_settings()
    assert settings.anthropic_api_key == "test-key"
    assert settings.anthropic_base_url == "https://test.anthropic.com"
    assert settings.anthropic_model == "claude-3-5-sonnet-20241022"
    assert settings.chunk_size == 256

def test_settings_default_values(monkeypatch):
    """测试默认配置值"""
    # 清除环境变量
    for key in ["ANTHROPIC_MODEL", "HF_EMBED_MODEL", "EMBED_DEVICE", "CHUNK_SIZE"]:
        monkeypatch.delenv(key, raising=False)
    # 设置必需的 API key
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-default-key")

    settings = get_settings()
    assert settings.anthropic_model == "claude-sonnet-4-20250514"
    assert settings.hf_embed_model == "nomic-ai/nomic-embed-text-v1.5"
    assert settings.embed_device == "cpu"
    assert settings.chunk_size == 512

def test_settings_hf_embed_config(monkeypatch):
    """测试 Hugging Face 嵌入配置"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-hf-key")
    monkeypatch.setenv("HF_EMBED_MODEL", "BAAI/bge-large-zh-v1.5")
    monkeypatch.setenv("EMBED_DEVICE", "cuda")

    settings = get_settings()
    assert settings.hf_embed_model == "BAAI/bge-large-zh-v1.5"
    assert settings.embed_device == "cuda"
