"""ReAct Agent演示脚本"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.react_agent import ReActAgent


def demo_with_mock():
    """使用Mock LLM演示ReAct循环"""
    print("=" * 60)
    print("ReAct Agent 演示 (使用Mock LLM)")
    print("=" * 60)

    class MockLLMClient:
        """模拟LLM客户端"""

        def __init__(self, responses):
            self.responses = responses
            self.index = 0

        def generate(self, prompt: str, **kwargs) -> str:
            response = self.responses[self.index]
            self.index += 1
            return response

    # 创建一个临时测试文件
    test_file = Path(__file__).parent / "workspace" / "demo.py"
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("""
\"\"\"演示模块\"\"\"

import os
from typing import List, Dict


def calculate_sum(numbers: List[int]) -> int:
    \"\"\"计算列表中数字的总和\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total


class DataProcessor:
    \"\"\"数据处理器类\"\"\"

    def __init__(self, name: str):
        self.name = name
        self.data = []

    def add_data(self, item: Dict) -> None:
        self.data.append(item)

    def get_summary(self) -> Dict:
        return {
            "name": self.name,
            "count": len(self.data)
        }
""")

    print(f"\n创建测试文件: {test_file}")

    # 模拟多轮对话
    responses = [
        # 第一轮：分析文件
        f"""Thought: 我需要先分析这个代码文件的结构，了解有哪些函数和类
Action: analyze_code
Action Input: {{"file_path": "{test_file}"}}""",
        # 第二轮：给出最终答案
        """Thought: 我已经获得了完整的代码分析结果，可以给出详细报告了
Final Answer: 分析完成！该Python文件包含：
- 1个类: DataProcessor（有3个方法）
- 2个函数: calculate_sum, get_summary
- 代码行数: 约25行
- 导入语句: os, typing (List, Dict)
- 复杂度: 低（圈复杂度为2）"""
    ]

    # 创建Agent
    agent = ReActAgent(llm_client=MockLLMClient(responses))

    # 执行查询
    query = f"分析文件 {test_file} 的结构"
    print(f"\n用户查询: {query}\n")

    result = agent.run(query, verbose=True)

    print(f"\n{'='*60}")
    print(f"最终答案：\n{result}")
    print(f"{'='*60}")


def demo_tool_list():
    """演示所有可用工具"""
    print("\n" + "=" * 60)
    print("可用工具列表")
    print("=" * 60)

    from agents.react_agent import ToolRegistry

    registry = ToolRegistry()

    # 注册一些示例工具
    def analyze_code(file_path: str) -> dict:
        return {"file": file_path, "functions": 5, "classes": 2}

    def count_lines(file_path: str) -> dict:
        return {"total": 100, "code": 80, "comments": 20}

    registry.register("analyze_code", analyze_code, "分析Python代码文件结构")
    registry.register("count_lines", count_lines, "统计代码行数")

    print("\n已注册的工具:")
    for name in registry.list_tools():
        desc = registry.get_description(name)
        print(f"  - {name}: {desc}")


if __name__ == "__main__":
    demo_with_mock()
    demo_tool_list()
