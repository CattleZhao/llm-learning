"""
LangChain Agent 演示脚本

展示 LangChain ReAct Agent 的基本使用
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.langchain_agent import LangChainCodeAgent


def demo_agent_mode():
    """演示 Agent 模式"""
    print("=" * 60)
    print("演示 1: Agent 模式")
    print("=" * 60)

    agent = LangChainCodeAgent()

    # 创建测试文件
    test_file = Path(__file__).parent / "workspace" / "demo.py"
    test_file.parent.mkdir(exist_ok=True)

    test_file.write_text('''"""演示模块"""

import os
from typing import List, Dict


def calculate_sum(numbers: List[int]) -> int:
    """计算列表中数字的总和"""
    total = 0
    for num in numbers:
        total += num
    return total


class DataProcessor:
    """数据处理器类"""

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
''')

    print(f"\n测试文件: {test_file}")
    print("\n查询: 分析这个文件的代码结构\n")

    response = agent.chat(f"分析文件 {test_file} 的代码结构")
    print(f"回复: {response}\n")


def demo_direct_mode():
    """演示直接调用模式"""
    print("=" * 60)
    print("演示 2: 直接调用模式")
    print("=" * 60)

    agent = LangChainCodeAgent()

    test_file = Path(__file__).parent / "workspace" / "demo.py"

    print("\n1. 代码分析")
    analysis = agent.analyze_code(str(test_file))
    print(f"   函数: {len(analysis.get('functions', []))} 个")
    print(f"   类: {len(analysis.get('classes', []))} 个")
    print(f"   复杂度: {analysis.get('complexity', {}).get('level', 'unknown')}")

    print("\n2. 质量评估")
    quality = agent.evaluate_quality(str(test_file))
    print(f"   分数: {quality.get('score', 0)}")
    print(f"   等级: {quality.get('level', 'unknown')}")


def demo_tools():
    """演示工具列表"""
    print("\n" + "=" * 60)
    print("演示 3: 可用工具")
    print("=" * 60)

    from tools.langchain_tools import get_all_tools

    tools = get_all_tools()
    print(f"\n共有 {len(tools)} 个工具:\n")
    for tool in tools:
        print(f"  - {tool.name}")
        print(f"    描述: {tool.description[:60]}...\n")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█  LangChain 代码助手 Agent - 演示程序".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60 + "\n")

    demo_tools()
    demo_direct_mode()
    # demo_agent_mode()  # 需要 API key

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
