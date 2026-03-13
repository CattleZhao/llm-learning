#!/usr/bin/env python3
"""
测试 MCP HTTP 连接

验证 HTTP 模式下的 MCP 连接是否正常工作
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.mcp.jadx_client_http import HTTPMCPClient


def test_mcp_http(server_url: str = "http://127.0.0.1:8651"):
    """测试 MCP HTTP 连接"""
    print(f"测试 MCP Server (HTTP 模式): {server_url}")
    print("=" * 60)

    # 创建客户端
    client = HTTPMCPClient(
        server_url=server_url,
        on_status_update=lambda msg: print(f"[状态] {msg}")
    )

    # 连接
    print("\n1. 连接 MCP Server...")
    if not client.connect():
        print("❌ 连接失败")
        print("\n请确保 MCP Server 已启动:")
        print("  cd /path/to/jadx-mcp-server")
        print("  uv run jadx_mcp_server.py --http --port 8651")
        return False

    # 列出工具
    print("\n2. 列出可用工具...")
    tools = client.list_tools()
    print(f"✅ 找到 {len(tools)} 个工具:")
    for tool in tools[:10]:
        print(f"   - {tool.get('name')}: {tool.get('description', 'N/A')[:60]}")

    # 测试获取 manifest（需要 JADX-GUI 已打开 APK）
    print("\n3. 测试 get_android_manifest...")
    print("   (需要 JADX-GUI 已打开 APK)")
    manifest = client.get_manifest()
    if manifest.get("package"):
        print(f"✅ 成功获取 manifest:")
        print(f"   包名: {manifest.get('package')}")
        print(f"   权限数: {len(manifest.get('permissions', []))}")
    else:
        print("⚠️  无法获取 manifest (可能需要先在 JADX-GUI 中打开 APK)")

    # 测试获取类列表
    print("\n4. 测试 get_all_classes...")
    classes = client.get_code_paths()
    if classes:
        print(f"✅ 成功获取 {len(classes)} 个类")
        print(f"   前 5 个类:")
        for cls in classes[:5]:
            print(f"   - {cls}")
    else:
        print("⚠️  无法获取类列表")

    # 测试获取字符串
    print("\n5. 测试 get_strings...")
    strings = client.get_strings()
    if strings:
        print(f"✅ 成功获取 {len(strings)} 个字符串")
        print(f"   前 5 个字符串:")
        for s in strings[:5]:
            print(f"   - {s[:50]}")
    else:
        print("⚠️  无法获取字符串")

    # 关闭连接
    print("\n6. 关闭连接...")
    client.close()
    print("✅ 测试完成")

    return True


if __name__ == "__main__":
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8651"

    success = test_mcp_http(server_url)
    sys.exit(0 if success else 1)
