# src/summary_module.py
from dotenv import load_dotenv
load_dotenv()

from typing import Optional
from .llm_client import get_client

class SummaryModule:
    """文档摘要模块"""

    def __init__(self, provider: str = "openai"):
        """
        初始化摘要模块

        Args:
            provider: LLM提供商 (openai | anthropic | glm | zhipu)
        """
        self.client = get_client(provider)

    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """
        生成文本摘要

        Args:
            text: 待摘要的文本
            max_length: 摘要最大长度（字符数）

        Returns:
            摘要文本
        """
        prompt = self._build_prompt(text, max_length)
        return self.client.generate(prompt, temperature=0.5)

    def _build_prompt(self, text: str, max_length: Optional[int]) -> str:
        """
        构建提示词

        Args:
            text: 待摘要的文本
            max_length: 摘要最大长度

        Returns:
            完整的提示词
        """
        length_constraint = ""
        if max_length:
            length_constraint = f"摘要长度控制在{max_length}字以内。"

        return f"""请对以下文本生成简洁的摘要：

{text}

要求：
1. 准确概括原文要点
2. 保持简洁明了
3. {length_constraint}

摘要："""
