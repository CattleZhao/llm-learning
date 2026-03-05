# src/qa_module.py
from dotenv import load_dotenv
load_dotenv()
from typing import Optional
from .llm_client import get_client

class QAModule:
    """问答模块"""

    def __init__(self, provider: str = "openai"):
        """
        初始化问答模块

        Args:
            provider: LLM提供商 (openai | anthropic | glm | zhipu)
        """
        self.client = get_client(provider)

    def ask(self, question: str, context: Optional[str] = None) -> str:
        """
        回答问题

        Args:
            question: 用户问题
            context: 可选的上下文信息

        Returns:
            答案文本
        """
        prompt = self._build_prompt(question, context)
        return self.client.generate(prompt)

    def _build_prompt(self, question: str, context: Optional[str]) -> str:
        """
        构建提示词

        Args:
            question: 用户问题
            context: 可选的上下文信息

        Returns:
            完整的提示词
        """
        if context:
            # 带上下文的问答（RAG的简化版）
            return f"""基于以下信息回答问题：

上下文：
{context}

问题：{question}

请仅基于上下文信息回答，如果上下文没有相关信息，请明确说明。"""
        else:
            # 纯问答（使用大模型的知识）
            return f"""请回答以下问题：

{question}

请提供准确、简洁的答案。"""
