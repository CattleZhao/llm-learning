#!/usr/bin/env python3
"""
测试完整工作流程

模拟 web.py 中的使用场景
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.apk_agent import create_apk_agent


def test_workflow():
    """测试工作流程"""
    print("=" * 50)
    print("测试 APK 分析工作流程")
    print("=" * 50)

    # 状态更新回调
    status_messages = []

    def on_status(msg: str):
        status_messages.append(msg)
        print(f"[状态] {msg}")

    # 配置路径
    mcp_server_path = "/root/Learn/jadx-mcp-server"
    # jadx_gui_path = None  # 不自动打开，假设已手动打开

    print(f"\n1. 创建 Agent...")
    print(f"   MCP Server 路径: {mcp_server_path}")

    try:
        agent = create_apk_agent(
            mcp_server_path=mcp_server_path,
            jadx_gui_path=None,  # 不自动打开
            enable_rag=False,
            enable_advanced=False,
            on_status_update=on_status
        )
        print("   ✅ Agent 创建成功（注意：此时未连接 MCP）")

    except Exception as e:
        print(f"   ❌ Agent 创建失败: {e}")
        return

    # 检查 MCP 客户端状态
    print(f"\n2. 检查 MCP 客户端状态...")
    print(f"   _is_connected: {agent.mcp_client._is_connected}")
    print(f"   _loop: {agent.mcp_client._loop}")

    # 测试连接（不会自动打开 JADX-GUI）
    print(f"\n3. 测试 MCP 连接...")
    print(f"   注意：如果 JADX-GUI 没有打开 APK，连接可能失败")

    connected = agent.mcp_client.connect()
    print(f"   连接结果: {connected}")

    if connected:
        print(f"\n4. 尝试获取工具列表...")
        tools = agent.mcp_client.list_tools()
        print(f"   工具数量: {len(tools)}")
        if tools:
            print(f"   前5个工具:")
            for tool in tools[:5]:
                print(f"     - {tool.get('name')}")

    # 清理
    print(f"\n5. 清理资源...")
    agent.mcp_client.close()
    print("   ✅ 已关闭")

    print(f"\n" + "=" * 50)
    print(f"测试完成！")
    print(f"状态消息数量: {len(status_messages)}")
    print(f"=" * 50)


if __name__ == "__main__":
    test_workflow()
