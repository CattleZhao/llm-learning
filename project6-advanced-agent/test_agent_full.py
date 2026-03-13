#!/usr/bin/env python3
"""测试 Agent 完整流程"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.apk_agent import create_apk_agent

def test():
    print("=" * 60)
    print("测试 Agent 完整流程")
    print("=" * 60)

    status_messages = []

    def on_status(msg):
        status_messages.append(msg)
        print(f"[状态] {msg}")

    print("\n[1] 创建 Agent...")
    agent = create_apk_agent(
        mcp_server_path="/root/Learn/jadx-mcp-server",
        jadx_gui_path=None,
        enable_rag=False,
        enable_advanced=False,
        on_status_update=on_status
    )
    print(f"     Agent 创建完成")
    print(f"     _is_connected: {agent.mcp_client._is_connected}")

    print("\n[2] 连接 MCP...")
    result = agent.mcp_client.connect()
    print(f"     连接结果: {result}")

    if result:
        print("\n[3] 列出工具...")
        tools = agent.mcp_client.list_tools()
        print(f"     工具数量: {len(tools)}")

    print("\n[4] 关闭连接...")
    agent.mcp_client.close()
    print("     完成")

    print("\n" + "=" * 60)
    print(f"状态消息总数: {len(status_messages)}")
    print("=" * 60)

if __name__ == "__main__":
    test()
