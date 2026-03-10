"""
Markdown 文档加载器

使用 LlamaIndex 的 SimpleDirectoryReader 和 MarkdownReader
加载目录中的 Markdown 文档。
"""
from pathlib import Path
from typing import List
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import MarkdownReader


class MarkdownLoader:
    """Markdown 文档加载器"""

    def __init__(self):
        """初始化加载器"""
        self.reader = MarkdownReader()

    def load_documents(self, directory: str, recursive: bool = True) -> List:
        """
        从目录加载 Markdown 文档

        Args:
            directory: 文档目录路径
            recursive: 是否递归加载子目录

        Returns:
            Document 对象列表
        """
        loader = SimpleDirectoryReader(
            input_dir=directory,
            recursive=recursive,
            file_extractor={".md": self.reader}
        )
        return loader.load_data()
