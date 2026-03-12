"""
JADX 命令行工具封装

使用 jadx-cli 进行 APK 反编译和分析
"""
import subprocess
import tempfile
import shutil
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class JadxWrapper:
    """
    JADX 命令行工具封装

    使用 jadx-cli 直接反编译 APK，无需 GUI 或 MCP Server
    """

    # 危险权限列表
    DANGEROUS_PERMISSIONS = {
        # 位置相关
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
        # 短信相关
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.RECEIVE_SMS",
        # 电话相关
        "android.permission.READ_PHONE_STATE",
        "android.permission.CALL_PHONE",
        "android.permission.READ_CALL_LOG",
        "android.permission.READ_CONTACTS",
        # 存储相关
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        # 摄像头/麦克风
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        # 其他
        "android.permission.GET_ACCOUNTS",
        "android.permission.READ_CALENDAR",
    }

    def __init__(
        self,
        jadx_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        keep_output: bool = False
    ):
        """
        初始化 JADX 封装器

        Args:
            jadx_path: jadx 可执行文件路径，默认从 PATH 查找
            output_dir: 反编译输出目录，默认使用临时目录
            keep_output: 是否保留反编译输出
        """
        self.jadx_path = jadx_path or self._find_jadx()
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="jadx_output_")
        self.keep_output = keep_output
        self._current_apk: Optional[str] = None
        self._decompiled: bool = False

    def _find_jadx(self) -> str:
        """查找 jadx 可执行文件"""
        # 先检查 PATH 中是否有 jadx
        for name in ["jadx", "jadx.bat"]:
            try:
                result = subprocess.run(
                    ["which", name] if name != "jadx.bat" else ["where", name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except FileNotFoundError:
                pass

        # 默认返回 jadx，假设在 PATH 中
        return "jadx"

    def decompile_apk(
        self,
        apk_path: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        反编译 APK 文件

        Args:
            apk_path: APK 文件路径
            force: 是否强制重新反编译

        Returns:
            反编译结果，包含代码结构信息
        """
        apk_file = Path(apk_path)
        if not apk_file.exists():
            raise FileNotFoundError(f"APK 文件不存在: {apk_path}")

        # 检查是否已经反编译过
        if self._current_apk == apk_path and self._decompiled and not force:
            return self._get_decompile_info()

        # 清理旧输出
        if self._decompiled and not self.keep_output:
            self._cleanup_output()

        # 执行反编译
        logger.info(f"正在反编译 APK: {apk_path}")

        cmd = [
            self.jadx_path,
            "-d", self.output_dir,
            "--no-res",  # 不反编译资源文件（加快速度）
            "--deobf",   # 简单的反混淆
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
                logger.error(f"jadx 执行失败: {result.stderr}")
                raise RuntimeError(f"反编译失败: {result.stderr}")

            self._current_apk = apk_path
            self._decompiled = True

            logger.info(f"反编译完成，输出目录: {self.output_dir}")
            return self._get_decompile_info()

        except subprocess.TimeoutExpired:
            raise RuntimeError("反编译超时（5分钟）")
        except FileNotFoundError:
            raise RuntimeError(
                f"未找到 jadx 命令。请安装 jadx:\n"
                f"  wget https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip\n"
                f"  unzip jadx-1.5.0.zip -d ~/jadx\n"
                f"  export PATH=$PATH:~/jadx/jadx-1.5.0"
            )

    def _get_decompile_info(self) -> Dict[str, Any]:
        """获取反编译信息"""
        if not self._decompiled:
            return {"success": False, "error": "未反编译任何 APK"}

        info = {
            "success": True,
            "output_dir": self.output_dir,
            "packages": [],
            "activities": [],
            "services": [],
            "receivers": [],
            "providers": []
        }

        # 扫描包结构
        sources_dir = Path(self.output_dir) / "sources"
        if sources_dir.exists():
            info["packages"] = self._scan_packages(sources_dir)

        # 解析 manifest
        manifest = self.get_manifest()
        if manifest:
            info.update({
                "package": manifest.get("package"),
                "version_code": manifest.get("version_code"),
                "version_name": manifest.get("version_name"),
                "activities": manifest.get("activities", []),
                "services": manifest.get("services", []),
                "receivers": manifest.get("receivers", []),
                "providers": manifest.get("providers", [])
            })

        return info

    def _scan_packages(self, sources_dir: Path) -> List[str]:
        """扫描包结构"""
        packages = set()

        for java_file in sources_dir.rglob("*.java"):
            # 将文件路径转换为包名
            rel_path = java_file.relative_to(sources_dir)
            parts = list(rel_path.parts[:-1])  # 去掉文件名
            if parts:
                packages.add(".".join(parts))

        return sorted(packages)

    def get_manifest(self) -> Dict[str, Any]:
        """
        获取 AndroidManifest.xml 内容

        Returns:
            Manifest 解析结果
        """
        if not self._decompiled:
            return {}

        manifest_path = Path(self.output_dir) / "AndroidManifest.xml"
        if not manifest_path.exists():
            return {}

        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()

            # 处理 Android 命名空间
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

    def get_permissions(self) -> Dict[str, Any]:
        """
        获取 APK 声明的权限列表

        Returns:
            权限信息，包含全部权限和危险权限
        """
        manifest = self.get_manifest()
        return {
            "all": manifest.get("permissions", []),
            "dangerous": manifest.get("permissions_dangerous", []),
            "count": len(manifest.get("permissions", [])),
            "dangerous_count": len(manifest.get("permissions_dangerous", []))
        }

    def get_package_paths(self) -> List[str]:
        """
        获取所有包路径（转换为正则匹配格式）

        Returns:
            包路径列表，如 ["com/example/app/", "com/example/app/activity/"]
        """
        if not self._decompiled:
            return []

        sources_dir = Path(self.output_dir) / "sources"
        if not sources_dir.exists():
            return []

        paths = set()
        for java_file in sources_dir.rglob("*.java"):
            # 转换为正则格式的路径
            rel_path = java_file.relative_to(sources_dir)
            dir_path = str(rel_path.parent)
            if dir_path != ".":
                paths.add(dir_path)

        return sorted(paths)

    def search_code(
        self,
        pattern: str,
        search_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        在反编译代码中搜索

        Args:
            pattern: 搜索模式
            search_type: 搜索类型 (text, regex, api)

        Returns:
            匹配结果列表
        """
        if not self._decompiled:
            return []

        results = []
        sources_dir = Path(self.output_dir) / "sources"
        if not sources_dir.exists():
            return results

        # 编译正则表达式
        if search_type == "regex":
            try:
                regex = re.compile(pattern)
            except re.error:
                logger.error(f"无效的正则表达式: {pattern}")
                return results
        else:
            regex = None

        # 搜索所有 Java 文件
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
                            "code": line.strip(),
                            "context": self._get_context(lines, line_num - 1)
                        })
            except Exception as e:
                logger.debug(f"搜索文件失败 {java_file}: {e}")

        return results

    def _get_context(self, lines: List[str], line_idx: int, context_size: int = 2) -> str:
        """获取代码上下文"""
        start = max(0, line_idx - context_size)
        end = min(len(lines), line_idx + context_size + 1)
        return "\n".join(lines[start:end])

    def get_strings(self, min_length: int = 4) -> List[str]:
        """
        提取 APK 中的字符串

        Args:
            min_length: 最小字符串长度

        Returns:
            字符串列表
        """
        strings = set()

        # 从 Java 文件中提取字符串
        sources_dir = Path(self.output_dir) / "sources"
        if sources_dir.exists():
            for java_file in sources_dir.rglob("*.java"):
                try:
                    content = java_file.read_text(encoding="utf-8", errors="ignore")
                    # 匹配 Java 字符串字面量
                    for match in re.finditer(r'"([^"]+)"', content):
                        s = match.group(1)
                        if len(s) >= min_length:
                            strings.add(s)
                except Exception:
                    pass

        return sorted(strings)

    def get_apis(self) -> List[Dict[str, Any]]:
        """
        获取 APK 使用的 API 调用

        Returns:
            API 调用列表，包含类名、方法名、调用位置
        """
        apis = []

        # 常见敏感 API 模式
        api_patterns = [
            (r'(\w+)\.getDeviceId\(\)', 'TelephonyManager', 'getDeviceId'),
            (r'(\w+)\.getSubscriberId\(\)', 'TelephonyManager', 'getSubscriberId'),
            (r'(\w+)\.sendTextMessage\(', 'SmsManager', 'sendTextMessage'),
            (r'(\w+)\.requestLocationUpdates\(', 'LocationManager', 'requestLocationUpdates'),
            (r'(\w+)\.getLastKnownLocation\(', 'LocationManager', 'getLastKnownLocation'),
            (r'Runtime\.getRuntime\(\)\.exec\(', 'Runtime', 'exec'),
            (r'ProcessBuilder\(', 'ProcessBuilder', '<init>'),
            (r'ClassLoader\.getSystemClassLoader\(\)', 'ClassLoader', 'getSystemClassLoader'),
        ]

        sources_dir = Path(self.output_dir) / "sources"
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
        """
        分析网络通信信息

        Returns:
            网络信息，包含 URL、IP、端口等
        """
        info = {
            "urls": [],
            "ips": [],
            "domains": [],
            "has_encryption": False,
            "has_http": False,
            "has_https": False
        }

        # URL 正则
        url_pattern = re.compile(
            r'(https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)'
        )

        # IP 正则
        ip_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        )

        strings = self.get_strings()

        for s in strings:
            # 检查 URL
            for match in url_pattern.findall(s):
                if match not in info["urls"]:
                    info["urls"].append(match)
                    if match.startswith("https://"):
                        info["has_https"] = True
                        info["has_encryption"] = True
                    elif match.startswith("http://"):
                        info["has_http"] = True

                    # 提取域名
                    from urllib.parse import urlparse
                    parsed = urlparse(match)
                    if parsed.netloc and parsed.netloc not in info["domains"]:
                        info["domains"].append(parsed.netloc)

            # 检查 IP
            for match in ip_pattern.findall(s):
                if match not in info["ips"]:
                    info["ips"].append(match)

        return info

    def get_code_paths(self) -> List[str]:
        """
        获取所有代码文件路径（用于规则匹配）

        Returns:
            代码文件路径列表
        """
        if not self._decompiled:
            return []

        paths = []
        sources_dir = Path(self.output_dir) / "sources"
        if not sources_dir.exists():
            return paths

        for java_file in sources_dir.rglob("*.java"):
            # 转换为类似 jadx 的路径格式
            rel_path = java_file.relative_to(sources_dir)
            paths.append(str(rel_path).replace(".java", ""))

        return paths

    def _cleanup_output(self):
        """清理反编译输出"""
        if not self.keep_output and Path(self.output_dir).exists():
            try:
                shutil.rmtree(self.output_dir)
            except Exception as e:
                logger.warning(f"清理输出目录失败: {e}")

    def __del__(self):
        """析构函数，清理临时文件"""
        if not self.keep_output:
            self._cleanup_output()


# 兼容性别名
JMCPClient = JadxWrapper


# 便捷函数
def create_jadx_wrapper(
    jadx_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    keep_output: bool = False
) -> JadxWrapper:
    """
    创建 JADX 封装器

    Args:
        jadx_path: jadx 可执行文件路径
        output_dir: 反编译输出目录
        keep_output: 是否保留反编译输出

    Returns:
        JadxWrapper 实例
    """
    return JadxWrapper(
        jadx_path=jadx_path,
        output_dir=output_dir,
        keep_output=keep_output
    )


def create_mcp_client(server_url: str = "http://localhost:3000") -> JadxWrapper:
    """
    创建 JADX 客户端（兼容旧 API）

    Args:
        server_url: 忽略此参数，仅为兼容性保留

    Returns:
        JadxWrapper 实例
    """
    return create_jadx_wrapper()
