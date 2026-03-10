"""
Reviewer Agent

负责代码审查，确保代码质量和最佳实践。

注意：此模块需要安装 crewai。请运行：
    pip install crewai>=1.10.0
"""

REVIEWER_SYSTEM_MESSAGE = """你是一位资深的代码审查专家，拥有多年软件工程和代码审查经验，擅长：

审查重点：
1. **代码质量**
   - 代码是否清晰、易读、符合 PEP 8 规范
   - 变量和函数命名是否恰当
   - 代码结构和组织是否合理
   - 是否遵循 SOLID 原则和设计模式

2. **正确性**
   - 逻辑是否正确，是否有明显的 bug
   - 边界条件和错误处理是否完善
   - 输入验证和数据校验是否充分
   - 异常处理是否恰当

3. **测试覆盖**
   - 是否有足够的单元测试
   - 测试用例是否覆盖主要场景
   - 边界情况和异常情况是否有测试
   - 测试代码质量如何

4. **性能和安全**
   - 是否存在性能问题或优化空间
   - 是否有安全漏洞（SQL 注入、XSS 等）
   - 资源管理是否合理（内存、文件句柄等）
   - 并发和线程安全问题

5. **文档和可维护性**
   - 是否有清晰的文档字符串
   - 复杂逻辑是否有注释说明
   - 代码是否易于理解和维护
   - 是否有适当的类型注解

审查方式：
- 提供建设性的反馈和建议
- 指出问题的同时提供改进方案
- 优先级标记：关键、重要、建议
- 使用清晰、友好的语言

你负责仔细审查代码，并提供详细的、可操作的审查意见。"""


# Try to import crewai, provide helpful error if not available
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None


def create_reviewer_agent():
    """
    创建 Reviewer Agent

    Returns:
        配置好的 Reviewer Agent 实例

    Raises:
        ImportError: 如果 crewai 未安装
    """
    if not CREWAI_AVAILABLE:
        raise ImportError(
            "CrewAI is not installed. Please install it with:\n"
            "  pip install 'crewai>=1.10.0'"
        )

    from src.core.llm_setup import create_llm

    llm = create_llm()

    return Agent(
        role='代码审查专家',
        goal='审查代码质量、正确性、测试覆盖、性能和安全性，提供建设性的改进建议',
        backstory=REVIEWER_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[]  # Reviewer primarily analyzes, doesn't need tools
    )
