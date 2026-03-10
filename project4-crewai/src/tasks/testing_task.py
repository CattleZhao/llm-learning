from crewai import Task


def create_testing_task(agent, context: list | None = None) -> Task:
    """
    Create a testing task for validating the code implementation.

    This task instructs the Tester agent to:
    - Design and write comprehensive test cases
    - Execute the tests
    - Report test results and coverage
    - Identify any issues or bugs

    Args:
        agent: The tester agent responsible for testing
        context: List of previous tasks (coding and review) to test

    Returns:
        Task: A configured Task object for testing
    """
    description = """为代码编写并执行测试用例。

请完成以下测试工作：
1. 测试用例设计
    - 单元测试
    - 边界条件测试
    - 异常处理测试
    - 集成测试（如适用）

2. 测试执行
    - 编写测试代码
    - 运行测试套件
    - 记录测试结果

3. 测试报告
    - 测试覆盖率分析
    - 通过/失败统计
    - 发现的问题列表
    - 测试结论

4. 问题跟踪
    - 记录发现的 bug
    - 提供复现步骤
    - 给出修复建议
"""
    return Task(
        description=description,
        agent=agent,
        context=context or [],
        expected_output="完整的测试文件和详细的测试执行结果报告"
    )
