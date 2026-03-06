# src/text_splitter.py
from typing import List, Optional
from src.document_loader import Document

class DocumentSplitter:
    """文档分块器 - 支持多种分块策略"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separators: 分隔符列表
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 默认分隔符（按优先级）
        default_separators = ["\n\n", "\n", "。", "！", "？", ".", " ", ""]
        self.separators = separators or default_separators

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档

        Args:
            documents: 文档列表

        Returns:
            分割后的文档块列表
        """
        all_chunks = []

        for doc in documents:
            chunks = self.split_text(doc.page_content)

            for i, chunk_text in enumerate(chunks):
                # 复制元数据并添加块索引
                metadata = doc.metadata.copy()
                metadata["chunk_index"] = i

                all_chunks.append(Document(
                    page_content=chunk_text,
                    metadata=metadata
                ))

        return all_chunks

    def split_text(self, text: str) -> List[str]:
        """
        分割文本

        Args:
            text: 待分割的文本

        Returns:
            文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # 计算当前块的结束位置
            end = start + self.chunk_size

            # 如果不是最后一块，尝试在分隔符处分割
            if end < len(text):
                # 在候选范围内找最近的分隔符
                split_pos = self._find_best_split_position(text, start, end)

                if split_pos > start:
                    end = split_pos

            # 提取文本块
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # 移动到下一块，考虑重叠
            start = end - self.chunk_overlap

            # 确保至少有进展
            if start <= 0:
                start = end

        return chunks

    def _find_best_split_position(self, text: str, start: int, end: int) -> int:
        """
        在指定范围内找最佳分割位置

        Args:
            text: 完整文本
            start: 起始位置
            end: 结束位置

        Returns:
            最佳分割位置
        """
        # 从end往回找，在重叠范围内找分隔符
        search_start = max(start, end - self.chunk_overlap)
        search_text = text[search_start:end]

        for sep in self.separators:
            # 从后往前找分隔符
            pos = search_text.rfind(sep)
            if pos != -1:
                return search_start + pos + len(sep)

        # 没找到分隔符，直接在end处分割
        return end
