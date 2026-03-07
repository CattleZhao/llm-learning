# src/vector_store.py
import os
import json
import numpy as np
from typing import List, Tuple, Dict, Any
from pathlib import Path
from embeddings import EmbeddingModel
from document_loader import Document

class VectorStore:
    """向量存储管理器 - 简化版实现"""

    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: str = "./data/chroma"
    ):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self._storage_file = self.persist_directory / f"{collection_name}.json"
        self._documents: List[Document] = []
        self._embeddings: List[List[float]] = []

        # 加载已有数据
        self._load()

    def add_documents(
        self,
        documents: List[Document],
        embeddings: EmbeddingModel
    ) -> List[str]:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表
            embeddings: 嵌入模型

        Returns:
            添加的文档ID列表
        """
        # 生成嵌入向量
        texts = [doc.page_content for doc in documents]
        embedding_vectors = embeddings.embed_documents(texts)

        # 添加到存储
        for doc, emb in zip(documents, embedding_vectors):
            doc_id = f"{doc.metadata.get('source', 'doc')}_{len(self._documents)}"
            doc.metadata['doc_id'] = doc_id

            self._documents.append(doc)
            self._embeddings.append(emb)

        # 持久化
        self._save()

        return [doc.metadata.get('doc_id') for doc in documents]

    def search(
        self,
        query: str,
        embeddings: EmbeddingModel,
        k: int = 4
    ) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            embeddings: 嵌入模型
            k: 返回结果数量

        Returns:
            匹配的文档列表
        """
        if not self._documents:
            return []

        # 嵌入查询
        query_embedding = embeddings.embed_query(query)

        # 计算相似度
        results_with_scores = self._search_with_score(
            query, embeddings, k
        )

        # 只返回文档
        return [doc for doc, _ in results_with_scores]

    def search_with_score(
        self,
        query: str,
        embeddings: EmbeddingModel,
        k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        带分数的相似度搜索

        Args:
            query: 查询文本
            embeddings: 嵌入模型
            k: 返回结果数量

        Returns:
            (文档, 相似度分数) 元组列表
        """
        if not self._documents:
            return []

        # 嵌入查询
        query_embedding = np.array(embeddings.embed_query(query))

        # 计算与所有文档的相似度
        similarities = []
        for doc_emb in self._embeddings:
            doc_emb = np.array(doc_emb)
            # 余弦相似度
            similarity = np.dot(query_embedding, doc_emb)
            similarities.append(similarity)

        # 获取top-k
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        results = []
        for idx in top_k_indices:
            results.append((
                self._documents[idx],
                float(similarities[idx])
            ))

        return results

    def _save(self):
        """保存到磁盘"""
        data = {
            'documents': [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }
                for doc in self._documents
            ],
            'embeddings': self._embeddings
        }

        with open(self._storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def _load(self):
        """从磁盘加载"""
        if not self._storage_file.exists():
            return

        try:
            with open(self._storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._documents = [
                Document(
                    page_content=item['content'],
                    metadata=item['metadata']
                )
                for item in data['documents']
            ]
            self._embeddings = data['embeddings']
        except Exception:
            pass

    def clear(self):
        """清空所有文档"""
        self._documents = []
        self._embeddings = []
        if self._storage_file.exists():
            self._storage_file.unlink()

    def count(self) -> int:
        """获取文档数量"""
        return len(self._documents)
