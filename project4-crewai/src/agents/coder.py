"""
Coder Agent

负责编写高质量、符合最佳实践的 Python 代码。

注意：此模块需要安装 crewai。请运行：
    pip install crewai>=1.10.0
"""

CODER_SYSTEM_MESSAGE = """你是一位经验丰富的 Python 高级软件工程师，擅长：

技术专长：
- 编写清晰、可维护、符合 PEP 8 规范的 Python 代码
- 遵循 SOLID 原则和设计模式
- 编写全面的单元测试（使用 pytest）
- 添加详细的文档字符串和类型注解
- 处理边界情况和错误处理

工作方式：
- 仔细分析需求，确保理解完整
- 编写模块化、可重用的代码
- 添加适当的日志记录
- 确保代码性能和安全性
- 遵循项目现有的代码风格和结构

质量控制：
- 在编写代码时考虑可测试性
- 使用有意义的变量和函数名
- 添加必要的注释解释复杂逻辑
- 考虑代码的可扩展性和维护性

你负责根据需求编写完整的 Python 代码实现，并将代码保存到适当的文件中。"""


# Try to import crewai, provide helpful error if not available
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None


def create_coder_agent():
    """
    创建 Coder Agent

    Returns:
        配置好的 Coder Agent 实例

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

    llm = create_llm()
    file_writer = FileWriterTool()

    return Agent(
        role='高级软件工程师',
        goal='编写高质量、符合最佳实践的 Python 代码',
        backstory=CODER_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[file_writer]
    )
