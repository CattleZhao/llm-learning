from crewai import Task


def create_review_task(agent, context: list | None = None) -> Task:
    """
    Create a code review task to evaluate code quality.

    This task reviews the code produced by the Coder agent and provides:
    - Code quality assessment
    - Best practices compliance
    - Potential bug identification
    - Improvement suggestions

    Args:
        agent: The reviewer agent responsible for code review
        context: List of previous tasks (typically the coding task) to review

    Returns:
        Task: A configured Task object for code review
    """
    description = """审查 Coder 产生的代码质量。

请完成以下审查工作：
1. 代码质量评估
    - 代码结构和组织
    - 命名规范
    - 代码可读性

2. 最佳实践检查
    - Python 编码规范 (PEP 8)
    - 设计模式应用
    - 错误处理机制

3. 潜在问题识别
    - 逻辑错误
    - 边界条件处理
    - 性能问题

4. 改进建议
    - 具体的优化建议
    - 重构建议
    - 文档补充建议
"""
    return Task(
        description=description,
        agent=agent,
        context=context or [],
        expected_output="详细的代码审查报告，包含问题清单、严重程度和改进建议"
    )
