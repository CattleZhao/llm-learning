"""
Tester Agent 模块

Tester 负责编写测试用例并验证代码的正确性。
"""
from typing import Optional, Callable
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== Tester 的系统消息 ==========
TESTER_SYSTEM_MESSAGE = """You are a testing engineer responsible for verifying code correctness.

Your testing strategy:
1. **Test Coverage**: Write tests that cover normal cases, edge cases, boundary conditions, and error cases
2. **Test Structure**: Use pytest framework with clear test names and Arrange-Act-Assert pattern
3. **Test Organization**: One test per behavior, tests should be independent
4. **Test Results**: Report results as PASSED/FAILED with clear descriptions

Output format:
- First, describe what you're testing
- Then, provide the complete test code using pytest
- Finally, run the tests and report results

When writing tests:
- Use descriptive test names
- Cover edge cases and boundary conditions
- Include error cases
- Verify error handling

After running tests:
- Report: PASSED: [test_name] or FAILED: [test_name] - [reason]
- Provide summary: X passed, Y failed

Test results format:
- PASSED: test_name
- FAILED: test_name - reason
- Summary: X passed, Y failed
"""


def create_tester(
    config: Config,
    name: str = "tester",
    system_message: Optional[str] = None,
    is_termination_msg: Optional[Callable[[dict], bool]] = None,
) -> AssistantAgent:
    """
    创建一个 Tester agent

    Tester 负责编写和执行测试用例。

    Args:
        config: 配置对象
        name: Agent 名称
        system_message: 自定义系统消息（如果不提供则使用默认）
        is_termination_msg: 判断是否终止的函数（接收消息字典）

    Returns:
        配置好的 AssistantAgent 实例
    """
    logger.info(f"Creating Tester agent: {name}")

    if system_message is None:
        system_message = TESTER_SYSTEM_MESSAGE

    # 默认终止消息检测
    if is_termination_msg is None:
        def is_termination_msg(msg: dict) -> bool:
            content = msg.get("content", "")
            return "TERMINATE" in content.upper() or "TESTS_COMPLETED" in content.upper()

    # 创建 Agent，使用 LLM 配置
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
        is_termination_msg=is_termination_msg,
    )

    logger.info(f"Tester agent '{name}' created successfully")
    return agent
