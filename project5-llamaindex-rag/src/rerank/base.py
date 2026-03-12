"""
Reranker 基类

定义重排序器的统一接口
"""
from abc import ABC, abstractmethod
from typing import List
from llama_index.core.schema import NodeWithScore


class BaseReranker(ABC):
    """
    重排序器基类

    所有 Reranker 实现都需要继承此类并实现 rerank 方法
    """

    def __init__(self, top_n: int = 3):
        """
        初始化 Reranker

        Args:
            top_n: 最终返回的节点数量
        """
        self.top_n = top_n

    @abstractmethod
    def rerank(
        self,
        query: str,
        nodes: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """
        对检索结果重新排序

        Args:
            query: 原始查询
            nodes: 检索到的节点列表（已按相似度排序）

        Returns:
            重新排序后的节点列表，只返回 top_n 个
        """
        pass

    def _sort_and_slice(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """
        按分数排序并切片

        Args:
            nodes: 节点列表

        Returns:
            排序并切片后的节点列表
        """
        # 按分数降序排序
        sorted_nodes = sorted(nodes, key=lambda x: x.score or 0, reverse=True)
        # 返回 top_n
        return sorted_nodes[:self.top_n]
