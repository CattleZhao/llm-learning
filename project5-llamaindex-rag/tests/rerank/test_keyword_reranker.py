"""
关键词重排序器测试
"""
import pytest
from llama_index.core.schema import NodeWithScore, TextNode, Document
from src.rerank.keyword_reranker import KeywordReranker


class TestKeywordReranker:
    """关键词重排序器测试类"""

    def test_extract_keywords(self):
        """测试关键词提取"""
        reranker = KeywordReranker(top_n=3)

        # 中文查询
        query = "什么是机器学习和深度学习？"
        keywords = reranker._extract_keywords(query)
        assert "机器学习" in keywords
        assert "深度学习" in keywords

        # 英文查询
        query = "What is machine learning and deep learning?"
        keywords = reranker._extract_keywords(query)
        assert "machine" in keywords
        assert "learning" in keywords
        assert "deep" in keywords

    def test_calculate_keyword_score(self):
        """测试关键词分数计算"""
        reranker = KeywordReranker(top_n=3)
        keywords = {"python", "编程", "代码"}

        # 高匹配文本
        high_match = "Python 是一种流行的编程语言，用于编写代码"
        score1 = reranker._calculate_keyword_score(high_match, keywords)
        assert score1 > 0.5

        # 低匹配文本
        low_match = "这是一篇关于天气的文章"
        score2 = reranker._calculate_keyword_score(low_match, keywords)
        assert score2 < 0.3

    def test_rerank_basic(self):
        """测试基本重排序功能"""
        reranker = KeywordReranker(top_n=2)

        # 创建测试节点
        nodes = [
            NodeWithScore(
                node=TextNode(text="Python 是一种编程语言"),
                score=0.7
            ),
            NodeWithScore(
                node=TextNode(text="Python 编程教程：从入门到精通"),
                score=0.6
            ),
            NodeWithScore(
                node=TextNode(text="今天天气不错"),
                score=0.8
            ),
        ]

        query = "Python 编程教程"
        reranked = reranker.rerank(query, nodes)

        # 应该返回 2 个节点
        assert len(reranked) == 2

        # 第一个应该是匹配度最高的（包含编程和教程关键词）
        assert "编程" in reranked[0].node.get_content() or "Python" in reranked[0].node.get_content()

    def test_rerank_with_empty_nodes(self):
        """测试空节点列表"""
        reranker = KeywordReranker(top_n=3)
        result = reranker.rerank("test query", [])
        assert result == []

    def test_top_n_slicing(self):
        """测试 top_n 切片"""
        reranker = KeywordReranker(top_n=2)

        nodes = [
            NodeWithScore(node=TextNode(text=f"Content {i}"), score=0.5)
            for i in range(5)
        ]

        result = reranker.rerank("test", nodes)
        assert len(result) == 2


@pytest.fixture
def sample_nodes():
    """创建示例节点用于测试"""
    return [
        NodeWithScore(
            node=TextNode(
                text="Python 是一种高级编程语言，广泛用于 Web 开发和数据科学",
                metadata={"file_name": "python_intro.md"}
            ),
            score=0.85
        ),
        NodeWithScore(
            node=TextNode(
                text="机器学习是人工智能的一个分支",
                metadata={"file_name": "ml_basics.md"}
            ),
            score=0.75
        ),
        NodeWithScore(
            node=TextNode(
                text="Python 在机器学习领域有丰富的库，如 TensorFlow 和 PyTorch",
                metadata={"file_name": "python_ml.md"}
            ),
            score=0.70
        ),
        NodeWithScore(
            node=TextNode(
                text="今天天气晴朗，适合外出游玩",
                metadata={"file_name": "weather.md"}
            ),
            score=0.60
        ),
    ]


def test_reranking_improves_relevance(sample_nodes):
    """
    集成测试：验证重排序能提高相关性

    当查询 "Python 机器学习" 时：
    - 原始最高分是 python_intro.md (0.85)
    - 但 python_ml.md 更相关（同时包含 Python 和机器学习）
    - 重排序后 python_ml.md 应该排名上升
    """
    reranker = KeywordReranker(top_n=2, keyword_weight=0.5, original_weight=0.5)

    query = "Python 机器学习"
    reranked = reranker.rerank(query, sample_nodes)

    # 验证返回的是最相关的文档
    contents = [node.node.get_content() for node in reranked]
    assert any("Python" in c and "机器学习" in c for c in contents)


def test_reranker_preserves_metadata(sample_nodes):
    """测试重排序保留元数据"""
    reranker = KeywordReranker(top_n=2)

    query = "Python 编程"
    reranked = reranker.rerank(query, sample_nodes)

    # 验证元数据被保留
    for node in reranked:
        assert hasattr(node.node, 'metadata')
        assert 'file_name' in node.node.metadata
