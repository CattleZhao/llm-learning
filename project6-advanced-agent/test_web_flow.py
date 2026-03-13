#!/usr/bin/env python3
"""测试 Web 流程"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("测试 Web 流程 - 模拟 streamlit")
print("=" * 60)

status_messages = []

def update_status(msg: str):
    status_messages.append(msg)
    print(f"[状态] {msg}")

# 模拟 web.py 中的配置
mcp_server_path = "/root/Learn/jadx-mcp-server"
jadx_gui_path = None  # 不自动打开
enable_rag = False
enable_advanced = False

print("\n[Step 1] 导入 create_apk_agent...")
from agents.apk_agent import create_apk_agent
print("  OK")

print("\n[Step 2] 创建 Agent...")
update_status("正在创建 Agent...")

start = time.time()
try:
    agent = create_apk_agent(
        mcp_server_path=mcp_server_path,
        jadx_gui_path=jadx_gui_path,
        enable_rag=enable_rag,
        enable_advanced=enable_advanced,
        on_status_update=update_status
    )
    elapsed = time.time() - start
    print(f"  OK (耗时 {elapsed:.2f}s)")
except Exception as e:
    print(f"  错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n[Step 3] 检查 Agent 状态...")
print(f"  _is_connected: {agent.mcp_client._is_connected}")
print(f"  _loop: {agent.mcp_client._loop}")

print(f"\n[Step 4] 测试 MCP 连接...")
start = time.time()
try:
    result = agent.mcp_client.connect()
    elapsed = time.time() - start
    print(f"  结果: {result} (耗时 {elapsed:.2f}s)")
    if result:
        tools = agent.mcp_client.list_tools()
        print(f"  工具数量: {len(tools)}")
except Exception as e:
    print(f"  错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print(f"测试完成！状态消息: {len(status_messages)} 条")
print("=" * 60)

# 清理
agent.mcp_client.close()
