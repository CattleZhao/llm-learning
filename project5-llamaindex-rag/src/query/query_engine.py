"""
RAG 查询引擎

提供基于向量索引的查询接口，支持重排序优化
"""
from typing import Optional, List
from src.config import get_settings
from src.indexes.vector_index import VectorIndexManager
from src.rerank.postprocessor import create_reranker_postprocessor
from llama_index.core import Settings


class RAGQueryEngine:
    """RAG 查询引擎"""

    def __init__(
        self,
        index=None,
        enable_rerank: bool = False,
        reranker_type: str = "keyword",
        compare_mode: bool = False
    ):
        """
        初始化查询引擎

        Args:
            index: VectorStoreIndex 实例，如果为 None 则需要后续设置
            enable_rerank: 是否启用重排序
            reranker_type: Reranker 类型 ("keyword" 或 "cohere")
            compare_mode: 对比模式（同时返回 rerank 前后结果）
        """
        self.settings = get_settings()
        self.index = index
        self.enable_rerank = enable_rerank
        self.reranker_type = reranker_type
        self.compare_mode = compare_mode
        self.query_engine = None
        self.baseline_query_engine = None  # 用于对比的无 rerank 版本
        if index:
            self._setup_query_engine()
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
        # 基础查询引擎（无 rerank）
        self.baseline_query_engine = self.index.as_query_engine(
            similarity_top_k=self.settings.top_k,
            llm=Settings.llm,
            verbose=False
        )

        # 带重排序的查询引擎
        if self.enable_rerank:
            # Rerank 需要先获取更多结果，然后再重排
            rerank_top_k = max(self.settings.top_k * 2, 10)
            postprocessor = create_reranker_postprocessor(
                reranker_type=self.reranker_type,
                top_n=self.settings.top_k
            )
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=rerank_top_k,
                node_postprocessors=[postprocessor],
                llm=Settings.llm,
                verbose=False
            )
        else:
            self.query_engine = self.baseline_query_engine

    def _extract_sources(self, response) -> List[dict]:
        """
        从响应中提取来源信息

        Args:
            response: LlamaIndex 查询响应

        Returns:
            来源信息列表
        """
        sources = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for node in response.source_nodes:
                metadata = node.metadata if hasattr(node, 'metadata') else {}
                sources.append({
                    "file_name": metadata.get('file_name', 'unknown'),
                    "score": node.score if hasattr(node, 'score') else 0
                })
        return sources

    def query(self, question: str) -> dict:
        """
        执行查询

        Args:
            question: 查询问题

        Returns:
            包含答案和来源的字典，对比模式下包含前后对比
        """
        if not self.query_engine:
            raise ValueError("Query engine not initialized. Please provide an index.")

        # 对比模式：同时获取两种结果
        if self.compare_mode and self.enable_rerank:
            # Baseline（无 rerank）
            baseline_response = self.baseline_query_engine.query(question)
            baseline_sources = self._extract_sources(baseline_response)

            # With Rerank
            rerank_response = self.query_engine.query(question)
            rerank_sources = self._extract_sources(rerank_response)

            return {
                "answer": str(rerank_response),
                "sources": rerank_sources,
                "compare": {
                    "baseline": {
                        "sources": baseline_sources,
                        "answer": str(baseline_response)
                    },
                    "reranked": {
                        "sources": rerank_sources,
                        "answer": str(rerank_response)
                    }
                }
            }

        # 正常模式
        response = self.query_engine.query(question)
        sources = self._extract_sources(response)

        return {
            "answer": str(response),
            "sources": sources,
            "rerank_enabled": self.enable_rerank
        }

    def set_index(self, index, enable_rerank: Optional[bool] = None):
        """
        设置索引并配置查询引擎

        Args:
            index: VectorStoreIndex 实例
            enable_rerank: 是否启用重排序（可选，覆盖原设置）
        """
        self.index = index
        if enable_rerank is not None:
            self.enable_rerank = enable_rerank
        self._setup_query_engine()

    def toggle_rerank(self, enabled: bool):
        """
        切换重排序状态

        Args:
            enabled: 是否启用重排序
        """
        self.enable_rerank = enabled
        if self.index:
            self._setup_query_engine()

    def toggle_compare_mode(self, enabled: bool):
        """
        切换对比模式

        Args:
            enabled: 是否启用对比模式
        """
        self.compare_mode = enabled
