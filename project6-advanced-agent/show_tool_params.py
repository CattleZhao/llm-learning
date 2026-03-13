#!/usr/bin/env python3
"""
查看 MCP 工具参数定义

显示 MCP Server 提供的所有工具及其参数
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.mcp.jadx_client_stdio import StdioMCPClient


def show_tool_params(mcp_server_path: str = "/root/Learn/jadx-mcp-server"):
    """显示所有工具的参数定义"""
    print(f"连接到 MCP Server: {mcp_server_path}")
    print("=" * 60)

    import platform
    if platform.system() == "Windows":
        command = ["python", str(Path(mcp_server_path) / "jadx_mcp_server.py")]
    else:
        command = ["uv", "--directory", mcp_server_path, "run", "jadx_mcp_server.py"]

    client = StdioMCPClient(
        server_command=command,
        on_status_update=lambda msg: print(f"[状态] {msg}")
    )
    client.connect()

    # 获取所有工具
    tools = client.list_tools()
    print(f"\n找到 {len(tools)} 个工具\n")

    for tool in tools:
        name = tool.get("name", "unknown")
        description = tool.get("description", "无描述")
        input_schema = tool.get("inputSchema", {})

        print(f"🔧 {name}")
        print(f"   描述: {description}")

        # 解析参数
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        if properties:
            print(f"   参数:")
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "unknown")
                param_desc = param_info.get("description", "")
                is_required = "必需" if param_name in required else "可选"

                print(f"      - {param_name} ({param_type}, {is_required})")
                if param_desc:
                    print(f"        {param_desc}")
        else:
            print(f"   参数: 无")

        print()

    client.close()


if __name__ == "__main__":
    mcp_path = sys.argv[1] if len(sys.argv) > 1 else "/root/Learn/jadx-mcp-server"
    show_tool_params(mcp_path)
