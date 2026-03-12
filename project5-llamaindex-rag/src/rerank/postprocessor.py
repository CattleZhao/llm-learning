"""
LlamaIndex 节点后处理器适配器

将自定义 Reranker 适配为 LlamaIndex 的 NodePostprocessor
"""
from typing import List, Optional, Any
from llama_index.core.schema import NodeWithScore
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from src.rerank.base import BaseReranker
from src.rerank.keyword_reranker import KeywordReranker
from src.rerank.cohere_reranker import CohereReranker


class RerankerPostprocessor(BaseNodePostprocessor):
    """
    Reranker 后处理器适配器

    将自定义的 BaseReranker 适配为 LlamaIndex 的 NodePostprocessor
    """

    def __init__(self, reranker: BaseReranker):
        """
        初始化后处理器

        Args:
            reranker: BaseReranker 实例
        """
        self.reranker = reranker

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[Any] = None
    ) -> List[NodeWithScore]:
        """
        后处理节点（重排序）

        Args:
            nodes: 要处理的节点列表
            query_bundle: 查询信息（包含 query_str）

        Returns:
            重排序后的节点列表
        """
        query_str = ""
        if query_bundle and hasattr(query_bundle, 'query_str'):
            query_str = query_bundle.query_str
        elif query_bundle and isinstance(query_bundle, str):
            query_str = query_bundle

        return self.reranker.rerank(query_str, nodes)


def create_reranker_postprocessor(
    reranker_type: str = "keyword",
    top_n: int = 3,
    **kwargs
) -> RerankerPostprocessor:
    """
    创建 Reranker 后处理器的工厂函数

    Args:
        reranker_type: Reranker 类型 ("keyword" 或 "cohere")
        top_n: 最终返回的节点数量
        **kwargs: 传递给具体 Reranker 的额外参数

    Returns:
        RerankerPostprocessor 实例

    Examples:
        >>> # 使用关键词重排序
        >>> postprocessor = create_reranker_postprocessor("keyword", top_n=3)
        >>>
        >>> # 使用 Cohere 重排序
        >>> postprocessor = create_reranker_postprocessor(
        ...     "cohere",
        ...     top_n=3,
        ...     api_key="your-api-key"
        ... )
    """
    if reranker_type == "keyword":
        reranker = KeywordReranker(top_n=top_n, **kwargs)
    elif reranker_type == "cohere":
        reranker = CohereReranker(top_n=top_n, **kwargs)
    else:
        raise ValueError(
            f"Unknown reranker type: {reranker_type}. "
            f"Use 'keyword' or 'cohere'."
        )

    return RerankerPostprocessor(reranker)
