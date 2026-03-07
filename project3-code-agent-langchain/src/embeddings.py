# src/embeddings.py
import hashlib
import numpy as np
from typing import List

class EmbeddingModel:
    """
    文本嵌入模型 - 简化版实现

    注意：这是用于学习的简化实现
    生产环境建议使用：
    - sentence-transformers（本地模型）
    - OpenAI Embeddings API
    - 或其他专业embedding服务
    """

    def __init__(self, dimension: int = 384):
        """
        初始化嵌入模型

        Args:
            dimension: 向量维度（默认384，与paraphrase-multilingual-MiniLM-L12一致）
        """
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单段文本

        Args:
            text: 待嵌入的文本

        Returns:
            向量表示
        """
        return self._text_to_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文本

        Args:
            texts: 待嵌入的文本列表

        Returns:
            向量列表
        """
        return [self._text_to_vector(text) for text in texts]

    def _text_to_vector(self, text: str) -> List[float]:
        """
        将文本转换为向量（简化实现）

        这是一个用于学习的简单实现：
        1. 对文本进行hash
        2. 转换为指定维度的向量

        实际生产环境应使用专业的embedding模型如：
        - sentence-transformers
        - OpenAI text-embedding-3
        """
        # 创建文本的多个hash特征
        features = []

        # 使用不同位置的hash来创建更多特征
        for i in range(self.dimension):
            # 对每个位置，用不同的盐值进行hash
            salt = f"{text}_{i}".encode('utf-8')
            hash_value = int(hashlib.sha256(salt).hexdigest(), 16)

            # 转换为[-1, 1]范围的浮点数
            normalized = (hash_value % 10000) / 5000.0 - 1.0
            features.append(normalized)

        # 归一化向量（使其长度为1）
        vector = np.array(features)
        norm = np.linalg.norm(vector)

        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    @property
    def dimension_size(self) -> int:
        """获取向量维度"""
        return self.dimension
