"""
RAG 查询引擎

提供基于向量索引的查询接口，支持重排序优化和流式输出
"""
from typing import Optional, List, Generator, Dict, Any
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
        compare_mode: bool = False,
        streaming: bool = False
    ):
        """
        初始化查询引擎

        Args:
            index: VectorStoreIndex 实例，如果为 None 则需要后续设置
            enable_rerank: 是否启用重排序
            reranker_type: Reranker 类型 ("keyword" 或 "cohere")
            compare_mode: 对比模式（同时返回 rerank 前后结果）
            streaming: 是否启用流式输出
        """
        self.settings = get_settings()
        self.index = index
        self.enable_rerank = enable_rerank
        self.reranker_type = reranker_type
        self.compare_mode = compare_mode
        self.streaming = streaming
        self.query_engine = None
        self.baseline_query_engine = None  # 用于对比的无 rerank 版本
        if index:
            self._setup_query_engine()

    def _setup_query_engine(self):
        """配置查询引擎"""
        # 基础查询引擎（无 rerank）
        self.baseline_query_engine = self.index.as_query_engine(
            similarity_top_k=self.settings.top_k,
            llm=Settings.llm,
            streaming=self.streaming,
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
                streaming=self.streaming,
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
        执行查询（非流式）

        Args:
            question: 查询问题

        Returns:
            包含答案和来源的字典，对比模式下包含前后对比
        """
        if not self.query_engine:
            raise ValueError("Query engine not initialized. Please provide an index.")

        # 如果启用了流式模式，切换到非流式
        if self.streaming:
            return self._query_non_stream(question)

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

    def _query_non_stream(self, question: str) -> dict:
        """
        非流式查询（当 streaming=True 时调用）

        Args:
            question: 查询问题

        Returns:
            包含答案和来源的字典
        """
        # 临时禁用流式模式执行查询
        was_streaming = self.streaming
        self.streaming = False
        self._setup_query_engine()

        result = self.query(question)

        # 恢复流式模式
        self.streaming = was_streaming
        self._setup_query_engine()

        return result

    def stream_query(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        执行流式查询

        Args:
            question: 查询问题

        Yields:
            包含增量文本和元数据的字典
            {
                "text": "增量文本",
                "sources": [...],  # 最后一次返回
                "done": False      # 是否完成
            }
        """
        if not self.query_engine:
            raise ValueError("Query engine not initialized. Please provide an index.")

        # 切换到流式模式
        was_streaming = self.streaming
        if not was_streaming:
            self.streaming = True
            self._setup_query_engine()

        try:
            # 执行流式查询
            streaming_response = self.query_engine.query(question)

            # 提取来源（流式响应也包含 source_nodes）
            sources = self._extract_sources(streaming_response)

            # 流式返回文本
            accumulated_text = ""
            for chunk in streaming_response.response_gen:
                accumulated_text += chunk
                yield {
                    "text": chunk,
                    "accumulated": accumulated_text,
                    "done": False
                }

            # 最后返回来源信息
            yield {
                "text": "",
                "accumulated": accumulated_text,
                "sources": sources,
                "done": True,
                "rerank_enabled": self.enable_rerank
            }

        finally:
            # 恢复原设置
            if not was_streaming:
                self.streaming = False
                self._setup_query_engine()

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

    def toggle_streaming(self, enabled: bool):
        """
        切换流式输出模式

        Args:
            enabled: 是否启用流式输出
        """
        self.streaming = enabled
        if self.index:
            self._setup_query_engine()
