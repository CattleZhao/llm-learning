"""
Cohere API 重排序器

使用 Cohere Rerank API 进行专业级重排序
需要 API key: https://cohere.com/rerank
"""
from typing import List, Optional
import os
from llama_index.core.schema import NodeWithScore
from src.rerank.base import BaseReranker

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


class CohereReranker(BaseReranker):
    """
    Cohere API 重排序器

    使用 Cohere 的 Rerank API 提供高质量的重排序服务
    需要设置 COHERE_API_KEY 环境变量
    """

    def __init__(
        self,
        top_n: int = 3,
        api_key: Optional[str] = None,
        model: str = "rerank-v3"
    ):
        """
        初始化 Cohere 重排序器

        Args:
            top_n: 最终返回的节点数量
            api_key: Cohere API key，如果为 None 则从环境变量读取
            model: Rerank 模型名称 (rerank-v3, rerank-multilingual-v3.0)
        """
        super().__init__(top_n=top_n)

        if not COHERE_AVAILABLE:
            raise ImportError(
                "Cohere SDK not installed. "
                "Install with: pip install cohere"
            )

        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "COHERE_API_KEY not found. "
                "Set it as environment variable or pass to constructor."
            )

        self.model = model
        self._client = cohere.Client(self.api_key)

    def rerank(
        self,
        query: str,
        nodes: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """
        使用 Cohere API 执行重排序

        Args:
            query: 原始查询
            nodes: 检索到的节点列表

        Returns:
            重排序后的节点列表
        """
        if not nodes:
            return []

        # 准备文档文本
        documents = [node.node.get_content() for node in nodes]

        # 调用 Cohere Rerank API
        try:
            response = self._client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=len(documents),  # 获取全部排序结果
                return_documents=False
            )
        except Exception as e:
            print(f"[CohereReranker] API error: {e}")
            # 失败时回退到原排序
            return self._sort_and_slice(nodes)

        # 根据 API 结果重新排序节点
        reranked_nodes = []
        node_map = {i: node for i, node in enumerate(nodes)}

        for result in response.results:
            original_index = result.index
            relevance_score = result.relevance_score

            if original_index in node_map:
                original_node = node_map[original_index]
                reranked_nodes.append(
                    NodeWithScore(
                        node=original_node.node,
                        score=relevance_score
                    )
                )

        # 返回 top_n
        return reranked_nodes[:self.top_n]

    def __repr__(self) -> str:
        api_key_preview = f"{self.api_key[:8]}..." if self.api_key else "None"
        return (
            f"CohereReranker(top_n={self.top_n}, "
            f"model={self.model}, "
            f"api_key={api_key_preview})"
        )
