"""
关键词重排序器

基于关键词匹配度进行重排序
无需外部模型，适合学习和原型开发
"""
import re
from typing import List, Set
from llama_index.core.schema import NodeWithScore
from src.rerank.base import BaseReranker


class KeywordReranker(BaseReranker):
    """
    关键词重排序器

    通过分析查询中的关键词，计算节点文本中关键词的出现频率和密度，
    结合原始向量相似度进行综合评分
    """

    def __init__(
        self,
        top_n: int = 3,
        keyword_weight: float = 0.3,
        original_weight: float = 0.7,
        min_word_length: int = 2
    ):
        """
        初始化关键词重排序器

        Args:
            top_n: 最终返回的节点数量
            keyword_weight: 关键词评分权重 (0-1)
            original_weight: 原始向量相似度权重 (0-1)
            min_word_length: 最小词长（忽略更短的词）
        """
        super().__init__(top_n=top_n)
        if not (0 <= keyword_weight <= 1 and 0 <= original_weight <= 1):
            raise ValueError("Weights must be between 0 and 1")
        if abs(keyword_weight + original_weight - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")

        self.keyword_weight = keyword_weight
        self.original_weight = original_weight
        self.min_word_length = min_word_length

    def _extract_keywords(self, query: str) -> Set[str]:
        """
        从查询中提取关键词

        Args:
            query: 查询文本

        Returns:
            关键词集合
        """
        # 转小写，分词
        words = re.findall(r'\w+', query.lower())

        # 过滤停用词和短词
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must',
            '的', '了', '是', '在', '有', '和', '与', '或', '但', '不', '也',
            '就', '都', '而', '及', '等', '这', '那', '什么', '哪些', '如何'
        }

        keywords = {
            word for word in words
            if len(word) >= self.min_word_length and word not in stopwords
        }

        return keywords

    def _calculate_keyword_score(
        self,
        text: str,
        keywords: Set[str]
    ) -> float:
        """
        计算文本的关键词匹配分数

        Args:
            text: 文本内容
            keywords: 关键词集合

        Returns:
            关键词分数 (0-1)
        """
        if not keywords:
            return 0.0

        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)

        if not words:
            return 0.0

        # 计算匹配的关键词数量
        matched_count = sum(1 for word in words if word in keywords)
        unique_keywords = len(keywords)

        # 基础分数：匹配率
        match_rate = min(matched_count / unique_keywords, 1.0)

        # 额外加分：关键词密度（匹配词在总词数中的占比）
        density = matched_count / len(words) if words else 0

        # 综合分数
        return match_rate * 0.7 + density * 0.3

    def rerank(
        self,
        query: str,
        nodes: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """
        执行关键词重排序

        Args:
            query: 原始查询
            nodes: 检索到的节点列表

        Returns:
            重排序后的节点列表
        """
        # 提取查询关键词
        keywords = self._extract_keywords(query)

        if not keywords:
            # 没有有效关键词，保持原排序
            return self._sort_and_slice(nodes)

        # 为每个节点重新计算分数
        reranked_nodes = []
        for node in nodes:
            # 获取原始分数
            original_score = node.score or 0

            # 计算关键词分数
            text = node.node.get_content()
            keyword_score = self._calculate_keyword_score(text, keywords)

            # 加权合并
            new_score = (
                original_score * self.original_weight +
                keyword_score * self.keyword_weight
            )

            # 创建新的节点对象（更新分数）
            reranked_nodes.append(
                NodeWithScore(
                    node=node.node,
                    score=new_score
                )
            )

        # 排序并返回 top_n
        return self._sort_and_slice(reranked_nodes)

    def __repr__(self) -> str:
        return (
            f"KeywordReranker(top_n={self.top_n}, "
            f"keyword_weight={self.keyword_weight}, "
            f"original_weight={self.original_weight})"
        )
