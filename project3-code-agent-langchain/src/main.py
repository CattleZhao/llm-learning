"""
主入口 - LangChain 版本代码助手
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.langchain_agent import LangChainCodeAgent


def print_banner():
    """打印欢迎信息"""
    print("=" * 60)
    print("  LangChain 代码助手 Agent")
    print("  基于 LangChain ReAct Agent 实现")
    print("=" * 60)
    print()


def interactive_mode(agent: LangChainCodeAgent):
    """
    交互式对话模式

    Args:
        agent: Agent 实例
    """
    print("进入交互模式（输入 'exit' 或 'quit' 退出）")
    print()

    while True:
        try:
            user_input = input("\n👤 用户: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break

            print("\n🤖 Agent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


def single_query_mode(agent: LangChainCodeAgent, query: str):
    """
    单次查询模式

    Args:
        agent: Agent 实例
        query: 用户查询
    """
    print(f"查询: {query}\n")
    response = agent.chat(query)
    print(f"回复: {response}\n")


def direct_mode(agent: LangChainCodeAgent, file_path: str):
    """
    直接调用模式（不使用 Agent）

    Args:
        agent: Agent 实例
        file_path: 文件路径
    """
    print(f"分析文件: {file_path}\n")

    # 分析代码
    print("1. 代码结构分析")
    analysis = agent.analyze_code(file_path=file_path)
    print(f"   函数数: {len(analysis.get('functions', []))}")
    print(f"   类数: {len(analysis.get('classes', []))}")
    print(f"   总行数: {analysis.get('lines', {}).get('total', 0)}")

    # 生成测试
    print("\n2. 生成测试代码")
    test_code = agent.generate_test(file_path)
    print(f"   {test_code[:100]}...")

    # 重构建议
    print("\n3. 重构建议")
    suggestions = agent.suggest_refactor(file_path)
    print(f"   {suggestions[:100]}...")

    # 质量评估
    print("\n4. 质量评估")
    quality = agent.evaluate_quality(file_path)
    print(f"   分数: {quality.get('score', 0)}")
    print(f"   等级: {quality.get('level', '未知')}")


def main():
    """主函数"""
    print_banner()

    # 检查 API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置 OPENAI_API_KEY")
        print("请在 .env 文件中设置 OPENAI_API_KEY")
        return

    # 初始化 Agent
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "workspace")
    agent = LangChainCodeAgent(workspace_dir=workspace_dir)

    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--interactive" or command == "-i":
            interactive_mode(agent)

        elif command == "--query" or command == "-q":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                single_query_mode(agent, query)
            else:
                print("错误: --query 需要提供查询内容")

        elif command == "--analyze" or command == "-a":
            if len(sys.argv) > 2:
                direct_mode(agent, sys.argv[2])
            else:
                print("错误: --analyze 需要提供文件路径")

        else:
            # 默认为查询模式
            query = " ".join(sys.argv[1:])
            single_query_mode(agent, query)
    else:
        # 默认进入交互模式
        interactive_mode(agent)


if __name__ == "__main__":
    main()
