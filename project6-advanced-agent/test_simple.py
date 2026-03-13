#!/usr/bin/env python3
"""简单测试 MCP 客户端"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.mcp.jadx_client_stdio import StdioMCPClient

print("创建 MCP 客户端...")
client = StdioMCPClient(
    server_command=['python3', '/root/Learn/jadx-mcp-server/jadx_mcp_server.py'],
    on_status_update=lambda msg: print(f"[状态] {msg}")
)

print("启动 MCP Server...")
result = client.start()
print(f"启动结果: {result}")

if result:
    tools = client.list_tools()
    print(f"工具数量: {len(tools)}")

client.close()
print("完成")
