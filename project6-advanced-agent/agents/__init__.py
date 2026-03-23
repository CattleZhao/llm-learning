"""
Agents 模块

提供各种 Agent 实现
"""
from agents.base import BaseAgent, AgentResponse, AgentState, ToolExecutor

# 传统 Agent
from agents.apk_agent import APKAnalysisAgent, create_apk_agent
from agents.apk_agent_llm import LLMAPKAnalysisAgent, create_llm_agent

# LangChain Agent
from agents.langchain_agent import LangChainAPKAgent, create_langchain_agent

# 上下文压缩相关
from agents.advanced_compressor import (
    create_advanced_compressor,
    AdvancedContextCompressor,
    AdvancedCompressionConfig
)
from agents.cache_manager import ToolResultCache, get_tool_cache
from agents.llm_summarizer import LLMSummarizer, get_llm_summarizer

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "AgentState",
    "ToolExecutor",
    # 传统 Agent
    "APKAnalysisAgent",
    "create_apk_agent",
    "LLMAPKAnalysisAgent",
    "create_llm_agent",
    # LangChain Agent
    "LangChainAPKAgent",
    "create_langchain_agent",
    # 高级压缩
    "create_advanced_compressor",
    "AdvancedContextCompressor",
    "AdvancedCompressionConfig",
    # 缓存和摘要
    "ToolResultCache",
    "get_tool_cache",
    "LLMSummarizer",
    "get_llm_summarizer",
]
