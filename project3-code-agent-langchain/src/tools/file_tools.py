"""
文件操作工具模块

提供workspace目录下的文件操作功能，包括：
- 读取文件内容
- 写入文件
- 列出目录文件
- 搜索文件
"""

import os
import fnmatch
from typing import List, Optional
from pathlib import Path


def tool(func):
    """装饰器：标记方法可被Agent调用"""
    func.is_tool = True
    return func


class FileTools:
    """文件操作工具类，处理workspace目录下的文件操作"""

    def __init__(self, workspace_dir: str = "/root/Learn/llm-learning/project3-code-agent/workspace"):
        """
        初始化文件工具

        Args:
            workspace_dir: 工作区目录路径
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        # 确保工作区目录存在
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, filepath: str) -> Path:
        """
        解析文件路径，确保在workspace目录下

        Args:
            filepath: 文件路径（可以是相对路径或绝对路径）

        Returns:
            解析后的Path对象

        Raises:
            ValueError: 如果路径超出workspace目录
        """
        path = Path(filepath)
        if not path.is_absolute():
            path = self.workspace_dir / path

        # 解析为绝对路径（处理..等符号链接）
        resolved_path = path.resolve()

        # 验证路径是否在workspace目录下
        try:
            resolved_path.relative_to(self.workspace_dir)
        except ValueError:
            raise ValueError(f"路径超出workspace目录范围: {filepath}")

        return resolved_path

    @tool
    def read_file(self, filepath: str) -> str:
        """
        读取文件内容

        Args:
            filepath: 文件路径（相对于workspace或绝对路径）

        Returns:
            文件内容字符串

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 路径超出workspace目录
        """
        path = self._resolve_path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        if not path.is_file():
            raise ValueError(f"路径不是文件: {filepath}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                raise IOError(f"无法读取文件 {filepath}: {e}")

    @tool
    def write_file(self, filepath: str, content: str) -> str:
        """
        写入文件内容

        Args:
            filepath: 文件路径（相对于workspace或绝对路径）
            content: 要写入的内容

        Returns:
            成功消息

        Raises:
            ValueError: 路径超出workspace目录
        """
        path = self._resolve_path(filepath)

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"成功写入文件: {path}"
        except Exception as e:
            raise IOError(f"无法写入文件 {filepath}: {e}")

    @tool
    def list_files(self, directory: str = "") -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径（相对于workspace，空字符串表示workspace根目录）

        Returns:
            文件和目录列表

        Raises:
            ValueError: 路径超出workspace目录
        """
        if directory:
            path = self._resolve_path(directory)
        else:
            path = self.workspace_dir

        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")

        if not path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")

        try:
            # 返回相对路径，便于后续操作
            items = []
            for item in path.iterdir():
                rel_path = item.relative_to(self.workspace_dir)
                items.append(str(rel_path))
            return sorted(items)
        except Exception as e:
            raise IOError(f"无法列出目录 {directory}: {e}")

    @tool
    def search_files(self, pattern: str, directory: str = "") -> List[str]:
        """
        搜索包含特定模式的文件

        Args:
            pattern: 文件名模式（支持通配符，如 *.py, test_*.txt）
            directory: 搜索目录（相对于workspace，空字符串表示workspace根目录）

        Returns:
            匹配的文件路径列表

        Raises:
            ValueError: 路径超出workspace目录
        """
        if directory:
            search_path = self._resolve_path(directory)
        else:
            search_path = self.workspace_dir

        if not search_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")

        if not search_path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")

        matches = []

        try:
            # 递归搜索匹配的文件
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        full_path = Path(root) / filename
                        rel_path = full_path.relative_to(self.workspace_dir)
                        matches.append(str(rel_path))
            return sorted(matches)
        except Exception as e:
            raise IOError(f"搜索文件时出错: {e}")

    @tool
    def file_exists(self, filepath: str) -> bool:
        """
        检查文件是否存在

        Args:
            filepath: 文件路径（相对于workspace或绝对路径）

        Returns:
            文件是否存在
        """
        path = self._resolve_path(filepath)
        return path.exists() and path.is_file()

    @tool
    def delete_file(self, filepath: str) -> str:
        """
        删除文件

        Args:
            filepath: 文件路径（相对于workspace或绝对路径）

        Returns:
            成功消息

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 路径超出workspace目录
        """
        path = self._resolve_path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        if not path.is_file():
            raise ValueError(f"路径不是文件: {filepath}")

        try:
            path.unlink()
            return f"成功删除文件: {path}"
        except Exception as e:
            raise IOError(f"无法删除文件 {filepath}: {e}")

    @tool
    def create_directory(self, directory: str) -> str:
        """
        创建目录

        Args:
            directory: 目录路径（相对于workspace或绝对路径）

        Returns:
            成功消息
        """
        path = self._resolve_path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return f"成功创建目录: {path}"

    def get_tools(self):
        """
        获取所有可用的工具方法

        Returns:
            工具方法列表
        """
        tools = []
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, 'is_tool') and attr.is_tool:
                tools.append(attr)
        return tools
