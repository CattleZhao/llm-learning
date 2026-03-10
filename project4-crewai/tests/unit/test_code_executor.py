"""
测试 CodeExecutor 工具
"""
import pytest
from src.tools.code_executor import execute_code, CodeExecutorTool


class TestExecuteCode:
    """测试 execute_code 函数"""

    def test_execute_code_success(self):
        """测试成功执行代码"""
        code = """
print("Hello, World!")
result = 2 + 2
print(f"Result: {result}")
"""
        result = execute_code(code)

        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Hello, World!" in result["stdout"]
        assert "Result: 4" in result["stdout"]
        assert result["stderr"] == ""
        assert result["error"] is None

    def test_execute_code_syntax_error(self):
        """测试语法错误"""
        code = """
print("Hello"
if True
    print("missing colon")
"""
        result = execute_code(code)

        assert result["success"] is False
        assert result["returncode"] != 0
        assert result["stderr"] != ""  # Python syntax errors go to stderr
        assert result["error"] is None

    def test_execute_code_runtime_error(self):
        """测试运行时错误"""
        code = """
x = 10
y = 0
result = x / y  # Division by zero
print(result)
"""
        result = execute_code(code)

        assert result["success"] is False
        assert result["returncode"] != 0
        assert "ZeroDivisionError" in result["stderr"]
        assert result["error"] is None

    def test_execute_code_timeout(self):
        """测试超时"""
        code = """
import time
time.sleep(35)  # Sleep longer than default timeout
"""
        result = execute_code(code, timeout=2)

        assert result["success"] is False
        assert result["returncode"] == -1
        assert "timeout" in result["error"].lower()
        assert "2 seconds" in result["error"]


class TestCodeExecutorTool:
    """测试 CodeExecutorTool 类"""

    def test_tool_schema(self):
        """测试工具 schema"""
        tool = CodeExecutorTool()
        schema = tool.get_schema()

        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "execute_code"
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]

        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "code" in params["properties"]
        assert "timeout" in params["properties"]
        assert params["properties"]["code"]["type"] == "string"
        assert params["properties"]["timeout"]["type"] == "integer"
        assert params["properties"]["timeout"]["default"] == 30
        assert "code" in params["required"]

    def test_tool_run_success(self):
        """测试工具运行成功"""
        tool = CodeExecutorTool()
        result = tool.run(code='print("Test successful")')

        assert "✓" in result or "成功" in result
        assert "Test successful" in result

    def test_tool_run_failure(self):
        """测试工具运行失败"""
        tool = CodeExecutorTool()
        result = tool.run(code="invalid syntax here")

        assert "✗" in result or "失败" in result
        assert "错误" in result or "Error" in result.lower()
