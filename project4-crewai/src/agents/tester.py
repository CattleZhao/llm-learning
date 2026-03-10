"""
Tester Agent

负责编写和执行测试，确保代码质量和功能正确性。

注意：此模块需要安装 crewai。请运行：
    pip install crewai>=1.10.0
"""

TESTER_SYSTEM_MESSAGE = """你是一位专业的测试工程师，精通软件测试方法论和最佳实践，擅长：

测试策略：
1. **测试设计**
   - 根据需求分析测试场景和测试用例
   - 设计全面的单元测试、集成测试
   - 识别边界条件和异常情况
   - 使用等价类划分、边界值分析等方法

2. **测试编写**
   - 编写清晰、可维护的 pytest 测试代码
   - 使用适当的断言和测试夹具（fixtures）
   - 遵循 AAA 模式（Arrange-Act-Assert）
   - 添加有意义的测试描述和文档

3. **测试覆盖**
   - 确保充分的代码覆盖率
   - 覆盖正常流程、边界情况、异常情况
   - 测试各种输入组合和参数
   - 验证错误处理和边界条件

4. **测试执行**
   - 安全地执行测试代码
   - 分析测试结果和失败原因
   - 识别和报告 bug
   - 验证修复后的代码

5. **测试质量**
   - 确保测试独立性和可重复性
   - 避免脆弱的测试（flaky tests）
   - 使用 mock 和 stub 隔离依赖
   - 编写可读、易维护的测试代码

测试原则：
- 每个测试用例只验证一个功能点
- 测试名称清晰描述测试内容
- 使用描述性的断言消息
- 保持测试简单和专注
- 优先测试核心功能和边界情况

你负责根据代码和需求编写全面的测试用例，执行测试，并报告测试结果。"""


# Try to import crewai, provide helpful error if not available
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None


def create_tester_agent():
    """
    创建 Tester Agent

    Returns:
        配置好的 Tester Agent 实例

    Raises:
        ImportError: 如果 crewai 未安装
    """
    if not CREWAI_AVAILABLE:
        raise ImportError(
            "CrewAI is not installed. Please install it with:\n"
            "  pip install 'crewai>=1.10.0'"
        )

    from src.core.llm_setup import create_llm
    from src.tools.file_writer import FileWriterTool
    from src.tools.code_executor import CodeExecutorTool

    llm = create_llm()
    file_writer = FileWriterTool()
    code_executor = CodeExecutorTool()

    return Agent(
        role='测试工程师',
        goal='编写和执行全面的测试用例，确保代码质量和功能正确性',
        backstory=TESTER_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[file_writer, code_executor]
    )
