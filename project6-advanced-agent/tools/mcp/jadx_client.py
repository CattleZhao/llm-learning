"""
JADX MCP 客户端模块

用于连接 JADX MCP Server 进行 APK 反编译和分析
"""
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging
import time
import re

logger = logging.getLogger(__name__)


class JMCPClient:
    """
    JADX MCP 客户端

    通过 MCP 协议与 JADX MCP Server 通信，
    实现 APK 反编译和代码分析功能
    """

    # JADX 可执行文件路径
    JADX_BIN = "jadx"

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
        jadx_path: Optional[str] = None,
        auto_open: bool = True
    ):
        """
        初始化 MCP 客户端

        Args:
            server_url: MCP Server 地址
            jadx_path: jadx 可执行文件路径（用于自动打开 APK）
            auto_open: 是否自动打开 APK
        """
        self.server_url = server_url
        self.jadx_path = jadx_path or self._find_jadx()
        self.auto_open = auto_open
        self._connected = False
        self._current_apk: Optional[str] = None
        self._jadx_process: Optional[subprocess.Popen] = None
        self._output_dir: Optional[str] = None

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

    def connect(self) -> bool:
        """
        连接到 MCP Server

        Returns:
            连接是否成功
        """
        # TODO: 实现 MCP 握手协议
        self._connected = True
        return True

    def open_apk(self, apk_path: str) -> Dict[str, Any]:
        """
        在 JADX 中打开 APK（通过 MCP 触发或启动 jadx-gui）

        Args:
            apk_path: APK 文件路径

        Returns:
            打开结果
        """
        apk_file = Path(apk_path)
        if not apk_file.exists():
            raise FileNotFoundError(f"APK 文件不存在: {apk_path}")

        self._current_apk = str(apk_file)

        # 方法1: 尝试通过 MCP 调用 jadx.open_apk
        mcp_result = self._call_tool("jadx.open_apk", {
            "apk_path": apk_path
        })

        # 如果 MCP 成功，直接返回
        if mcp_result.get("success"):
            return mcp_result

        # 方法2: MCP 失败时，使用 jadx-cli 预处理
        logger.info(f"MCP 不可用，使用 jadx-cli 预处理: {apk_path}")

        # 创建临时输出目录
        self._output_dir = tempfile.mkdtemp(prefix="jadx_mcp_")

        # 使用 jadx-cli 反编译（只反编译代码，不反编译资源）
        cmd = [
            self.jadx_path,
            "-d", self._output_dir,
            "--no-res",  # 不反编译资源
            "--no-imports",  # 不优化导入
            str(apk_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                logger.error(f"jadx 处理失败: {result.stderr}")
                return {"success": False, "error": result.stderr}

            logger.info(f"jadx 处理完成，输出目录: {self._output_dir}")

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
                "error": f"未找到 jadx。请安装: wget https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip"
            }

    def decompile_apk(self, apk_path: str) -> Dict[str, Any]:
        """
        反编译 APK 文件

        Args:
            apk_path: APK 文件路径

        Returns:
            反编译结果，包含代码结构信息
        """
        # 确保已打开 APK
        if self._current_apk != apk_path:
            self.open_apk(apk_path)

        return self._call_tool("jadx.decompile", {
            "apk_path": apk_path,
            "output_format": "tree"
        })

    def get_manifest(self, apk_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 AndroidManifest.xml 内容

        Args:
            apk_path: APK 文件路径（可选，如果已打开则使用当前 APK）

        Returns:
            Manifest 解析结果
        """
        # 优先从本地文件解析
        if self._output_dir:
            return self._parse_local_manifest()

        # 否则通过 MCP 获取
        if apk_path:
            if self._current_apk != apk_path:
                self.open_apk(apk_path)

        return self._call_tool("jadx.get_manifest", {
            "apk_path": self._current_apk
        })

    def _parse_local_manifest(self) -> Dict[str, Any]:
        """从本地反编译结果解析 Manifest"""
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

            # 解析权限
            for perm in root.findall("uses-permission"):
                perm_name = perm.get(f"{{{ns['android']}}}name")
                if perm_name:
                    result["permissions"].append(perm_name)
                    if perm_name in self.DANGEROUS_PERMISSIONS:
                        result["permissions_dangerous"].append(perm_name)

            # 解析组件
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

    def get_permissions(self, apk_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 APK 声明的权限列表

        Args:
            apk_path: APK 文件路径（可选）

        Returns:
            权限信息，包含全部权限和危险权限
        """
        manifest = self.get_manifest(apk_path)
        return {
            "all": manifest.get("permissions", []),
            "dangerous": manifest.get("permissions_dangerous", []),
            "count": len(manifest.get("permissions", [])),
            "dangerous_count": len(manifest.get("permissions_dangerous", []))
        }

    def get_package_paths(self) -> List[str]:
        """
        获取所有包路径

        Returns:
            包路径列表
        """
        if not self._output_dir:
            # 通过 MCP 获取
            result = self._call_tool("jadx.get_package_paths", {})
            return result.get("paths", [])

        # 从本地扫描
        paths = []
        sources_dir = Path(self._output_dir) / "sources"
        if sources_dir.exists():
            for java_file in sources_dir.rglob("*.java"):
                rel_path = java_file.relative_to(sources_dir)
                dir_path = str(rel_path.parent)
                if dir_path != "." and dir_path not in paths:
                    paths.append(dir_path)

        return sorted(paths)

    def get_code_paths(self) -> List[str]:
        """
        获取所有代码文件路径（用于规则匹配）

        Returns:
            代码文件路径列表
        """
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

    def search_code(
        self,
        apk_path: str,
        pattern: str,
        search_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        在反编译代码中搜索

        Args:
            apk_path: APK 文件路径
            pattern: 搜索模式
            search_type: 搜索类型 (text, regex, api)

        Returns:
            匹配结果列表
        """
        # 如果有本地输出，直接搜索
        if self._output_dir:
            return self._search_local_code(pattern, search_type)

        # 否则通过 MCP
        return self._call_tool("jadx.search", {
            "apk_path": apk_path,
            "pattern": pattern,
            "type": search_type
        })

    def _search_local_code(self, pattern: str, search_type: str) -> List[Dict[str, Any]]:
        """在本地代码中搜索"""
        results = []
        sources_dir = Path(self._output_dir) / "sources"
        if not sources_dir.exists():
            return results

        # 编译正则表达式
        if search_type == "regex":
            try:
                regex = re.compile(pattern)
            except re.error:
                return results
        else:
            regex = None

        for java_file in sources_dir.rglob("*.java"):
            try:
                content = java_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    matched = False
                    if search_type == "regex" and regex:
                        matched = regex.search(line) is not None
                    else:
                        matched = pattern in line

                    if matched:
                        results.append({
                            "file": str(java_file.relative_to(sources_dir)),
                            "line": line_num,
                            "code": line.strip()
                        })
            except Exception:
                pass

        return results

    def get_strings(self, apk_path: Optional[str] = None, min_length: int = 4) -> List[str]:
        """
        提取 APK 中的字符串

        Args:
            apk_path: APK 文件路径（可选）
            min_length: 最小字符串长度

        Returns:
            字符串列表
        """
        # 如果有本地输出，直接提取
        if self._output_dir:
            return self._extract_local_strings(min_length)

        # 否则通过 MCP
        result = self._call_tool("jadx.get_strings", {
            "apk_path": apk_path or self._current_apk,
            "min_length": min_length
        })
        return result.get("strings", []) if isinstance(result, dict) else result

    def _extract_local_strings(self, min_length: int) -> List[str]:
        """从本地代码中提取字符串"""
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

    def get_apis(self, apk_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取 APK 使用的 API 调用

        Args:
            apk_path: APK 文件路径（可选）

        Returns:
            API 调用列表
        """
        # 如果有本地输出，直接分析
        if self._output_dir:
            return self._analyze_local_apis()

        # 否则通过 MCP
        result = self._call_tool("jadx.get_apis", {
            "apk_path": apk_path or self._current_apk
        })
        return result.get("apis", []) if isinstance(result, dict) else result

    def _analyze_local_apis(self) -> List[Dict[str, Any]]:
        """分析本地代码中的 API 调用"""
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

    def get_network_info(self, apk_path: Optional[str] = None) -> Dict[str, Any]:
        """
        分析网络通信信息

        Args:
            apk_path: APK 文件路径（可选）

        Returns:
            网络信息
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

        strings = self.get_strings(apk_path)

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

    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        调用 MCP 工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果
        """
        # TODO: 实现 MCP 协议通信
        # 这里先返回模拟数据或使用本地处理
        return self._mock_response(tool_name, params)

    def _mock_response(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """模拟 MCP 响应（MCP 不可用时使用）"""
        # 返回失败，让上层使用本地处理
        return {"success": False, "error": "MCP not available"}

    def close(self):
        """关闭客户端，清理资源"""
        if self._jadx_process:
            try:
                self._jadx_process.terminate()
                self._jadx_process.wait(timeout=5)
            except:
                self._jadx_process.kill()
            self._jadx_process = None

    def __del__(self):
        """析构函数"""
        self.close()


# 便捷函数
def create_mcp_client(
    server_url: str = "http://localhost:3000",
    jadx_path: Optional[str] = None,
    auto_open: bool = True
) -> JMCPClient:
    """
    创建 MCP 客户端

    Args:
        server_url: MCP Server 地址
        jadx_path: jadx 可执行文件路径
        auto_open: 是否自动打开 APK

    Returns:
        JMCPClient 实例
    """
    client = JMCPClient(
        server_url=server_url,
        jadx_path=jadx_path,
        auto_open=auto_open
    )
    client.connect()
    return client
