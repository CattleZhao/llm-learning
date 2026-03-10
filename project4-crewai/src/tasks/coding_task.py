from crewai import Task


def create_coding_task(agent, description: str | None = None) -> Task:
    """
    Create a coding task for implementing user requirements.

    This task instructs the Coder agent to:
    - Understand user requirements
    - Write Python code to implement the solution
    - Follow best practices and coding standards
    - Include appropriate documentation

    Args:
        agent: The coder agent responsible for implementation
        description: Custom task description. If None, uses default description

    Returns:
        Task: A configured Task object for coding implementation
    """
    if description is None:
        description = """根据用户需求编写 Python 代码。

请完成以下工作：
1. 理解用户需求
2. 设计解决方案
3. 编写高质量 Python 代码
4. 添加必要的注释和文档字符串
5. 遵循 Python 最佳实践 (PEP 8)

代码要求：
- 清晰的结构和组织
- 适当的错误处理
- 良好的可维护性
- 充分的代码注释
"""
    return Task(
        description=description,
        agent=agent,
        expected_output="完整的 Python 代码实现，包含源代码和必要的使用说明"
    )
