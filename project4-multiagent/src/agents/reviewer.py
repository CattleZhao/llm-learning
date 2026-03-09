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
- Clearly state: "APPROVED"

If the code needs revision:
- List all issues that need to be addressed
- Clearly state: "NEEDS REVISION"

Be constructive and specific in your feedback. Help the coder improve their work.
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

    # 创建 Agent，使用 LLM 配置
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
    )

    logger.info(f"Reviewer agent '{name}' created successfully")
    return agent
