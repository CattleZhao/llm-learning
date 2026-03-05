# src/llm_client.py
import os
from typing import Optional
from openai import OpenAI
from anthropic import Anthropic

class LLMClientBase:
    """LLM客户端基类"""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

class OpenAIClient(LLMClientBase):
    """OpenAI客户端"""
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """生成文本"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

class AnthropicClient(LLMClientBase):
    """Anthropic客户端"""
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """生成文本"""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")

class GLMClient(LLMClientBase):
    """智谱AI (Z.ai) 客户端 - 使用OpenAI兼容接口"""
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("ZhipuAI API key is required")
        super().__init__(api_key)
        # Z.ai使用OpenAI兼容的API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.z.ai/api/coding/paas/v4"  # Z.ai的OpenAI兼容端点
        )

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """生成文本"""
        try:
            response = self.client.chat.completions.create(
                model="GLM-4.7",  # Z.ai使用的模型
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"ZhipuAI API error: {e}")

def get_client(provider: str = "openai") -> LLMClientBase:
    """工厂函数：获取LLM客户端"""
    providers = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "glm": GLMClient,
        "zhipu": GLMClient,  # 别名
        "zhipuai": GLMClient,  # 别名
    }
    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")
    return providers[provider]()
