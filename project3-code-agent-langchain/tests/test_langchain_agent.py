"""
LangChain Agent 测试
"""
import sys
from pathlib import Path
import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.langchain_agent import LangChainCodeAgent
from tools.langchain_tools import get_all_tools


class TestLangChainTools:
    """测试 LangChain 工具"""

    def test_tools_count(self):
        """测试工具数量"""
        tools = get_all_tools()
        assert len(tools) == 7

    def test_tool_names(self):
        """测试工具名称"""
        tools = get_all_tools()
        tool_names = [t.name for t in tools]
        expected = [
            "analyze_code",
            "list_functions",
            "list_classes",
            "count_lines",
            "get_imports",
            "get_complexity",
            "read_file"
        ]
        for name in expected:
            assert name in tool_names

    def test_analyze_code_tool(self):
        """测试 analyze_code 工具"""
        from tools.langchain_tools import analyze_code

        # 创建测试文件
        test_file = Path("/tmp/test_langchain_code.py")
        test_file.write_text("def test(): pass")

        result = analyze_code(str(test_file))
        assert isinstance(result, dict)
        assert "functions" in result

        # 清理
        test_file.unlink()


class TestLangChainAgent:
    """测试 LangChain Agent"""

    def test_agent_creation(self):
        """测试 Agent 创建"""
        agent = LangChainCodeAgent()
        assert agent.llm is not None
        assert len(agent.tools) > 0
        assert agent.agent is not None
        assert agent.agent_executor is not None

    def test_analyze_code_direct(self):
        """测试直接分析代码"""
        agent = LangChainCodeAgent()

        # 创建测试文件
        test_file = Path("/tmp/test_langchain_analyze.py")
        test_file.write_text('''
def hello():
    print("hello")

class TestClass:
    pass
''')

        result = agent.analyze_code(str(test_file))
        assert isinstance(result, dict)
        assert "functions" in result
        assert len(result["functions"]) >= 1

        # 清理
        test_file.unlink()

    def test_evaluate_quality(self):
        """测试质量评估"""
        agent = LangChainCodeAgent()

        # 创建测试文件
        test_file = Path("/tmp/test_langchain_quality.py")
        test_file.write_text("def simple(): pass")

        result = agent.evaluate_quality(str(test_file))
        assert isinstance(result, dict)
        assert "score" in result
        assert "level" in result
        assert 0 <= result["score"] <= 100

        # 清理
        test_file.unlink()

    def test_context(self):
        """测试获取上下文"""
        agent = LangChainCodeAgent()
        context = agent.get_context()
        assert isinstance(context, dict)
        assert "conversation_summary" in context
        assert "project_stats" in context


class TestLLMClient:
    """测试 LLM 客户端"""

    def test_create_llm(self):
        """测试创建 LLM"""
        from llm_client import create_llm
        llm = create_llm()
        assert llm is not None
        assert llm.temperature == 0.3

    def test_simple_llm_client(self):
        """测试 SimpleLLMClient"""
        from llm_client import SimpleLLMClient
        client = SimpleLLMClient()
        assert client.llm is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
