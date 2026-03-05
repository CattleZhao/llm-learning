# tests/test_llm_client.py
import pytest
from src.llm_client import OpenAIClient, GLMClient, get_client

def test_openai_client_init():
    """测试OpenAI客户端初始化"""
    client = OpenAIClient(api_key="test_key")
    assert client.client is not None

def test_openai_client_generate_requires_api_key():
    """测试没有API密钥时生成失败"""
    client = OpenAIClient(api_key="invalid_key")
    with pytest.raises(Exception):
        client.generate(prompt="test")

def test_glm_client_init():
    """测试GLM客户端初始化"""
    client = GLMClient(api_key="test_key")
    assert client.client is not None

def test_glm_client_generate_requires_api_key():
    """测试GLM没有API密钥时生成失败"""
    client = GLMClient(api_key="invalid_key")
    with pytest.raises(Exception):
        client.generate(prompt="test")

def test_get_client_glm():
    """测试通过工厂函数获取GLM客户端"""
    # 设置临时环境变量
    import os
    os.environ["ZHIPUAI_API_KEY"] = "test_key"
    client = get_client("glm")
    assert isinstance(client, GLMClient)
