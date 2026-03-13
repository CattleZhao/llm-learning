"""
JADX MCP 客户端模块 (stdio 方式)

通过 stdio 与 MCP Server 通信，这是 MCP 协议的标准方式
"""
import subprocess
import json
import uuid
import asyncio
import re
import time
import threading
import platform
import select
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class StdioMCPClient:
    """
    MCP stdio 客户端

    通过 stdin/stdout 与 MCP Server 进行 JSON-RPC 通信
    """

    # 危险权限列表
    DANGEROUS_PERMISSIONS = {
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_PHONE_STATE",
        "android.permission.CALL_PHONE",
        "android.permission.READ_CALL_LOG",
        "android.permission.READ_CONTACTS",
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.GET_ACCOUNTS",
        "android.permission.READ_CALENDAR",
    }

    def __init__(
        self,
        server_command: List[str],
        jadx_gui_path: Optional[str] = None,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        """
        初始化 stdio MCP 客户端

        Args:
            server_command: 启动 MCP Server 的命令，如 ["uv", "run", "jadx_mcp_server.py"]
            jadx_gui_path: jadx-gui 可执行文件路径
            on_status_update: 状态更新回调
        """
        self.server_command = server_command
        self.jadx_gui_path = jadx_gui_path or self._find_jadx_gui()
        self.on_status_update = on_status_update or (lambda msg: None)
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._current_apk: Optional[str] = None

    def _find_jadx_gui(self) -> str:
        """查找 jadx-gui 可执行文件"""
        is_windows = platform.system() == "Windows"

        if is_windows:
            candidates = ["jadx-gui.exe", "jadx-gui.bat"]
            common_paths = [
                "~/jadx/jadx-gui.exe",
                "C:/jadx/jadx-gui.exe",
                "C:/Program Files/JADX/bin/jadx-gui.exe",
            ]
        else:
            candidates = ["jadx-gui", "jadx"]
            common_paths = [
                "~/jadx/jadx-gui",
                "/opt/jadx/bin/jadx-gui",
                "/usr/local/bin/jadx-gui",
            ]

        # 检查常见路径
        for path in common_paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                return str(expanded)

        # 使用 where/which 查找
        for name in candidates:
            try:
                cmd = ["where", name] if is_windows else ["which", name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.strip().split("\n")[0].strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        return "jadx-gui.exe" if is_windows else "jadx-gui"

    def start(self) -> bool:
        """启动 MCP Server 进程"""
        self.on_status_update("启动 MCP Server...")

        try:
            # Windows 上使用 CREATE_NO_WINDOW 避免弹出窗口
            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                startupinfo=startupinfo
            )

            # 等待一小段时间让进程启动
            time.sleep(2)

            # 检查进程是否仍在运行
            if self.process.poll() is not None:
                # 进程已退出，读取错误信息
                stderr_output = self.process.stderr.read() if self.process.stderr else ""
                self.on_status_update(f"❌ MCP Server 启动失败: {stderr_output[:200]}")
                return False

            # 发送初始化请求
            self._send_request({
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "apk-analysis-agent",
                        "version": "1.0.0"
                    }
                }
            })

            # 等待响应（带超时）
            response = self._read_response(timeout=10)
            if response and response.get("result"):
                self.on_status_update("✅ MCP Server 已连接")
                return True

            # 没有收到有效响应
            self.on_status_update("⚠️ MCP Server 无响应，可能使用非 stdio 模式")
            # 不关闭进程，继续尝试
            return True

        except Exception as e:
            self.on_status_update(f"❌ 启动失败: {e}")
            return False

    def connect(self) -> bool:
        """连接到 MCP Server（别名，兼容 JMCPClient 接口）"""
        return self.start()

    def _next_id(self) -> int:
        """生成下一个请求 ID"""
        self._request_id += 1
        return self._request_id

    def _send_request(self, request: Dict[str, Any]) -> None:
        """发送 JSON-RPC 请求到 MCP Server"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP Server 未运行")

        message = json.dumps(request)
        logger.debug(f"发送: {message}")
        self.process.stdin.write(message + "\n")
        self.process.stdin.flush()

    def _read_response(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """从 MCP Server 读取响应（带超时）"""
        if not self.process or not self.process.stdout:
            return None

        try:
            # 使用 select 实现超时（仅 Unix）
            if hasattr(select, 'select'):
                ready, _, _ = select.select([self.process.stdout], [], [], timeout)
                if not ready:
                    logger.warning(f"读取响应超时 ({timeout}s)")
                    return None

            line = self.process.stdout.readline()
            if not line:
                return None

            response = json.loads(line.strip())
            logger.debug(f"接收: {response}")
            return response

        except json.JSONDecodeError as e:
            logger.error(f"解析响应失败: {e}")
            return None
        except Exception as e:
            logger.error(f"读取响应异常: {e}")
            return None

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        调用 MCP 工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }

        self._send_request(request)
        response = self._read_response()

        if response:
            if "result" in response:
                return response["result"]
            elif "error" in response:
                logger.error(f"工具调用失败: {response['error']}")
                return None

        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        }

        self._send_request(request)
        response = self._read_response()

        if response and "result" in response:
            return response["result"].get("tools", [])

        return []

    def close(self):
        """关闭 MCP Server"""
        if self.process:
            try:
                # 发送关闭请求
                self._send_request({
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "shutdown"
                })

                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None

    # ============ JMCPClient 兼容接口 ============

    def open_apk(self, apk_path: str) -> Dict[str, Any]:
        """
        在 JADX-GUI 中打开 APK

        Args:
            apk_path: APK 文件路径

        Returns:
            打开结果
        """
        apk_file = Path(apk_path)
        if not apk_file.exists():
            raise FileNotFoundError(f"APK 文件不存在: {apk_path}")

        self._current_apk = str(apk_file)
        self.on_status_update(f"🚀 在 JADX-GUI 中打开: {apk_file.name}")

        # 启动 jadx-gui 并打开 APK
        is_windows = platform.system() == "Windows"
        cmd = [self.jadx_gui_path, str(apk_file)]

        try:
            def launch_gui():
                try:
                    if is_windows:
                        subprocess.Popen(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                        )
                    else:
                        subprocess.Popen(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                except Exception as e:
                    logger.error(f"启动 JADX-GUI 失败: {e}")

            thread = threading.Thread(target=launch_gui, daemon=True)
            thread.start()

            time.sleep(3)

            self.on_status_update("✅ JADX-GUI 已启动并打开 APK")

            return {
                "success": True,
                "apk_path": apk_path,
                "method": "jadx-gui",
                "command": " ".join(cmd)
            }

        except Exception as e:
            self.on_status_update(f"⚠️ 启动失败: {e}")
            return {"success": False, "error": str(e)}

    def get_manifest(self) -> Dict[str, Any]:
        """获取 AndroidManifest.xml 内容"""
        result = self.call_tool("jadx_get_manifest", {})
        if result and isinstance(result, dict):
            return result
        return {}

    def get_permissions(self) -> Dict[str, Any]:
        """获取权限列表"""
        manifest = self.get_manifest()
        return {
            "all": manifest.get("permissions", []),
            "dangerous": manifest.get("permissions_dangerous", []),
            "count": len(manifest.get("permissions", [])),
            "dangerous_count": len(manifest.get("permissions_dangerous", []))
        }

    def get_code_paths(self) -> List[str]:
        """获取代码文件路径"""
        result = self.call_tool("jadx_get_code_paths", {})
        if result and isinstance(result, dict):
            return result.get("paths", [])
        return []

    def get_strings(self, min_length: int = 4) -> List[str]:
        """提取字符串"""
        result = self.call_tool("jadx_get_strings", {"min_length": min_length})
        if result and isinstance(result, dict):
            return result.get("strings", [])
        return []

    def get_apis(self) -> List[Dict[str, Any]]:
        """获取 API 调用"""
        result = self.call_tool("jadx_get_apis", {})
        if result and isinstance(result, dict):
            return result.get("apis", [])
        return []

    def get_network_info(self) -> Dict[str, Any]:
        """分析网络通信信息"""
        info = {
            "urls": [],
            "ips": [],
            "domains": [],
            "has_encryption": False,
            "has_http": False,
            "has_https": False
        }

        url_pattern = re.compile(r'(https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)')
        ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')

        strings = self.get_strings()

        for s in strings:
            for match in url_pattern.findall(s):
                if match not in info["urls"]:
                    info["urls"].append(match)
                    if match.startswith("https://"):
                        info["has_https"] = True
                        info["has_encryption"] = True
                    elif match.startswith("http://"):
                        info["has_http"] = True

                    parsed = urlparse(match)
                    if parsed.netloc and parsed.netloc not in info["domains"]:
                        info["domains"].append(parsed.netloc)

            for match in ip_pattern.findall(s):
                if match not in info["ips"]:
                    info["ips"].append(match)

        return info


# 使用示例
def create_stdio_client(
    mcp_server_dir: str,
    uv_path: str = "uv",
    python_path: str = "python"
) -> StdioMCPClient:
    """
    创建 stdio MCP 客户端

    Args:
        mcp_server_dir: jadx-mcp-server 目录
        uv_path: uv 可执行文件路径
        python_path: Python 可执行文件路径（Windows 备用）

    Returns:
        StdioMCPClient 实例
    """
    import sys

    # Windows 上优先使用 Python 直接运行
    if platform.system() == "Windows":
        command = [
            python_path,
            str(Path(mcp_server_dir) / "jadx_mcp_server.py")
        ]
    else:
        command = [
            uv_path,
            "--directory",
            mcp_server_dir,
            "run",
            "jadx_mcp_server.py"
        ]

    client = StdioMCPClient(server_command=command)
    client.start()
    return client


# 测试代码
if __name__ == "__main__":
    import sys

    # 使用示例
    mcp_server_path = sys.argv[1] if len(sys.argv) > 1 else "/path/to/jadx-mcp-server"

    client = create_stdio_client(
        mcp_server_dir=mcp_server_path,
        on_status_update=lambda msg: print(f"[状态] {msg}")
    )

    # 列出可用工具
    tools = client.list_tools()
    print(f"\n可用工具: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.get('name')}: {tool.get('description', 'N/A')}")

    client.close()
