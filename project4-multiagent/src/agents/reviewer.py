"""
Reviewer Agent 模块

Reviewer 负责确保代码质量，检查代码是否符合最佳实践。
"""
from typing import Optional
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== Reviewer 的系统消息 ==========
REVIEWER_SYSTEM_MESSAGE = """You are a code review expert responsible for ensuring code quality.

Your review checklist:

1. **Correctness**: Does the code do what it's supposed to do?
2. **Code Style**: Does the code follow PEP 8 and best practices?
3. **Documentation**: Is the code properly documented?
4. **Performance**: Are there any obvious performance issues?
5. **Security**: Are there any security vulnerabilities?
6. **Error Handling**: Are errors handled appropriately?

Review format:
- For each issue found: describe the problem, location, and provide a suggestion
- If the code is good: acknowledge what's done well
- Clearly state: "APPROVED" or "NEEDS_REVISION"

Be constructive and specific in your feedback. Help the coder improve their work.

IMPORTANT:
- After review, clearly state your decision: "APPROVED" or "NEEDS_REVISION"
- If approved, the coder can proceed
- If needs revision, list specific issues to address
"""


def create_reviewer(
    config: Config,
    name: str = "reviewer",
    system_message: Optional[str] = None,
) -> AssistantAgent:
    """
    创建一个 Reviewer agent

    Reviewer 负责审查代码质量并提供改进建议。

    Args:
        config: 配置对象
        name: Agent 名称
        system_message: 自定义系统消息（如果不提供则使用默认）

    Returns:
        配置好的 AssistantAgent 实例
    """
    logger.info(f"Creating Reviewer agent: {name}")

    if system_message is None:
        system_message = REVIEWER_SYSTEM_MESSAGE

    # 获取模型配置
    model_config = config.get_model_config()

    # 创建 Agent，使用新的 API
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        model_client=model_config['model_client'],
        temperature=model_config.get('temperature'),
    )

    logger.info(f"Reviewer agent '{name}' created successfully")
    return agent
