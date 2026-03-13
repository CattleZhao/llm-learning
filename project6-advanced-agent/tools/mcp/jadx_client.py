"""
JADX MCP 客户端模块

用于连接 JADX MCP Server 进行 APK 反编译和分析

完整流程:
1. 启动 JADX-GUI 并打开 APK
2. MCP Server 连接到 JADX
3. 通过 MCP 协议进行代码分析
"""
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import json
import logging
import time
import re
import httpx
import threading

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
        server_url: str = "http://localhost:3000",
        jadx_port: int = 8652,
        jadx_path: Optional[str] = None,
        jadx_gui_path: Optional[str] = None,
        mcp_server_path: Optional[str] = None,
        uv_path: str = "uv",
        timeout: float = 30.0,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        """
        初始化 MCP 客户端

        Args:
            server_url: MCP Server HTTP 地址
            jadx_port: JADX 运行端口
            jadx_path: jadx 可执行文件路径（回退用）
            jadx_gui_path: jadx-gui 可执行文件路径
            mcp_server_path: JADX MCP Server 路径
            uv_path: uv 可执行文件路径
            timeout: 请求超时时间
            on_status_update: 状态更新回调函数
        """
        self.server_url = server_url.rstrip("/")
        self.jadx_port = jadx_port
        self.jadx_path = jadx_path or self._find_jadx()
        self.jadx_gui_path = jadx_gui_path or self._find_jadx_gui()
        self.mcp_server_path = mcp_server_path
        self.uv_path = uv_path
        self.timeout = timeout
        self.on_status_update = on_status_update or (lambda msg: None)

        self._connected = False
        self._current_apk: Optional[str] = None
        self._jadx_gui_process: Optional[subprocess.Popen] = None
        self._mcp_process: Optional[subprocess.Popen] = None
        self._output_dir: Optional[str] = None
        self._use_fallback = False

    def _find_jadx(self) -> str:
        """查找 jadx 可执行文件"""
        for name in ["jadx", "jadx.bat"]:
            try:
                result = subprocess.run(
                    ["which", name] if name != "jadx.bat" else ["where", name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        return "jadx"

    def _find_jadx_gui(self) -> str:
        """查找 jadx-gui 可执行文件"""
        candidates = ["jadx-gui", "jadx-gui.bat", "jadx"]

        # 检查常见的安装路径
        common_paths = [
            "~/jadx/jadx-gui",
            "/opt/jadx/bin/jadx-gui",
            "/usr/local/bin/jadx-gui",
        ]

        for path in common_paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                return str(expanded)

        for name in candidates:
            try:
                result = subprocess.run(
                    ["which", name] if not name.endswith(".bat") else ["where", name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        # 默认返回 jadx，尝试用同一个二进制
        return self.jadx_path

    def connect(self) -> bool:
        """
        连接到 MCP Server

        Returns:
            连接是否成功
        """
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

        # 尝试启动 MCP Server
        if self.mcp_server_path:
            self.on_status_update("尝试启动 JADX MCP Server...")
            return self._start_mcp_server()

        # 标记使用回退模式
        self._use_fallback = True
        self.on_status_update("ℹ️ 使用 jadx-cli 回退模式")
        self._connected = True
        return True

    def _start_mcp_server(self) -> bool:
        """启动 JADX MCP Server"""
        if not Path(self.mcp_server_path).exists():
            self.on_status_update(f"⚠️ MCP Server 路径不存在: {self.mcp_server_path}")
            self._use_fallback = True
            return True

        try:
            cmd = [
                self.uv_path,
                "--directory",
                self.mcp_server_path,
                "run",
                "jadx_mcp_server.py",
                "--jadx-port",
                str(self.jadx_port)
            ]

            self._mcp_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            time.sleep(2)

            if self._mcp_process.poll() is None:
                self.on_status_update("✅ JADX MCP Server 启动成功")
                return True
            else:
                stderr = self._mcp_process.stderr.read()
                self.on_status_update(f"❌ MCP Server 启动失败: {stderr}")
                self._use_fallback = True
                return True

        except Exception as e:
            self.on_status_update(f"❌ 启动 MCP Server 失败: {e}")
            self._use_fallback = True
            return True

    def open_apk_in_jadx_gui(self, apk_path: str) -> Dict[str, Any]:
        """
        在 JADX-GUI 中打开 APK

        这是完整流程的第一步：
        1. 启动 JADX-GUI（如果未运行）
        2. 打开指定的 APK 文件

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

        # 检查 jadx-gui 是否存在
        if not self.jadx_gui_path or not Path(self.jadx_gui_path).exists():
            self.on_status_update("⚠️ jadx-gui 不可用，使用命令行模式")
            return self._open_apk_cli(apk_path)

        # 启动 jadx-gui 并打开 APK
        try:
            # 使用单独的线程启动 GUI，避免阻塞
            def launch_gui():
                try:
                    subprocess.Popen(
                        [self.jadx_gui_path, str(apk_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e:
                    logger.error(f"启动 JADX-GUI 失败: {e}")

            thread = threading.Thread(target=launch_gui, daemon=True)
            thread.start()

            # 等待 GUI 启动
            time.sleep(3)

            self.on_status_update("✅ JADX-GUI 已启动并打开 APK")

            return {
                "success": True,
                "apk_path": apk_path,
                "method": "jadx-gui",
                "message": "APK 已在 JADX-GUI 中打开"
            }

        except Exception as e:
            self.on_status_update(f"⚠️ 启动 JADX-GUI 失败: {e}")
            return self._open_apk_cli(apk_path)

    def _open_apk_cli(self, apk_path: str) -> Dict[str, Any]:
        """使用命令行模式打开 APK（回退方案）"""
        self.on_status_update(f"📦 使用 jadx-cli 处理: {Path(apk_path).name}")

        self._output_dir = tempfile.mkdtemp(prefix="jadx_fallback_")

        cmd = [
            self.jadx_path,
            "-d", self._output_dir,
            "--no-res",
            "--no-imports",
            str(apk_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr,
                    "method": "jadx-cli-failed"
                }

            self.on_status_update("✅ jadx-cli 处理完成")

            return {
                "success": True,
                "apk_path": apk_path,
                "output_dir": self._output_dir,
                "method": "jadx-cli"
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "处理超时"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "未找到 jadx，请安装: wget https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip"
            }

    def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用 MCP 工具"""
        if self._use_fallback:
            return {"success": False, "error": "fallback mode"}

        try:
            response = httpx.post(
                f"{self.server_url}/tools/{tool_name}",
                json=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"MCP 调用失败: {e}")
            return {"success": False, "error": str(e)}

    def get_manifest(self) -> Dict[str, Any]:
        """获取 AndroidManifest.xml 内容"""
        if self._use_fallback or self._output_dir:
            return self._parse_local_manifest()

        result = self._call_mcp_tool("jadx_get_manifest", {})
        return result if result.get("success") else {}

    def _parse_local_manifest(self) -> Dict[str, Any]:
        """从本地解析 Manifest"""
        if not self._output_dir:
            return {}

        manifest_path = Path(self._output_dir) / "AndroidManifest.xml"
        if not manifest_path.exists():
            return {}

        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            ns = {"android": "http://schemas.android.com/apk/res/android"}

            result = {
                "package": root.get("package"),
                "version_code": root.get(f"{{{ns['android']}}}versionCode"),
                "version_name": root.get(f"{{{ns['android']}}}versionName"),
                "permissions": [],
                "permissions_dangerous": [],
                "activities": [],
                "services": [],
                "receivers": [],
                "providers": []
            }

            for perm in root.findall("uses-permission"):
                perm_name = perm.get(f"{{{ns['android']}}}name")
                if perm_name:
                    result["permissions"].append(perm_name)
                    if perm_name in self.DANGEROUS_PERMISSIONS:
                        result["permissions_dangerous"].append(perm_name)

            for app in root.findall("application"):
                for activity in app.findall("activity"):
                    name = activity.get(f"{{{ns['android']}}}name")
                    if name:
                        result["activities"].append(name)
                for service in app.findall("service"):
                    name = service.get(f"{{{ns['android']}}}name")
                    if name:
                        result["services"].append(name)
                for receiver in app.findall("receiver"):
                    name = receiver.get(f"{{{ns['android']}}}name")
                    if name:
                        result["receivers"].append(name)
                for provider in app.findall("provider"):
                    name = provider.get(f"{{{ns['android']}}}name")
                    if name:
                        result["providers"].append(name)

            return result

        except ET.ParseError as e:
            logger.error(f"解析 Manifest 失败: {e}")
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
        if self._use_fallback or self._output_dir:
            return self._get_local_code_paths()

        result = self._call_mcp_tool("jadx_get_code_paths", {})
        return result.get("paths", []) if result.get("success") else []

    def _get_local_code_paths(self) -> List[str]:
        """从本地获取代码路径"""
        if not self._output_dir:
            return []

        paths = []
        sources_dir = Path(self._output_dir) / "sources"
        if not sources_dir.exists():
            return paths

        for java_file in sources_dir.rglob("*.java"):
            rel_path = java_file.relative_to(sources_dir)
            paths.append(str(rel_path).replace(".java", ""))

        return paths

    def get_strings(self, min_length: int = 4) -> List[str]:
        """提取字符串"""
        if self._use_fallback or self._output_dir:
            return self._extract_local_strings(min_length)

        result = self._call_mcp_tool("jadx_get_strings", {
            "min_length": min_length
        })
        return result.get("strings", []) if result.get("success") else []

    def _extract_local_strings(self, min_length: int) -> List[str]:
        """从本地提取字符串"""
        strings = set()
        sources_dir = Path(self._output_dir) / "sources"

        if sources_dir.exists():
            for java_file in sources_dir.rglob("*.java"):
                try:
                    content = java_file.read_text(encoding="utf-8", errors="ignore")
                    for match in re.finditer(r'"([^"]+)"', content):
                        s = match.group(1)
                        if len(s) >= min_length:
                            strings.add(s)
                except Exception:
                    pass

        return sorted(strings)

    def get_apis(self) -> List[Dict[str, Any]]:
        """获取 API 调用"""
        if self._use_fallback or self._output_dir:
            return self._analyze_local_apis()

        result = self._call_mcp_tool("jadx_get_apis", {})
        return result.get("apis", []) if result.get("success") else []

    def _analyze_local_apis(self) -> List[Dict[str, Any]]:
        """分析本地 API 调用"""
        apis = []
        api_patterns = [
            (r'(\w+)\.getDeviceId\(\)', 'TelephonyManager', 'getDeviceId'),
            (r'(\w+)\.getSubscriberId\(\)', 'TelephonyManager', 'getSubscriberId'),
            (r'(\w+)\.sendTextMessage\(', 'SmsManager', 'sendTextMessage'),
            (r'(\w+)\.requestLocationUpdates\(', 'LocationManager', 'requestLocationUpdates'),
            (r'Runtime\.getRuntime\(\)\.exec\(', 'Runtime', 'exec'),
        ]

        sources_dir = Path(self._output_dir) / "sources"
        if not sources_dir.exists():
            return apis

        for java_file in sources_dir.rglob("*.java"):
            try:
                content = java_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for pattern, cls, method in api_patterns:
                        if re.search(pattern, line):
                            apis.append({
                                "class": cls,
                                "method": method,
                                "file": str(java_file.relative_to(sources_dir)),
                                "line": line_num,
                                "code": line.strip()
                            })
            except Exception:
                pass

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

                    from urllib.parse import urlparse
                    parsed = urlparse(match)
                    if parsed.netloc and parsed.netloc not in info["domains"]:
                        info["domains"].append(parsed.netloc)

            for match in ip_pattern.findall(s):
                if match not in info["ips"]:
                    info["ips"].append(match)

        return info

    def close(self):
        """关闭客户端"""
        if hasattr(self, '_mcp_process') and self._mcp_process:
            try:
                self._mcp_process.terminate()
                self._mcp_process.wait(timeout=5)
            except:
                self._mcp_process.kill()
            self._mcp_process = None

    def __del__(self):
        """析构函数"""
        self.close()


# 便捷函数
def create_mcp_client(
    server_url: str = "http://localhost:3000",
    jadx_port: int = 8652,
    jadx_path: Optional[str] = None,
    jadx_gui_path: Optional[str] = None,
    mcp_server_path: Optional[str] = None,
    uv_path: str = "uv",
    on_status_update: Optional[Callable[[str], None]] = None
) -> JMCPClient:
    """
    创建 MCP 客户端

    Args:
        server_url: MCP Server 地址
        jadx_port: JADX 端口
        jadx_path: jadx 可执行文件路径
        jadx_gui_path: jadx-gui 可执行文件路径
        mcp_server_path: JADX MCP Server 路径
        uv_path: uv 可执行文件路径
        on_status_update: 状态更新回调

    Returns:
        JMCPClient 实例
    """
    client = JMCPClient(
        server_url=server_url,
        jadx_port=jadx_port,
        jadx_path=jadx_path,
        jadx_gui_path=jadx_gui_path,
        mcp_server_path=mcp_server_path,
        uv_path=uv_path,
        on_status_update=on_status_update
    )
    client.connect()
    return client
