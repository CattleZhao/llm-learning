"""
文件操作工具模块测试
"""

import os
import unittest
import tempfile
import shutil
from pathlib import Path

from src.tools.file_tools import FileTools


class TestFileTools(unittest.TestCase):
    """FileTools类的测试用例"""

    def setUp(self):
        """测试前准备：创建临时工作区"""
        self.test_dir = tempfile.mkdtemp()
        self.file_tools = FileTools(workspace_dir=self.test_dir)

    def tearDown(self):
        """测试后清理：删除临时目录"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_creates_workspace(self):
        """测试初始化时创建workspace目录"""
        new_dir = os.path.join(tempfile.gettempdir(), "test_workspace_new")
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)

        FileTools(workspace_dir=new_dir)
        self.assertTrue(os.path.exists(new_dir))

        shutil.rmtree(new_dir)

    def test_write_and_read_file(self):
        """测试写入和读取文件"""
        content = "Hello, World!\nThis is a test file."
        filepath = "test.txt"

        # 写入文件
        result = self.file_tools.write_file(filepath, content)
        self.assertIn("成功写入文件", result)

        # 读取文件
        read_content = self.file_tools.read_file(filepath)
        self.assertEqual(content, read_content)

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.file_tools.read_file("nonexistent.txt")

    def test_write_file_creates_subdirectories(self):
        """测试写入文件时自动创建子目录"""
        content = "Content in subdirectory"
        filepath = "subdir/nested/deep.txt"

        result = self.file_tools.write_file(filepath, content)
        self.assertIn("成功写入文件", result)

        # 验证文件存在
        self.assertTrue(self.file_tools.file_exists(filepath))

        # 验证内容
        read_content = self.file_tools.read_file(filepath)
        self.assertEqual(content, read_content)

    def test_list_files_empty_directory(self):
        """测试列出空目录"""
        files = self.file_tools.list_files()
        self.assertEqual(files, [])

    def test_list_files_with_files(self):
        """测试列出包含文件的目录"""
        # 创建一些文件
        self.file_tools.write_file("file1.txt", "content1")
        self.file_tools.write_file("file2.py", "content2")
        self.file_tools.write_file("subdir/file3.txt", "content3")

        files = self.file_tools.list_files()
        self.assertEqual(len(files), 3)  # 根目录有2个文件和1个子目录
        self.assertIn("file1.txt", files)
        self.assertIn("file2.py", files)
        self.assertIn("subdir", files)

    def test_list_files_subdirectory(self):
        """测试列出子目录内容"""
        self.file_tools.write_file("subdir/file1.txt", "content1")
        self.file_tools.write_file("subdir/file2.txt", "content2")

        files = self.file_tools.list_files("subdir")
        self.assertEqual(len(files), 2)
        self.assertIn(os.path.join("subdir", "file1.txt"), files)
        self.assertIn(os.path.join("subdir", "file2.txt"), files)

    def test_search_files_by_pattern(self):
        """测试按模式搜索文件"""
        # 创建测试文件
        self.file_tools.write_file("test1.py", "content1")
        self.file_tools.write_file("test2.py", "content2")
        self.file_tools.write_file("main.py", "content3")
        self.file_tools.write_file("README.md", "content4")
        self.file_tools.write_file("subdir/test3.py", "content5")

        # 搜索所有.py文件
        py_files = self.file_tools.search_files("*.py")
        self.assertEqual(len(py_files), 4)
        self.assertIn("test1.py", py_files)
        self.assertIn("main.py", py_files)
        self.assertIn(os.path.join("subdir", "test3.py"), py_files)

        # 搜索test开头的文件
        test_files = self.file_tools.search_files("test*.py")
        self.assertEqual(len(test_files), 3)

    def test_search_files_in_subdirectory(self):
        """测试在子目录中搜索文件"""
        self.file_tools.write_file("subdir/file1.py", "content1")
        self.file_tools.write_file("subdir/file2.txt", "content2")
        self.file_tools.write_file("other/file3.py", "content3")

        files = self.file_tools.search_files("*.py", "subdir")
        self.assertEqual(len(files), 1)
        self.assertIn(os.path.join("subdir", "file1.py"), files)

    def test_file_exists(self):
        """测试检查文件是否存在"""
        self.assertFalse(self.file_tools.file_exists("test.txt"))

        self.file_tools.write_file("test.txt", "content")
        self.assertTrue(self.file_tools.file_exists("test.txt"))

    def test_delete_file(self):
        """测试删除文件"""
        self.file_tools.write_file("test.txt", "content")
        self.assertTrue(self.file_tools.file_exists("test.txt"))

        result = self.file_tools.delete_file("test.txt")
        self.assertIn("成功删除文件", result)
        self.assertFalse(self.file_tools.file_exists("test.txt"))

    def test_delete_nonexistent_file(self):
        """测试删除不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.file_tools.delete_file("nonexistent.txt")

    def test_create_directory(self):
        """测试创建目录"""
        result = self.file_tools.create_directory("new_dir")
        self.assertIn("成功创建目录", result)

        # 验证目录存在
        dir_path = Path(self.test_dir) / "new_dir"
        self.assertTrue(dir_path.exists())
        self.assertTrue(dir_path.is_dir())

    def test_create_nested_directory(self):
        """测试创建嵌套目录"""
        result = self.file_tools.create_directory("parent/child/grandchild")
        self.assertIn("成功创建目录", result)

        # 验证所有目录都存在
        dir_path = Path(self.test_dir) / "parent" / "child" / "grandchild"
        self.assertTrue(dir_path.exists())

    def test_resolve_path_security(self):
        """测试路径解析安全性 - 防止路径穿越攻击"""
        from pathlib import Path

        # 尝试访问workspace外的目录
        with self.assertRaises(ValueError):
            self.file_tools._resolve_path("../../../etc/passwd")

        with self.assertRaises(ValueError):
            self.file_tools._resolve_path("/etc/passwd")

    def test_write_file_with_unicode(self):
        """测试写入Unicode内容"""
        content = "你好，世界！\nこんにちは\nПривет мир"
        filepath = "unicode.txt"

        self.file_tools.write_file(filepath, content)
        read_content = self.file_tools.read_file(filepath)
        self.assertEqual(content, read_content)

    def test_list_nonexistent_directory(self):
        """测试列出不存在的目录"""
        with self.assertRaises(FileNotFoundError):
            self.file_tools.list_files("nonexistent_dir")

    def test_list_file_as_directory(self):
        """测试将文件作为目录列出"""
        self.file_tools.write_file("file.txt", "content")

        with self.assertRaises(ValueError):
            self.file_tools.list_files("file.txt")

    def test_get_tools(self):
        """测试获取所有工具方法"""
        tools = self.file_tools.get_tools()

        # 验证返回的是可调用对象
        for tool in tools:
            self.assertTrue(callable(tool))

        # 验证包含主要工具方法
        tool_names = {tool.__name__ for tool in tools}
        expected_tools = {
            "read_file", "write_file", "list_files",
            "search_files", "file_exists", "delete_file",
            "create_directory"
        }
        self.assertEqual(tool_names, expected_tools)


if __name__ == "__main__":
    unittest.main()
