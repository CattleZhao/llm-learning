#!/usr/bin/env python3
"""测试 Agent 创建（不自动连接 MCP）"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.apk_agent import create_apk_agent

print("创建 APK Agent...")
print("注意：此时不会自动连接 MCP Server")

status_messages = []

def on_status(msg):
    status_messages.append(msg)
    print(f"[状态] {msg}")

agent = create_apk_agent(
    mcp_server_path="/root/Learn/jadx-mcp-server",
    jadx_gui_path=None,  # 不自动打开
    enable_rag=False,
    enable_advanced=False,
    on_status_update=on_status
)

print(f"\nAgent 创建成功！")
print(f"MCP 已连接: {agent.mcp_client._is_connected}")

# 测试连接
print("\n测试 MCP 连接...")
result = agent.mcp_client.connect()
print(f"连接结果: {result}")

if result:
    tools = agent.mcp_client.list_tools()
    print(f"工具数量: {len(tools)}")

# 清理
agent.mcp_client.close()
print("\n完成")
