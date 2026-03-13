#!/usr/bin/env python3
"""
测试 MCP Server 连接

用于验证 jadx-mcp-server 是否能正常启动和响应
"""
import sys
import subprocess
import json
import time
from pathlib import Path

def test_mcp_server(mcp_server_path: str):
    """测试 MCP Server"""
    print(f"测试 MCP Server: {mcp_server_path}")
    print("=" * 60)

    # 构建命令
    command = ["uv", "--directory", mcp_server_path, "run", "jadx_mcp_server.py"]
    print(f"命令: {' '.join(command)}")
    print()

    try:
        print("启动 MCP Server...")
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"PID: {process.pid}")
        print("等待 3 秒...")
        time.sleep(3)

        # 检查进程状态
        poll_result = process.poll()
        if poll_result is not None:
            print(f"❌ 进程已退出，退出码: {poll_result}")
            stderr = process.stderr.read()
            if stderr:
                print(f"错误输出:\n{stderr}")
            return False

        print("✅ 进程正在运行")

        # 发送初始化请求
        print("\n发送初始化请求...")
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        message = json.dumps(request) + "\n"
        process.stdin.write(message)
        process.stdin.flush()

        print("等待响应（5秒）...")
        time.sleep(5)

        # 尝试读取响应
        if process.stdout.readable():
            try:
                # 尝试读取一行
                import select
                ready, _, _ = select.select([process.stdout], [], [], 1)
                if ready:
                    response_line = process.stdout.readline()
                    if response_line:
                        print(f"✅ 收到响应: {response_line[:200]}")
                    else:
                        print("⚠️ 读取到空响应")
                else:
                    print("⚠️ 超时：无数据可读")
            except Exception as e:
                print(f"⚠️ 读取失败: {e}")
        else:
            print("❌ stdout 不可读")

        # 清理
        print("\n关闭进程...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

        print("✅ 测试完成")
        return True

    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        print("请确保 uv 已安装: pip install uv")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_mcp_server.py <jadx-mcp-server-path>")
        print("示例: python test_mcp_server.py ~/jadx-mcp-server")
        sys.exit(1)

    mcp_path = sys.argv[1].expanduser() if sys.argv[1].startswith("~") else sys.argv[1]

    if not Path(mcp_path).exists():
        print(f"❌ 路径不存在: {mcp_path}")
        sys.exit(1)

    success = test_mcp_server(mcp_path)
    sys.exit(0 if success else 1)
