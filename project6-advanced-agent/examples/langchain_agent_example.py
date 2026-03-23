"""
LangChain Agent 使用示例

展示如何在代码中使用 LangChain Agent 进行 APK 分析
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.langchain_agent import create_langchain_agent


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)

    # 1. 创建 Agent
    agent = create_langchain_agent(
        mcp_server_path="/path/to/jadx-mcp-server",  # 修改为你的 MCP Server 路径
        model="claude-sonnet-4-20250514"
    )

    # 2. 执行分析
    apk_path = "/path/to/your/app.apk"  # 修改为你的 APK 路径

    response = agent.think(
        f"请分析 APK 文件: {apk_path}",
        context={"apk_path": apk_path}
    )

    # 3. 获取结果
    print("\n分析报告:")
    print(response.content)

    print("\n元数据:")
    print(f"- 风险等级: {response.metadata.get('risk_level')}")
    print(f"- 工具调用次数: {response.metadata.get('tool_calls_count')}")

    # 4. 关闭连接
    agent.close()


def example_with_status_callback():
    """带状态更新的示例"""
    print("\n" + "=" * 60)
    print("示例 2: 带状态更新")
    print("=" * 60)

    # 定义状态更新回调
    def on_status(message: str):
        print(f"[状态] {message}")

    # 创建 Agent（带状态回调）
    agent = create_langchain_agent(
        mcp_server_path="/path/to/jadx-mcp-server",
        on_status_update=on_status
    )

    # 执行分析
    response = agent.think(
        "分析 app.apk",
        context={"apk_path": "/path/to/app.apk"}
    )

    print(f"\n分析完成，风险等级: {response.metadata.get('risk_level')}")
    agent.close()


def example_in_web_ui():
    """在 Web UI 中使用的示例"""
    print("\n" + "=" * 60)
    print("示例 3: Web UI 集成")
    print("=" * 60)

    # Streamlit Web UI 中的使用方式
    code_example = '''
# app/web.py

from agents.langchain_agent import create_langchain_agent

# 在用户选择 "LangChain Agent" 时
if agent_type == "LangChain Agent":
    agent = create_langchain_agent(
        mcp_server_path=mcp_server_path,
        on_status_update=lambda msg: st.session_state.analysis_status.append(msg)
    )

    response = agent.think(
        f"分析 APK: {apk_path}",
        context={"apk_path": apk_path}
    )

    # 显示结果
    st.markdown(response.content)
    st.info(f"风险等级: {response.metadata.get('risk_level')}")
'''

    print(code_example)


def example_comparison():
    """三种 Agent 对比"""
    print("\n" + "=" * 60)
    print("三种 Agent 对比")
    print("=" * 60)

    comparison = """
┌─────────────────┬──────────────┬──────────────┬──────────────────┐
│ 特性            │ 硬编码流程   │ LLM 驱动     │ LangChain       │
├─────────────────┼──────────────┼──────────────┼──────────────────┤
│ 导入            │ create_apk   │ create_llm   │ create_langchain│
│ 工具选择        │ 固定 9 步   │ LLM 自主选择 │ LLM 自主选择    │
│ 迭代管理        │ 无需         │ 手动 while    │ 自动管理        │
│ 停止判断        │ 完成即停止   │ 需判断       │ 自动判断        │
│ 适用场景        │ 标准化分析  │ 灵活分析     │ 复杂编排        │
└─────────────────┴──────────────┴──────────────┴──────────────────┘

使用建议:
- 硬编码流程: 日常快速分析，结果稳定
- LLM 驱动:   需要灵活决策的场景
- LangChain:  复杂多步任务，需要优化提示词
"""

    print(comparison)


if __name__ == "__main__":
    print("📚 LangChain Agent 使用示例\n")

    # 显示对比
    example_comparison()

    print("\n" + "=" * 60)
    print("💡 快速开始")
    print("=" * 60)
    print("""
1. 修改路径:
   - mcp_server_path: 指向你的 jadx-mcp-server 目录
   - apk_path: 指向你要分析的 APK 文件

2. 基本调用:
   from agents.langchain_agent import create_langchain_agent

   agent = create_langchain_agent(mcp_server_path="...")
   response = agent.think("分析 app.apk", context={"apk_path": "..."})
   print(response.content)

3. 运行此文件前确保:
   - JADX MCP Server 已启动
   - ANTHROPIC_API_KEY 环境变量已设置
""")

    # 如果参数正确，可以取消注释运行实际示例
    # example_basic_usage()
    # example_with_status_callback()
