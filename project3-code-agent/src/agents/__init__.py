"""Agents package for code assistant"""

from .react_agent import ReActAgent, CodeAssistantAgent as ReActCodeAssistant, ToolRegistry

# Optional import for CodeAssistantAgent (may have dependency issues)
try:
    from .code_assistant_agent import CodeAssistantAgent
    _has_code_assistant = True
except ImportError:
    _has_code_assistant = False
    CodeAssistantAgent = ReActCodeAssistant  # Use ReActAgent as fallback

__all__ = ['ReActAgent', 'CodeAssistantAgent', 'ReActCodeAssistant', 'ToolRegistry']
