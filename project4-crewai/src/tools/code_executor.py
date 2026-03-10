"""
代码执行工具

在沙箱环境中安全执行 Python 代码。
"""
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def execute_code(code: str, timeout: int = 30) -> dict:
    """
    在临时目录中执行 Python 代码

    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒）

    Returns:
        包含执行结果的字典:
        - success: 是否成功
        - returncode: 返回码
        - stdout: 标准输出
        - stderr: 标准错误
        - error: 错误信息（超时或其他异常）
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = Path(tmpdir) / "code.py"
        code_file.write_text(code, encoding='utf-8')

        try:
            result = subprocess.run(
                ["python", str(code_file)],
                capture_output=True,
                timeout=timeout,
                cwd=tmpdir,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": None
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "",
                "error": f"Execution timeout after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "",
                "error": str(e)
            }


class CodeExecutorTool:
    """CrewAI 兼容的代码执行工具"""

    def __init__(self):
        self.name = "execute_code"
        self.description = "执行 Python 代码并返回输出。输入: code (Python代码字符串), timeout (可选超时秒数，默认30)"

    def get_schema(self) -> dict:
        """返回工具的 schema 定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的 Python 代码"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒）",
                            "default": 30
                        }
                    },
                    "required": ["code"]
                }
            }
        }

    def run(self, code: str, timeout: int = 30) -> str:
        """
        执行代码并返回格式化结果

        Args:
            code: 要执行的 Python 代码
            timeout: 超时时间（秒）

        Returns:
            格式化的执行结果
        """
        result = execute_code(code, timeout)

        if result["success"]:
            output = result["stdout"] or "代码执行成功（无输出）"
            return f"✓ 代码执行成功\n\n输出:\n{output}"
        else:
            error_msg = result["error"] or result["stderr"]
            return f"✗ 代码执行失败\n\n错误:\n{error_msg}"
