"""
JADX MCP 客户端模块 (HTTP 方式)

通过 HTTP 与 MCP Server 通信
"""
import json
import asyncio
import re
import time
import logging
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class HTTPMCPClient:
    """
    MCP HTTP 客户端

    通过 HTTP 与 MCP Server 进行 JSON-RPC 通信
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
        server_url: str = "http://127.0.0.1:8651",
        mcp_server_path: Optional[str] = None,
        jadx_gui_path: Optional[str] = None,
        on_status_update: Optional[Callable[[str], None]] = None,
        auto_start_server: bool = True
    ):
        """
        初始化 HTTP MCP 客户端

        Args:
            server_url: MCP Server HTTP 地址 (默认: http://127.0.0.1:8651)
            mcp_server_path: jadx-mcp-server 目录路径（用于自动启动 Server）
            jadx_gui_path: jadx-gui 可执行文件路径
            on_status_update: 状态更新回调
            auto_start_server: 是否自动启动 MCP Server（默认 True）
        """
        self.server_url = server_url.rstrip("/")
        self.mcp_server_path = mcp_server_path
        self.jadx_gui_path = jadx_gui_path or self._find_jadx_gui()
        self.on_status_update = on_status_update or (lambda msg: None)
        self._request_id = 0
        self._current_apk: Optional[str] = None
        self._client: Optional[httpx.Client] = None
        self._server_process: Optional[Any] = None
        self._auto_start_server = auto_start_server

    def _find_jadx_gui(self) -> str:
        """查找 jadx-gui 可执行文件"""
        import platform
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

        return "jadx-gui.exe" if is_windows else "jadx-gui"

    def start(self) -> bool:
        """启动 MCP 客户端（HTTP 模式下验证连接，可选自动启动 Server）"""
        self.on_status_update(f"连接到 MCP Server: {self.server_url}")

        # 如果启用了自动启动，先尝试连接，失败则启动 Server
        if self._auto_start_server and self.mcp_server_path:
            if not self._try_connect():
                self.on_status_update("⚠️ MCP Server 未运行，尝试自动启动...")
                if self._start_mcp_server():
                    # 等待 Server 启动
                    import time
                    for i in range(10):  # 最多等待 10 秒
                        time.sleep(1)
                        if self._try_connect():
                            self.on_status_update("✅ MCP Server 自动启动成功")
                            return True
                    self.on_status_update("❌ MCP Server 启动超时")
                    return False
                else:
                    self.on_status_update("❌ 无法启动 MCP Server")
                    return False

        return self._try_connect()

    def _try_connect(self) -> bool:
        """尝试连接到 MCP Server"""
        try:
            self._client = httpx.Client(timeout=5.0)
            tools = self.list_tools()
            return tools is not None
        except Exception:
            if self._client:
                self._client.close()
                self._client = None
            return False

    def _start_mcp_server(self) -> bool:
        """自动启动 MCP Server"""
        import subprocess
        import platform
        import threading

        server_dir = Path(self.mcp_server_path)
        if not server_dir.exists():
            self.on_status_update(f"❌ MCP Server 路径不存在: {self.mcp_server_path}")
            return False

        server_script = server_dir / "jadx_mcp_server.py"
        if not server_script.exists():
            self.on_status_update(f"❌ 找不到 jadx_mcp_server.py: {server_script}")
            return False

        # 构建启动命令
        is_windows = platform.system() == "Windows"
        if is_windows:
            command = ["python", str(server_script), "--http", "--port", "8651"]
        else:
            command = ["uv", "--directory", str(server_dir), "run", "jadx_mcp_server.py", "--http", "--port", "8651"]

        self.on_status_update(f"启动命令: {' '.join(command)}")

        try:
            # 在后台启动进程
            if is_windows:
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            return True
        except Exception as e:
            self.on_status_update(f"❌ 启动失败: {e}")
            return False

        try:
            self._client = httpx.Client(timeout=60.0)

            # 测试连接 - 尝试列出工具
            tools = self.list_tools()
            if tools:
                self.on_status_update(f"✅ MCP Server 已连接 ({len(tools)} 个工具)")
                return True
            else:
                self.on_status_update("⚠️ MCP Server 已连接，但没有工具可用")
                return True

        except Exception as e:
            self.on_status_update(f"❌ 连接失败: {e}")
            return False

    def connect(self) -> bool:
        """连接到 MCP Server（别名）"""
        return self.start()

    def _next_id(self) -> int:
        """生成下一个请求 ID"""
        self._request_id += 1
        return self._request_id

    def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送 JSON-RPC 请求到 MCP Server"""
        if not self._client:
            raise RuntimeError("MCP Client 未连接")

        try:
            logger.debug(f"发送: {json.dumps(request)}")

            response = self._client.post(
                f"{self.server_url}/",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"接收: {json.dumps(result)}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"请求异常: {e}")
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

        response = self._send_request(request)

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

        response = self._send_request(request)

        if response and "result" in response:
            return response["result"].get("tools", [])

        return []

    def close(self):
        """关闭 MCP 客户端"""
        if self._client:
            self._client.close()
            self._client = None

        # 如果是我们启动的 Server，可以选择关闭（这里暂时不关闭，因为可能还有其他连接）
        # self._server_process = None

    # ============ JMCPClient 兼容接口 ============

    def open_apk(self, apk_path: str) -> Dict[str, Any]:
        """
        在 JADX-GUI 中打开 APK

        Args:
            apk_path: APK 文件路径

        Returns:
            打开结果
        """
        import platform
        import subprocess
        import threading

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
        """获取 AndroidManifest.xml 内容

        Returns:
            标准化格式的 manifest 信息
        """
        result = self.call_tool("get_android_manifest", {})
        if result and isinstance(result, dict):
            # 处理可能的响应格式
            content = result.get("content", "")
            if content:
                import xml.etree.ElementTree as ET
                try:
                    ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
                    root = ET.fromstring(content)

                    # 提取包名和版本
                    manifest_attrs = root.attrib
                    package_name = manifest_attrs.get("package", "")

                    # 提取权限
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

            # 如果解析失败或没有 content，使用原始返回值
            return {
                "package": result.get("package", ""),
                "version_name": result.get("version_name", result.get("versionName", "")),
                "version_code": result.get("version_code", result.get("versionCode", "")),
                "permissions": result.get("permissions", []),
                "permissions_dangerous": result.get("permissions_dangerous", []),
                "min_sdk": result.get("min_sdk", result.get("minSdkVersion", "")),
                "target_sdk": result.get("target_sdk", result.get("targetSdkVersion", "")),
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
        """提取字符串

        Args:
            min_length: 最小字符串长度（保留用于向后兼容）
            offset: 分页偏移量
            count: 返回数量（0表示全部）

        Returns:
            字符串列表
        """
        result = self.call_tool("get_strings", {"offset": offset, "count": count})
        if result and isinstance(result, dict):
            strings_data = result.get("strings", [])
            if isinstance(strings_data, list):
                return strings_data
            elif isinstance(strings_data, dict):
                return strings_data.get("strings", [])
        return []

    def get_apis(self, max_classes: int = 50) -> List[Dict[str, Any]]:
        """获取 API 调用

        注意: MCP Server 没有直接的 get_apis 工具，
        我们通过获取类源码并分析来提取 API 调用

        Args:
            max_classes: 最多分析的类数量

        Returns:
            API 调用列表，每个元素包含 {"class": str, "method": str, "api": str}
        """
        apis = []

        # 获取所有类
        classes_result = self.call_tool("get_all_classes", {"count": max_classes})
        if not classes_result or not isinstance(classes_result, dict):
            return apis

        classes = classes_result.get("classes", [])
        if not classes:
            return apis

        # 分析每个类提取 API 调用
        api_patterns = [
            r'(getDeviceId|getSubscriberId|getLine1Number|sendTextMessage|requestLocationUpdates)',
            r'(TelephonyManager|SmsManager|LocationManager|ConnectivityManager)',
            r'\.(findViewById|getSystemService|startActivity|startService)',
        ]

        for class_name in classes[:max_classes]:
            try:
                # 获取类源码
                source_result = self.call_tool("get_class_source", {"class_name": class_name})
                if source_result and isinstance(source_result, dict):
                    source_code = source_result.get("source", "")
                    if source_code:
                        # 分析源码提取 API 调用
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
        """分析网络通信信息

        Returns:
            网络通信分析结果，包含 URL、IP、域名等
        """
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

        # 获取字符串资源
        strings = self.get_strings()

        for s in strings:
            # 查找 URL
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

            # 查找 IP 地址
            for match in ip_pattern.findall(s):
                if match not in info["ips"]:
                    info["ips"].append(match)

        return info


# 使用示例
def create_http_client(
    server_url: str = "http://127.0.0.1:8651",
    mcp_server_path: str = None,
    jadx_gui_path: str = None,
    auto_start_server: bool = True
) -> HTTPMCPClient:
    """
    创建 HTTP MCP 客户端

    Args:
        server_url: MCP Server HTTP 地址
        mcp_server_path: jadx-mcp-server 目录（用于自动启动 Server）
        jadx_gui_path: jadx-gui 可执行文件路径
        auto_start_server: 是否自动启动 MCP Server（默认 True）

    Returns:
        HTTPMCPClient 实例
    """
    client = HTTPMCPClient(
        server_url=server_url,
        mcp_server_path=mcp_server_path,
        jadx_gui_path=jadx_gui_path,
        auto_start_server=auto_start_server
    )
    client.start()
    return client


# 测试代码
if __name__ == "__main__":
    import sys

    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8651"

    client = create_http_client(
        server_url=server_url,
        on_status_update=lambda msg: print(f"[状态] {msg}")
    )

    # 列出可用工具
    tools = client.list_tools()
    print(f"\n可用工具: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.get('name')}: {tool.get('description', 'N/A')[:60]}")

    client.close()
