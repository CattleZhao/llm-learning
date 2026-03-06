# src/document_loader.py
import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Document:
    """文档数据类"""
    page_content: str
    metadata: Dict[str, Any]

class DocumentLoader:
    """文档加载器 - 支持多种格式"""

    SUPPORTED_FORMATS = {
        '.txt': 'text',
        '.md': 'markdown',
    }

    def __init__(self):
        self.loaders = {
            'text': self._load_text,
            'markdown': self._load_markdown,
        }

    def load_file(self, file_path: str) -> List[Document]:
        """
        加载文档

        Args:
            file_path: 文档路径

        Returns:
            文档列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的格式
        """
        path = Path(file_path)

        # 先检查格式
        ext = path.suffix.lower()

        if ext not in self.SUPPORTED_FORMATS:
            supported = ', '.join(self.SUPPORTED_FORMATS.keys())
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported formats: {supported}"
            )

        # 再检查文件是否存在
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        loader_type = self.SUPPORTED_FORMATS[ext]
        loader_func = self.loaders[loader_type]

        content = loader_func(str(path))

        return [Document(
            page_content=content,
            metadata={"source": path.name}
        )]

    def _load_text(self, file_path: str) -> str:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_markdown(self, file_path: str) -> str:
        """加载Markdown文件"""
        return self._load_text(file_path)  # Markdown也是文本

    def is_supported(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
