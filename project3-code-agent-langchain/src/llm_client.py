"""
LLM 客户端 - LangChain 版本

使用 LangChain 的 ChatOpenAI 替代自研实现
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def create_llm(temperature: float = 0.3, model: str = None, verbose: bool = False):
    """
    创建 LangChain LLM 实例

    Args:
        temperature: 生成温度 (0-1)
        model: 模型名称，默认从环境变量读取
        verbose: 是否打印详细日志

    Returns:
        ChatOpenAI 实例
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Please set it in .env file or environment variables."
        )

    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        verbose=verbose,
    )


# 简单的 LLM 客户端包装类（保持与原项目接口兼容）
class SimpleLLMClient:
    """简单的 LLM 客户端包装"""

    def __init__(self, temperature: float = 0.3, model: str = None):
        self.llm = create_llm(temperature=temperature, model=model)

    def generate(self, prompt: str, temperature: float = None) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            temperature: 温度（覆盖初始化时的值）

        Returns:
            生成的文本
        """
        from langchain.schema import HumanMessage

        if temperature is not None:
            original_temp = self.llm.temperature
            self.llm.temperature = temperature
            result = self.llm.invoke([HumanMessage(content=prompt)])
            self.llm.temperature = original_temp
        else:
            result = self.llm.invoke([HumanMessage(content=prompt)])

        return result.content

    def chat(self, messages: list) -> str:
        """
        聊天模式

        Args:
            messages: 消息列表，每个消息是 {"role": "...", "content": "..."} 格式

        Returns:
            AI 回复
        """
        from langchain.schema import HumanMessage, AIMessage, SystemMessage

        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user
                langchain_messages.append(HumanMessage(content=content))

        result = self.llm.invoke(langchain_messages)
        return result.content
