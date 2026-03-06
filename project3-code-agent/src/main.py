"""ReAct代码助手Agent - 主入口"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.react_agent import CodeAssistantAgent


def main():
    """主函数"""
    print("=" * 60)
    print("ReAct代码助手Agent")
    print("=" * 60)
    print("\n可用功能：")
    print("- 分析Python代码结构")
    print("- 统计代码行数")
    print("- 列出函数和类")
    print("- 获取导入语句")
    print("- 计算代码复杂度")
    print("\n输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    # 创建Agent
    agent = CodeAssistantAgent(enable_memory=False)

    print("\nAgent已就绪，请输入你的问题：\n")

    while True:
        try:
            query = input("\n> ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break

            # 执行查询
            result = agent.run(query, verbose=True)

            # 打印最终答案
            print(f"\n{'='*60}")
            print(f"最终答案：\n{result}")
            print(f"{'='*60}")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
