"""
Reviewer Agent 模块

Reviewer 负责确保代码质量，检查代码是否符合最佳实践。
"""
from typing import Optional, Callable
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== Reviewer 的系统消息 ==========
REVIEWER_SYSTEM_MESSAGE = """You are a code review expert responsible for ensuring code quality.

Your review checklist:

1. **Correctness**: Does the code do what it's supposed to do?
   - Check for logical errors
   - Verify edge cases are handled
   - Ensure the implementation matches requirements

2. **Code Style**: Does the code follow PEP 8 and best practices?
   - Check naming conventions
   - Verify proper indentation
   - Look for overly complex code that could be simplified

3. **Documentation**: Is the code properly documented?
   - Are there docstrings for functions and classes?
   - Are comments helpful and not redundant?
   - Is complex logic explained?

4. **Performance**: Are there any obvious performance issues?
   - Check for inefficient algorithms
   - Look for unnecessary computations
   - Consider time and space complexity

5. **Security**: Are there any security vulnerabilities?
   - Check for hardcoded secrets
   - Verify input validation
   - Look for potential injection attacks

6. **Error Handling**: Are errors handled appropriately?
   - Check for proper exception handling
   - Verify error messages are helpful
   - Ensure resources are cleaned up

Review format:

For each issue found:
```
**Problem**: [Clearly describe the issue]
**Location**: [Specify where the issue is]
**Suggestion**: [Provide a concrete improvement suggestion]
```

If the code is good:
- Acknowledge what's done well
- Suggest any minor improvements if applicable
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
    is_termination_msg: Optional[Callable[[str], bool]] = None,
) -> AssistantAgent:
    """
    创建一个 Reviewer agent

    Reviewer 负责审查代码质量并提供改进建议。

    Args:
        config: 配置对象
        name: Agent 名称
        system_message: 自定义系统消息（如果不提供则使用默认）
        is_termination_msg: 判断是否终止的函数

    Returns:
        配置好的 AssistantAgent 实例
    """
    logger.info(f"Creating Reviewer agent: {name}")

    if system_message is None:
        system_message = REVIEWER_SYSTEM_MESSAGE

    # 默认终止消息检测
    if is_termination_msg is None:
        def is_termination_msg(msg: str) -> bool:
            return "TERMINATE" in msg.upper() or "APPROVED" in msg.upper()

    # 创建 Agent，使用 LLM 配置
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
        is_termination_msg=is_termination_msg,
    )

    logger.info(f"Reviewer agent '{name}' created successfully")
    return agent
