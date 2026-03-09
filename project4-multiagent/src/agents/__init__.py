"""
Agents 模块

包含所有 Agent 的创建函数和系统消息。
"""
from src.agents.user_proxy import (
    create_user_proxy,
    create_user_proxy_for_web,
    USER_PROXY_SYSTEM_MESSAGE,
)
from src.agents.coder import create_coder, CODER_SYSTEM_MESSAGE
from src.agents.reviewer import create_reviewer, REVIEWER_SYSTEM_MESSAGE
from src.agents.tester import create_tester, TESTER_SYSTEM_MESSAGE

__all__ = [
    'create_user_proxy',
    'create_user_proxy_for_web',
    'USER_PROXY_SYSTEM_MESSAGE',
    'create_coder',
    'CODER_SYSTEM_MESSAGE',
    'create_reviewer',
    'REVIEWER_SYSTEM_MESSAGE',
    'create_tester',
    'TESTER_SYSTEM_MESSAGE',
]
