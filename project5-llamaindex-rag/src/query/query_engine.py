"""
RAG 查询引擎

提供基于向量索引的查询接口
"""
from src.config import get_settings
from src.indexes.vector_index import VectorIndexManager
from llama_index.core import Settings


class RAGQueryEngine:
    """RAG 查询引擎"""

    def __init__(self, index=None):
        """
        初始化查询引擎

        Args:
            index: VectorStoreIndex 实例，如果为 None 则需要后续设置
        """
        self.settings = get_settings()
        self.index = index
        self.query_engine = None
        if index:
            self._setup_query_engine()

    def _setup_query_engine(self):
        """配置查询引擎"""
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=self.settings.top_k,
            llm=Settings.llm,  # 显式使用配置的 LLM
            verbose=True
        )

    def query(self, question: str) -> dict:
        """
        执行查询

        Args:
            question: 查询问题

        Returns:
            包含答案和来源的字典
        """
        if not self.query_engine:
            raise ValueError("Query engine not initialized. Please provide an index.")

        response = self.query_engine.query(question)

        # 提取来源信息
        sources = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for node in response.source_nodes:
                metadata = node.metadata if hasattr(node, 'metadata') else {}
                file_name = metadata.get('file_name', 'unknown')
                sources.append(file_name)

        return {
            "answer": str(response),
            "sources": sources
        }

    def set_index(self, index):
        """
        设置索引并配置查询引擎

        Args:
            index: VectorStoreIndex 实例
        """
        self.index = index
        self._setup_query_engine()
