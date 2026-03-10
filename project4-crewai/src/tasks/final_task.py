from crewai import Task


def create_final_task(agent, context: list | None = None) -> Task:
    """
    Create a final task that aggregates all work from previous stages.

    This task generates a comprehensive delivery report that includes:
    - Summary of the development work completed
    - Code review findings
    - Testing results
    - Final deliverables

    Args:
        agent: The coordinator agent responsible for final aggregation
        context: List of previous tasks (coding, review, testing) to reference

    Returns:
        Task: A configured Task object for final reporting
    """
    description = """汇总所有阶段的工作成果，生成最终交付报告。

请完成以下工作：
1. 整合 Coder 生成的代码
2. 包含 Reviewer 的审查意见
3. 汇总 Tester 的测试结果
4. 生成完整的任务交付报告

报告应包含：
- 任务概述
- 实现代码
- 审查反馈
- 测试结果
- 最终结论和建议
"""
    return Task(
        description=description,
        agent=agent,
        context=context or [],
        expected_output="完整的任务交付报告，包含代码、审查和测试的完整汇总"
    )
