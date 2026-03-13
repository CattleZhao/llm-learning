"""
JADX MCP 客户端模块 (使用官方 MCP SDK)

正确处理 async context manager 和会话生命周期
"""
import asyncio
import re
import time
import threading
import platform
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from urllib.parse import urlparse
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class StdioMCPClient:
    """
    MCP stdio 客户端 (使用官方 MCP SDK)
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
        self._session: Optional[ClientSession] = None
        self._server_params: Optional[StdioServerParameters] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[asyncio.Event] = None

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

    def start(self) -> bool:
        """启动 MCP Server 并创建会话"""
        self.on_status_update("启动 MCP Server...")

        try:
            self._server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else []
            )

            # 创建事件循环和停止信号
            self._stop_event = asyncio.Event()
            self._loop = asyncio.new_event_loop()

            # 启动事件循环线程
            self._loop_thread = threading.Thread(
                target=self._run_event_loop,
                daemon=True
            )
            self._loop_thread.start()
            time.sleep(0.5)

            # 在事件循环中初始化会话
            def init_session():
                async def create():
                    async with stdio_client(self._server_params) as (read_stream, write_stream):
                        self._session = ClientSession(read_stream, write_stream)
                        await self._session.initialize()
                        # 等待停止信号，保持会话活跃
                        await self._stop_event.wait()
                        # 清理
                        await self._session.close()

                asyncio.run_coroutine_threadsafe(create(), self._loop)

            init_session()
            time.sleep(3)  # 等待会话初始化

            if self._session:
                self.on_status_update("✅ MCP Server 已连接")
                return True
            else:
                self.on_status_update("❌ MCP Server 启动失败")
                return False

        except Exception as e:
            self.on_status_update(f"❌ 启动失败: {e}")
            logger.error(f"启动失败: {e}", exc_info=True)
            return False

    def _run_event_loop(self):
        """在后台线程中运行事件循环"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def connect(self) -> bool:
        """连接到 MCP Server"""
        return self.start()

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """调用 MCP 工具（同步包装）"""
        if not self._session:
            return None

        async def _call():
            result = await self._session.call_tool(tool_name, params)
            return result

        try:
            future = asyncio.run_coroutine_threadsafe(_call(), self._loop)
            return future.result(timeout=60)
        except Exception as e:
            logger.error(f"工具调用失败 {tool_name}: {e}")
            return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表（同步包装）"""
        if not self._session:
            return []

        async def _list():
            tools_result = await self._session.list_tools()
            result = []
            for tool in tools_result.tools:
                result.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            return result

        try:
            future = asyncio.run_coroutine_threadsafe(_list(), self._loop)
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"列出工具失败: {e}")
            return []

    def close(self):
        """关闭 MCP Server"""
        if self._stop_event:
            # 发送停止信号
            self._loop.call_soon_threadsafe(self._stop_event.set)
            self._stop_event = None

        if self._loop and self._loop.is_running():
            # 停止事件循环
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=3)

        self._session = None
        self._loop = None

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

        if result and isinstance(result, list) and len(result) > 0:
            result = result[0]

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
                "version_name": result.get("version_name", result.get("versionName", "")),
                "version_code": result.get("version_code", result.get("versionCode", "")),
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
        if result and isinstance(result, list) and len(result) > 0:
            result = result[0]
        if result and isinstance(result, dict):
            return result.get("classes", [])
        return []

    def get_strings(self, min_length: int = 4, offset: int = 0, count: int = 0) -> List[str]:
        """提取字符串"""
        result = self.call_tool("get_strings", {"offset": offset, "count": count})
        if result and isinstance(result, list) and len(result) > 0:
            result = result[0]
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
        if classes_result and isinstance(classes_result, list) and len(classes_result) > 0:
            classes_result = classes_result[0]

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
                if source_result and isinstance(source_result, list) and len(source_result) > 0:
                    source_result = source_result[0]

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
    is_windows = platform.system() == "Windows"

    if is_windows:
        command = [python_path, str(Path(mcp_server_dir) / "jadx_mcp_server.py")]
    else:
        command = [uv_path, "--directory", mcp_server_dir, "run", "jadx_mcp_server.py"]

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
