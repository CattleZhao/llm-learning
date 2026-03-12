"""
Markdown 文档加载器

使用 LlamaIndex 的 SimpleDirectoryReader 和 MarkdownReader
加载目录中的 Markdown 文档，并自动提取元数据。
"""
from pathlib import Path
from typing import List, Optional
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import MarkdownReader
from src.metadata.extractor import MetadataExtractor, DocumentMetadata


class MarkdownLoader:
    """Markdown 文档加载器，支持元数据提取"""

    def __init__(self, extract_metadata: bool = True):
        """
        初始化加载器

        Args:
            extract_metadata: 是否自动提取元数据
        """
        self.reader = MarkdownReader()
        self.extract_metadata = extract_metadata
        self.metadata_extractor = MetadataExtractor() if extract_metadata else None
        self._metadata_cache: Optional[dict] = None

    def load_documents(
        self,
        directory: str,
        recursive: bool = True,
        enrich_metadata: bool = True
    ) -> List:
        """
        从目录加载 Markdown 文档

        Args:
            directory: 文档目录路径
            recursive: 是否递归加载子目录
            enrich_metadata: 是否增强文档元数据

        Returns:
            Document 对象列表
        """
        # 加载文档
        loader = SimpleDirectoryReader(
            input_dir=directory,
            recursive=recursive,
            file_extractor={".md": self.reader}
        )
        documents = loader.load_data()

        # 提取和增强元数据
        if self.extract_metadata and enrich_metadata:
            self._enrich_documents_metadata(documents, directory)

        return documents

    def _enrich_documents_metadata(self, documents: List, directory: str):
        """增强文档元数据"""
        # 提取所有文件的元数据
        if self._metadata_cache is None:
            self._metadata_cache = self.metadata_extractor.extract_from_directory(directory)

        # 为每个文档添加元数据
        for doc in documents:
            # 获取文件路径
            file_path = doc.metadata.get('file_name', '')

            # 查找对应的元数据
            metadata = None
            for path, doc_metadata in self._metadata_cache.items():
                if file_path in path or path.endswith(file_path):
                    metadata = doc_metadata
                    break

            # 如果没有找到，尝试直接提取
            if metadata is None and Path(file_path).exists():
                metadata = self.metadata_extractor.extract_from_file(file_path)

            # 将元数据添加到文档
            if metadata:
                # 保留原有元数据
                existing_metadata = doc.metadata.copy()

                # 添加提取的元数据
                doc.metadata = {
                    **existing_metadata,
                    **self._metadata_to_dict(metadata),
                    # 确保文件名存在
                    'file_name': metadata.file_name,
                }

    def _metadata_to_dict(self, metadata: DocumentMetadata) -> dict:
        """将 DocumentMetadata 转换为字典"""
        return {
            'file_path': metadata.file_path,
            'file_type': metadata.file_type,
            'file_size': metadata.file_size,
            'title': metadata.title,
            'author': metadata.author,
            'category': metadata.category,
            'tags': metadata.tags,
            'created_date': metadata.created_date,
            'modified_date': metadata.modified_date,
            'year': metadata.year,
            'word_count': metadata.word_count,
            'char_count': metadata.char_count,
            **metadata.custom,
        }

    def get_available_metadata_fields(self, documents: List) -> set:
        """
        获取文档中所有可用的元数据字段

        Args:
            documents: 文档列表

        Returns:
            元数据字段名集合
        """
        fields = set()
        for doc in documents:
            fields.update(doc.metadata.keys())
        return fields

    def get_metadata_values(self, documents: List, field: str) -> List:
        """
        获取指定字段的所有唯一值

        Args:
            documents: 文档列表
            field: 元数据字段名

        Returns:
            该字段的所有唯一值列表
        """
        values = set()
        for doc in documents:
            value = doc.metadata.get(field)
            if value is not None:
                if isinstance(value, list):
                    values.update(value)
                else:
                    values.add(value)
        return sorted(list(values))
