"""测试ReAct Agent"""

import pytest
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.react_agent import ReActAgent, ToolRegistry


class TestToolRegistry:
    """测试工具注册表"""

    def test_register_and_get_tool(self):
        """测试工具注册和获取"""
        registry = ToolRegistry()

        def dummy_tool(x: str) -> str:
            return f"Hello {x}"

        registry.register("dummy", dummy_tool, "A dummy tool")

        # 检查工具是否注册成功
        assert registry.get("dummy") == dummy_tool
        assert registry.get_description("dummy") == "A dummy tool"

    def test_list_tools(self):
        """测试列出所有工具"""
        registry = ToolRegistry()

        def tool1():
            pass

        def tool2():
            pass

        registry.register("tool1", tool1, "Description 1")
        registry.register("tool2", tool2, "Description 2")

        tools = registry.list_tools()
        assert set(tools) == {"tool1", "tool2"}

    def test_get_nonexistent_tool(self):
        """测试获取不存在的工具"""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None


class TestReActAgent:
    """测试ReAct Agent"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例（不使用真实LLM）"""
        # 使用mock避免真实API调用
        class MockLLMClient:
            def generate(self, prompt: str, **kwargs) -> str:
                # 模拟简单响应
                return "Final Answer: 这是一个测试答案"

        agent = ReActAgent(llm_client=MockLLMClient())
        return agent

    def test_initialization(self, agent):
        """测试Agent初始化"""
        assert agent.llm_client is not None
        assert agent.tool_registry is not None
        assert len(agent.tool_registry.list_tools()) > 0

    def test_tools_registered(self, agent):
        """测试所有工具是否正确注册"""
        tools = agent.tool_registry.list_tools()

        # 检查核心工具是否存在
        expected_tools = [
            "analyze_code",
            "list_functions",
            "list_classes",
            "count_lines",
            "get_imports",
            "get_complexity",
            "read_file"
        ]

        for tool in expected_tools:
            assert tool in tools, f"工具 {tool} 未注册"

    def test_parse_response_with_final_answer(self):
        """测试解析包含Final Answer的响应"""
        agent = ReActAgent(llm_client=None)  # 不需要LLM来测试解析

        response = "Thought: 我现在知道答案了\nFinal Answer: Python文件包含3个类"
        thought, action, action_input, final_answer = agent._parse_response(response)

        assert final_answer == "Python文件包含3个类"

    def test_parse_response_with_action(self):
        """测试解析包含Action的响应"""
        agent = ReActAgent(llm_client=None)

        response = """Thought: 我需要分析这个文件
Action: list_classes
Action Input: {"file_path": "/path/to/file.py"}"""

        thought, action, action_input, final_answer = agent._parse_response(response)

        assert thought is not None
        assert action == "list_classes"
        assert action_input == {"file_path": "/path/to/file.py"}
        assert final_answer is None

    def test_execute_action_count_lines(self, agent, tmp_path):
        """测试执行count_lines工具"""
        # 创建临时测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("""
# 这是一个测试文件
def hello():
    print("Hello")

class MyClass:
    pass
""")

        result = agent._execute_action("count_lines", {"file_path": str(test_file)})

        assert "total" in result
        assert "code" in result

    def test_execute_action_read_file(self, agent, tmp_path):
        """测试执行read_file工具"""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        result = agent._execute_action("read_file", {"file_path": str(test_file)})

        assert "Hello, World!" in result

    def test_execute_invalid_action(self, agent):
        """测试执行不存在的工具"""
        result = agent._execute_action("nonexistent_tool", {})
        assert "错误" in result


class TestReActAgentIntegration:
    """集成测试（需要真实的测试文件）"""

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """创建示例Python文件"""
        file_path = tmp_path / "sample.py"
        file_path.write_text("""
\"\"\"示例模块\"\"\"

import os
from typing import List


def calculate_sum(a: int, b: int) -> int:
    \"\"\"计算两个数的和\"\"\"
    return a + b


class DataProcessor:
    \"\"\"数据处理器\"\"\"

    def __init__(self, name: str):
        self.name = name

    def process(self, data: List) -> dict:
        return {"result": len(data)}


if __name__ == "__main__":
    print("Module loaded")
""")
        return str(file_path)

    def test_full_code_analysis(self, sample_python_file):
        """测试完整的代码分析流程"""
        class MockLLMClient:
            def __init__(self, responses):
                self.responses = responses
                self.index = 0

            def generate(self, prompt: str, **kwargs) -> str:
                response = self.responses[self.index]
                self.index += 1
                return response

        # 模拟多轮对话
        responses = [
            # 第一轮：选择分析文件
            f"""Thought: 我需要先分析这个代码文件的结构
Action: analyze_code
Action Input: {{"file_path": "{sample_python_file}"}}""",
            # 第二轮：给出最终答案
            """Thought: 我已经获得了完整的分析结果
Final Answer: 该文件包含2个函数（calculate_sum和process）、1个类（DataProcessor）、8行代码、2个import语句。"""
        ]

        agent = ReActAgent(llm_client=MockLLMClient(responses))
        result = agent.run("分析这个文件", verbose=False)

        assert "类" in result or "函数" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
