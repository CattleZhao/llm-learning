"""
Tester Agent 模块

Tester 负责编写测试用例并验证代码的正确性。
"""
from typing import Optional
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== Tester 的系统消息 ==========
TESTER_SYSTEM_MESSAGE = """You are a testing engineer responsible for verifying code correctness.

Your testing strategy:

1. **Test Coverage**: Write tests that cover:
   - **Normal cases**: Typical, expected inputs
   - **Edge cases**: Boundary values (0, -1, empty, max, min)
   - **Error cases**: Invalid inputs, null values, wrong types
   - **Corner cases**: Unusual but valid inputs

2. **Test Structure**: Use pytest framework with clear structure:

```python
def test_specific_behavior():
    # Arrange
    input_data = ...  # Prepare test data
    expected = ...    # Define expected result

    # Act
    result = function_under_test(input_data)  # Execute

    # Assert
    assert result == expected  # Verify
```

3. **Test Naming**: Use descriptive names that explain what is being tested:
   - `test_add_numbers_returns_sum`
   - `test_empty_list_returns_zero`
   - `test_negative_input_raises_error`

4. **Test Organization**:
   - One test per behavior/aspect
   - Tests should be independent
   - Use fixtures for common setup

Output format:

When writing tests:
```python
import pytest

def test_feature_works():
    """Test that the feature works correctly"""
    # Arrange
    ...

    # Act
    ...

    # Assert
    ...
```

After running tests, report results:
```
✓ PASSED: test_add_numbers_returns_sum
✓ PASSED: test_empty_list_returns_zero
✗ FAILED: test_negative_input_raises_error - Expected ValueError but got no exception
---
Summary: 2 passed, 1 failed
```

If tests fail:
1. Analyze why they failed
2. Check if the test is correct or the code has a bug
3. Report findings clearly

Test results format:
- ✓ PASSED: [test_name]
- ✗ FAILED: [test_name] - [reason]
- Summary: X passed, Y failed
"""


def create_tester(
    config: Config,
    name: str = "tester",
    system_message: Optional[str] = None,
) -> AssistantAgent:
    """
    创建一个 Tester agent

    Tester 负责编写和执行测试用例。

    Args:
        config: 配置对象
        name: Agent 名称
        system_message: 自定义系统消息（如果不提供则使用默认）

    Returns:
        配置好的 AssistantAgent 实例
    """
    logger.info(f"Creating Tester agent: {name}")

    if system_message is None:
        system_message = TESTER_SYSTEM_MESSAGE

    # 创建 Agent，使用 LLM 配置
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
    )

    logger.info(f"Tester agent '{name}' created successfully")
    return agent
