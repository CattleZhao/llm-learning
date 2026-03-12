"""
基础 Agent 实现

使用 LangChain 和 Anthropic Claude API 的基础对话 Agent
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional, Dict, List
from anthropic import Anthropic
from agents.base import BaseAgent, AgentResponse
from config import get_settings


class BasicConversationAgent(BaseAgent):
    """
    基础对话 Agent

    使用 Claude API 进行对话的简单 Agent 实现
    """

    def __init__(
        self,
        name: str = "Claude",
        description: str = "一个有帮助的 AI 助手",
        **kwargs
    ):
        super().__init__(name=name, description=description, **kwargs)
        self.settings = get_settings()
        self.client = Anthropic(
            api_key=self.settings.anthropic_api_key,
            base_url=self.settings.anthropic_base_url
        )

    def think(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> AgentResponse:
        """
        执行思考并生成响应

        Args:
            input_text: 用户输入
            context: 额外上下文

        Returns:
            AgentResponse 对象
        """
        # 构建消息列表
        messages = []

        # 添加系统提示
        system_prompt = self._build_system_prompt()

        # 添加对话历史（如果有）
        if self.enable_memory and self.state.conversation_history:
            for msg in self.state.conversation_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

        # 添加当前输入
        messages.append({
            "role": "user",
            "content": input_text
        })

        # 调用 Claude API
        try:
            response = self.client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            )

            content = response.content[0].text

            return AgentResponse(
                content=content,
                metadata={
                    "model": self.settings.anthropic_model,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )

        except Exception as e:
            return AgentResponse(
                content=f"抱歉，处理您的请求时出错: {str(e)}",
                metadata={"error": str(e)}
            )

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""你是{self.name}，{self.description}

你的角色: {self.role}

请根据用户的问题提供有帮助的回答。
"""

    def stream_think(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ):
        """
        流式思考（生成器）

        Args:
            input_text: 用户输入
            context: 额外上下文

        Yields:
            文本块
        """
        messages = []
        system_prompt = self._build_system_prompt()

        if self.enable_memory and self.state.conversation_history:
            for msg in self.state.conversation_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

        messages.append({
            "role": "user",
            "content": input_text
        })

        try:
            with self.client.messages.stream(
                model=self.settings.anthropic_model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as e:
            yield f"错误: {str(e)}"


# 便捷函数
def create_agent(
    name: str = "Claude",
    description: str = "一个有帮助的 AI 助手",
    enable_memory: bool = True
) -> BasicConversationAgent:
    """
    创建一个 Agent 实例

    Args:
        name: Agent 名称
        description: Agent 描述
        enable_memory: 是否启用记忆

    Returns:
        BasicConversationAgent 实例
    """
    return BasicConversationAgent(
        name=name,
        description=description,
        enable_memory=enable_memory
    )
