"""
JADX MCP 客户端模块

完整流程:
1. 启动 JADX-GUI 并打开 APK
2. 通过 MCP 协议与 JADX-GUI 通信进行代码分析
"""
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import json
import logging
import time
import re
import httpx
import threading
import platform

logger = logging.getLogger(__name__)


class JMCPClient:
    """
    JADX MCP 客户端

    完整流程:
    1. 启动 JADX-GUI 并打开 APK
    2. 通过 MCP 协议调用 JADX 进行分析
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
        mcp_server_url: str = "http://localhost:8650",
        jadx_gui_path: Optional[str] = None,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        """
        初始化 MCP 客户端

        Args:
            mcp_server_url: MCP Server HTTP 地址
            jadx_gui_path: jadx-gui 可执行文件路径
            on_status_update: 状态更新回调函数
        """
        self.server_url = mcp_server_url.rstrip("/")
        self.jadx_gui_path = jadx_gui_path or self._find_jadx_gui()
        self.on_status_update = on_status_update or (lambda msg: None)

        self._connected = False
        self._current_apk: Optional[str] = None
        self._jadx_process: Optional[subprocess.Popen] = None
        self._use_fallback = False

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

    def connect(self) -> bool:
        """连接到 MCP Server"""
        self.on_status_update("检查 MCP Server 连接...")

        try:
            response = httpx.post(
                f"{self.server_url}/ping",
                timeout=5.0
            )
            if response.status_code == 200:
                self._connected = True
                self.on_status_update("✅ 已连接到 MCP Server")
                return True
        except Exception as e:
            self.on_status_update(f"⚠️ MCP Server 不可用: {e}")

        self._use_fallback = True
        self.on_status_update("⚠️ 使用本地回退模式")
        self._connected = True
        return True

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

    def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用 MCP 工具"""
        if self._use_fallback:
            return {"success": False, "error": "fallback mode"}

        try:
            response = httpx.post(
                f"{self.server_url}/tools/{tool_name}",
                json=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"MCP 调用失败: {e}")
            return {"success": False, "error": str(e)}

    def get_manifest(self) -> Dict[str, Any]:
        """获取 AndroidManifest.xml 内容"""
        result = self._call_mcp_tool("jadx_get_manifest", {})
        return result if result.get("success") else {}

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
        result = self._call_mcp_tool("jadx_get_code_paths", {})
        return result.get("paths", []) if result.get("success") else []

    def get_strings(self, min_length: int = 4) -> List[str]:
        """提取字符串"""
        result = self._call_mcp_tool("jadx_get_strings", {"min_length": min_length})
        return result.get("strings", []) if result.get("success") else []

    def get_apis(self) -> List[Dict[str, Any]]:
        """获取 API 调用"""
        result = self._call_mcp_tool("jadx_get_apis", {})
        return result.get("apis", []) if result.get("success") else []

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

                    from urllib.parse import urlparse
                    parsed = urlparse(match)
                    if parsed.netloc and parsed.netloc not in info["domains"]:
                        info["domains"].append(parsed.netloc)

            for match in ip_pattern.findall(s):
                if match not in info["ips"]:
                    info["ips"].append(match)

        return info


# 便捷函数
def create_mcp_client(
    mcp_server_url: str = "http://localhost:3000",
    jadx_gui_path: Optional[str] = None,
    on_status_update: Optional[Callable[[str], None]] = None
) -> JMCPClient:
    """
    创建 MCP 客户端

    Args:
        mcp_server_url: MCP Server 地址
        jadx_gui_path: jadx-gui 可执行文件路径
        on_status_update: 状态更新回调

    Returns:
        JMCPClient 实例
    """
    client = JMCPClient(
        server_url=mcp_server_url,
        jadx_gui_path=jadx_gui_path,
        on_status_update=on_status_update
    )
    client.connect()
    return client
