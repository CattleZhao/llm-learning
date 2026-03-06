# src/llm_client.py
"""
LLM客户端 - 连接到Z.ai的GLM模型
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

def get_client():
    """
    获取LLM客户端（Z.ai GLM）

    Returns:
        配置好的OpenAI客户端
    """
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        raise ValueError("ZHIPUAI_API_KEY not found in environment")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.z.ai/api/coding/paas/v4"
    )

    return client

class SimpleLLMClient:
    """简化的LLM客户端"""

    def __init__(self):
        self.client = get_client()

    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            **kwargs: 其他参数（temperature, max_tokens等）

        Returns:
            生成的文本
        """
        try:
            response = self.client.chat.completions.create(
                model="GLM-4.7",
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成出错: {e}"
