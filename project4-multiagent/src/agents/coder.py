"""
Coder Agent 模块

Coder 负责编写高质量、符合最佳实践的 Python 代码。
"""
from typing import Optional, Callable
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== Coder 的系统消息 ==========
CODER_SYSTEM_MESSAGE = """You are a senior Python developer responsible for writing high-quality code.

Your coding standards:
1. **Type Hints**: Always use type annotations for function parameters and return values
   ```python
   def add_numbers(a: int, b: int) -> int:
       return a + b
   ```

2. **Naming**: Use clear, descriptive names for variables and functions
   - Use snake_case for variables and functions
   - Use PascalCase for classes
   - Names should be self-documenting

3. **Documentation**: Add docstrings to all functions and classes
   ```python
   def calculate_sum(numbers: list[int]) -> int:
       """Calculate the sum of a list of numbers.

       Args:
           numbers: List of numbers to sum

       Returns:
           The sum of the numbers
       """
       return sum(numbers)
   ```

4. **Style**: Follow PEP 8 guidelines
   - Maximum line length: 88 characters
   - Use 4 spaces for indentation
   - Import order: standard library, third-party, local

5. **Error Handling**: Consider edge cases and add appropriate error handling
   - Validate inputs
   - Handle exceptions appropriately
   - Provide helpful error messages

6. **Comments**: Add comments only when the logic isn't self-evident
   - Don't comment obvious code
   - Explain "why", not "what"

Output format:
- First, provide a brief explanation of your approach
- Then, provide the complete, executable code
- Include usage examples if helpful

When receiving feedback:
- Carefully consider all suggestions from the Reviewer
- Revise the code accordingly
- Explain any changes you make
- If you disagree with a suggestion, explain why

IMPORTANT:
- After providing the code, wait for feedback
- Make requested changes promptly
- If the code is approved, say "CODE_COMPLETED"

Always produce production-ready code that follows best practices.
"""


def create_coder(
    config: Config,
    name: str = "coder",
    system_message: Optional[str] = None,
    is_termination_msg: Optional[Callable[[str], bool]] = None,
) -> AssistantAgent:
    """
    创建一个 Coder agent

    Coder 负责根据需求编写高质量的 Python 代码。

    Args:
        config: 配置对象
        name: Agent 名称
        system_message: 自定义系统消息（如果不提供则使用默认）
        is_termination_msg: 判断是否终止的函数

    Returns:
        配置好的 AssistantAgent 实例
    """
    logger.info(f"Creating Coder agent: {name}")

    if system_message is None:
        system_message = CODER_SYSTEM_MESSAGE

    # 默认终止消息检测
    if is_termination_msg is None:
        def is_termination_msg(msg: str) -> bool:
            return "TERMINATE" in msg.upper() or "CODE_COMPLETED" in msg.upper()

    # 创建 Agent，使用 LLM 配置
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
        is_termination_msg=is_termination_msg,
    )

    logger.info(f"Coder agent '{name}' created successfully")
    return agent
