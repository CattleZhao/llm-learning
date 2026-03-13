"""
JADX MCP 客户端模块 (使用统一事件循环)

直接与 MCP Server 进行 JSON-RPC 通信
"""
import asyncio
import json
import re
import time
import threading
import platform
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class StdioMCPClient:
    """
    MCP stdio 客户端 (直接实现，使用统一事件循环)
    """

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
        self.server_command = server_command
        self.jadx_gui_path = jadx_gui_path or self._find_jadx_gui()
        self.on_status_update = on_status_update or (lambda msg: None)
        self._current_apk: Optional[str] = None
        self._request_id = 0
        self._process: Optional[asyncio.subprocess.Process] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._is_connected = False
        self._connection_lock = threading.Lock()

    def _find_jadx_gui(self) -> str:
        """查找 jadx-gui 可执行文件"""
        is_windows = platform.system() == "Windows"

        if is_windows:
            common_paths = [
                "~/jadx/jadx-gui.exe",
                "C:/jadx/jadx-gui.exe",
                "C:/Program Files/JADX/bin/jadx-gui.exe",
            ]
        else:
            common_paths = [
                "~/jadx/jadx-gui",
                "/opt/jadx/bin/jadx-gui",
                "/usr/local/bin/jadx-gui",
            ]

        for path in common_paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                return str(expanded)

        return "jadx-gui.exe" if is_windows else "jadx-gui"

    def _run_event_loop(self):
        """在后台线程中运行事件循环"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _start_server(self):
        """启动 MCP Server 进程"""
        self._process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL  # 忽略 stderr，避免缓冲区阻塞
        )
        # 等待服务器启动
        await asyncio.sleep(2)  # 减少等待时间

    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送 JSON-RPC 请求并读取响应"""
        if not self._process or not self._process.stdin:
            raise RuntimeError("MCP Server 未运行")

        message = json.dumps(request)
        self._process.stdin.write(message.encode() + b'\n')
        await self._process.stdin.drain()

        # 读取响应
        response_line = await asyncio.wait_for(
            self._process.stdout.readline(),
            timeout=30.0
        )
        response = json.loads(response_line.decode())

        if "error" in response:
            logger.error(f"请求错误: {response['error']}")
            raise Exception(response["error"])

        return response.get("result", response)

    async def _initialize(self):
        """初始化 MCP 会话"""
        init_request = {
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
        }
        await self._send_request(init_request)

    def start(self) -> bool:
        """启动 MCP 客户端"""
        with self._connection_lock:
            if self._is_connected:
                return True

            self.on_status_update("启动 MCP Server...")

            # 先清理可能存在的旧进程
            self._cleanup_old_processes()

            try:
                # 创建事件循环线程
                self._loop = asyncio.new_event_loop()
                self._loop_thread = threading.Thread(
                    target=self._run_event_loop,
                    daemon=True
                )
                self._loop_thread.start()
                time.sleep(0.5)

                # 在事件循环中启动服务器和初始化
                def init():
                    async def _init():
                        await self._start_server()
                        await self._initialize()

                    asyncio.run_coroutine_threadsafe(_init(), self._loop)

                init()
                time.sleep(5)  # 等待初始化完成

                # 验证连接
                tools = self.list_tools()
                if tools and len(tools) > 0:
                    self.on_status_update(f"✅ MCP Server 已连接 ({len(tools)} 个工具)")
                    self._is_connected = True
                    return True
                else:
                    # 工具为空不代表失败，可能只是 JADX 插件还没加载项目
                    self.on_status_update("⚠️ MCP Server 已启动，等待 JADX 加载项目...")
                    self._is_connected = True
                    return True
            except Exception as e:
                self.on_status_update(f"❌ 启动失败: {e}")
                logger.error(f"启动失败: {e}", exc_info=True)
                self._is_connected = False
                return False

    def _cleanup_old_processes(self):
        """清理可能存在的旧 MCP Server 进程"""
        try:
            import subprocess
            import platform

            # 查找可能的旧进程（更精确的匹配）
            if platform.system() == "Windows":
                # Windows: 使用 wmic 查找 python.exe 运行 jadx_mcp_server.py 的进程
                try:
                    result = subprocess.run(
                        ['wmic', 'process', 'where', "commandline like '%jadx_mcp_server.py%'"],
                        capture_output=True,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if 'CommandLine' in line and 'jadx_mcp_server.py' in line:
                                # 提取 PID
                                parts = line.split('=')
                                if len(parts) > 1:
                                    pid = parts[1].strip()
                                    try:
                                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                                      capture_output=True, stderr=subprocess.DEVNULL)
                                    except:
                                        pass
                except:
                    pass
            else:
                # Unix/Linux: 使用 pkill 匹配
                subprocess.run(
                    ['pkill', '-f', 'jadx_mcp_server.py'],
                    capture_output=True
                )
        except Exception as e:
            logger.debug(f"清理旧进程时出错: {e}")
            pass

    def connect(self) -> bool:
        """连接到 MCP Server（幂等操作）"""
        with self._connection_lock:
            if self._is_connected:
                return True
            return self.start()

    async def _call_tool_async(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """异步调用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        return await self._send_request(request)

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """调用 MCP 工具（同步包装）"""
        if not self._loop:
            # 尝试自动重连
            if not self._is_connected:
                self.on_status_update("⚠️ MCP 未连接，尝试重新连接...")
                if not self.start():
                    logger.error("无法连接到 MCP Server")
                    return None

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._call_tool_async(tool_name, params),
                self._loop
            )
            return future.result(timeout=60)
        except Exception as e:
            logger.error(f"工具调用失败 {tool_name}: {e}")
            # 如果是连接相关错误，标记为未连接
            if "Server 未运行" in str(e) or "Future" in str(e):
                self._is_connected = False
            return None

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        """异步获取工具列表"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        }
        result = await self._send_request(request)

        # 提取工具信息
        tools = []
        for tool in result.get("tools", []):
            tools.append({
                "name": tool.get("name"),
                "description": tool.get("description"),
                "inputSchema": tool.get("inputSchema", {})
            })
        return tools

    def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表（同步包装）"""
        if not self._loop:
            return []

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._list_tools_async(),
                self._loop
            )
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"列出工具失败: {e}")
            return []

    def close(self):
        """关闭 MCP Server"""
        with self._connection_lock:
            self._is_connected = False

            # 终止 MCP Server 进程
            if self._process:
                try:
                    self._process.terminate()
                    # 等待进程结束
                    asyncio.run_coroutine_threadsafe(
                        self._process.wait(),
                        self._loop
                    )
                except:
                    try:
                        self._process.kill()
                    except:
                        pass
                self._process = None

            # 停止事件循环
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)

            if self._loop_thread and self._loop_thread.is_alive():
                self._loop_thread.join(timeout=2)

            self._loop = None

    def _next_id(self) -> int:
        """生成下一个请求 ID"""
        self._request_id += 1
        return self._request_id

    # ============ JMCPClient 兼容接口 ============

    def open_apk(self, apk_path: str) -> Dict[str, Any]:
        """在 JADX-GUI 中打开 APK"""
        import subprocess

        apk_file = Path(apk_path)
        if not apk_file.exists():
            raise FileNotFoundError(f"APK 文件不存在: {apk_path}")

        self._current_apk = str(apk_file)
        self.on_status_update(f"🚀 在 JADX-GUI 中打开: {apk_file.name}")

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
            return {"success": True, "apk_path": apk_path}

        except Exception as e:
            self.on_status_update(f"⚠️ 启动失败: {e}")
            return {"success": False, "error": str(e)}

    def get_manifest(self) -> Dict[str, Any]:
        """获取 AndroidManifest.xml 内容"""
        result = self.call_tool("get_android_manifest", {})

        if result and isinstance(result, dict):
            content = result.get("content", "")
            if content:
                import xml.etree.ElementTree as ET
                try:
                    ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
                    root = ET.fromstring(content)
                    manifest_attrs = root.attrib
                    package_name = manifest_attrs.get("package", "")

                    permissions = []
                    dangerous_permissions = []
                    for perm in root.findall(".//uses-permission"):
                        perm_name = perm.attrib.get(
                            "{http://schemas.android.com/apk/res/android}name",
                            perm.attrib.get("name", "")
                        )
                        if perm_name:
                            permissions.append(perm_name)
                            if perm_name in self.DANGEROUS_PERMISSIONS:
                                dangerous_permissions.append(perm_name)

                    return {
                        "package": package_name,
                        "version_name": manifest_attrs.get(
                            "{http://schemas.android.com/apk/res/android}versionName", ""
                        ),
                        "version_code": manifest_attrs.get(
                            "{http://schemas.android.com/apk/res/android}versionCode", ""
                        ),
                        "permissions": permissions,
                        "permissions_dangerous": dangerous_permissions,
                        "raw_xml": content,
                        "raw": result
                    }
                except ET.ParseError:
                    pass

            return {
                "package": result.get("package", ""),
                "version_name": result.get("version_name", ""),
                "version_code": result.get("version_code", ""),
                "permissions": result.get("permissions", []),
                "permissions_dangerous": result.get("permissions_dangerous", []),
                "raw": result
            }
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
        result = self.call_tool("get_all_classes", {})
        if result and isinstance(result, dict):
            return result.get("classes", [])
        return []

    def get_strings(self, min_length: int = 4, offset: int = 0, count: int = 0) -> List[str]:
        """提取字符串"""
        result = self.call_tool("get_strings", {"offset": offset, "count": count})
        if result and isinstance(result, dict):
            strings_data = result.get("strings", [])
            if isinstance(strings_data, list):
                return strings_data
            elif isinstance(strings_data, dict):
                return strings_data.get("strings", [])
        return []

    def get_apis(self, max_classes: int = 50) -> List[Dict[str, Any]]:
        """获取 API 调用"""
        apis = []
        classes_result = self.call_tool("get_all_classes", {"count": max_classes})

        if not classes_result or not isinstance(classes_result, dict):
            return apis

        classes = classes_result.get("classes", [])
        if not classes:
            return apis

        api_patterns = [
            r'(getDeviceId|getSubscriberId|getLine1Number|sendTextMessage|requestLocationUpdates)',
            r'(TelephonyManager|SmsManager|LocationManager|ConnectivityManager)',
            r'\.(findViewById|getSystemService|startActivity|startService)',
        ]

        for class_name in classes[:max_classes]:
            try:
                source_result = self.call_tool("get_class_source", {"class_name": class_name})
                if source_result and isinstance(source_result, dict):
                    source_code = source_result.get("source", "")
                    if source_code:
                        for pattern in api_patterns:
                            matches = re.finditer(pattern, source_code)
                            for match in matches:
                                apis.append({
                                    "class": class_name,
                                    "method": match.group(0),
                                    "api": match.group(0)
                                })
            except Exception as e:
                logger.debug(f"分析类 {class_name} 失败: {e}")
                continue

        return apis

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


def create_stdio_client(
    mcp_server_dir: str,
    python_path: str = "python3"
) -> StdioMCPClient:
    """
    创建 stdio MCP 客户端

    Args:
        mcp_server_dir: jadx-mcp-server 目录
        python_path: Python 可执行文件路径

    Returns:
        StdioMCPClient 实例
    """
    command = [python_path, str(Path(mcp_server_dir) / "jadx_mcp_server.py")]

    client = StdioMCPClient(server_command=command)
    client.start()
    return client


# 测试代码
if __name__ == "__main__":
    import sys

    mcp_server_path = sys.argv[1] if len(sys.argv) > 1 else "/path/to/jadx-mcp-server"

    client = create_stdio_client(
        mcp_server_dir=mcp_server_path,
        on_status_update=lambda msg: print(f"[状态] {msg}")
    )

    tools = client.list_tools()
    print(f"\n可用工具: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.get('name')}: {tool.get('description', 'N/A')[:60]}")

    client.close()
