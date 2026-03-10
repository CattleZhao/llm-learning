"""
LLM 设置模块

负责创建和配置 LangChain 与 Anthropic 的 LLM 实例。
"""
from langchain_anthropic import ChatAnthropic
from src.core.config import get_config


def create_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None
) -> ChatAnthropic:
    """
    创建 LangChain ChatAnthropic 实例

    Args:
        model: 模型名称，如果为 None 则从配置读取
        temperature: 温度参数，如果为 None 则从配置读取
        max_tokens: 最大 token 数，如果为 None 则从配置读取

    Returns:
        ChatAnthropic 实例
    """
    config = get_config()

    return ChatAnthropic(
        model=model or config.model,
        temperature=temperature if temperature is not None else config.temperature,
        max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
        api_key=config.api_key,
    )


def create_crewai_llm() -> ChatAnthropic:
    """
    创建用于 CrewAI 的 LLM 实例

    CrewAI 可以直接使用 LangChain 的 ChatAnthropic。

    Returns:
        ChatAnthropic 实例
    """
    return create_llm()
