# tests/test_llm_client.py
import pytest
from src.llm_client import OpenAIClient

def test_openai_client_init():
    """测试OpenAI客户端初始化"""
    client = OpenAIClient(api_key="test_key")
    assert client.client is not None

def test_openai_client_generate_requires_api_key():
    """测试没有API密钥时生成失败"""
    client = OpenAIClient(api_key="invalid_key")
    with pytest.raises(Exception):
        client.generate(prompt="test")
