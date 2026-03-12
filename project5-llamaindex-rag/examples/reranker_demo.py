#!/usr/bin/env python3
"""
Reranker 演示脚本

展示如何使用重排序功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine
from src.rerank.keyword_reranker import KeywordReranker
from src.rerank.base import BaseReranker
from llama_index.core.schema import NodeWithScore, TextNode


def demo_reranker_direct():
    """演示直接使用 Reranker"""
    print("=" * 60)
    print("演示 1: 直接使用 KeywordReranker")
    print("=" * 60)

    # 创建测试节点
    nodes = [
        NodeWithScore(
            node=TextNode(text="Python 是一种高级编程语言"),
            score=0.85
        ),
        NodeWithScore(
            node=TextNode(text="Python 编程教程：从入门到精通"),
            score=0.70
        ),
        NodeWithScore(
            node=TextNode(text="机器学习是人工智能的分支"),
            score=0.60
        ),
        NodeWithScore(
            node=TextNode(text="Python 在机器学习领域应用广泛，有 TensorFlow 和 PyTorch"),
            score=0.65
        ),
    ]

    query = "Python 机器学习教程"

    # 创建 Reranker
    reranker = KeywordReranker(top_n=2)

    # 执行重排序
    print(f"\n查询: {query}")
    print("\n原始排序:")
    for i, node in enumerate(nodes, 1):
        print(f"  {i}. [{node.score:.2f}] {node.node.get_content()[:50]}...")

    reranked = reranker.rerank(query, nodes)

    print("\n重排序后 (Top 2):")
    for i, node in enumerate(reranked, 1):
        print(f"  {i}. [{node.score:.2f}] {node.node.get_content()[:50]}...")


def demo_query_engine_with_rerank():
    """演示在查询引擎中使用 Reranker"""
    print("\n" + "=" * 60)
    print("演示 2: 查询引擎中使用 Reranker")
    print("=" * 60)

    try:
        settings = get_settings()
        loader = MarkdownLoader()

        # 加载文档
        print("\n正在加载文档...")
        documents = loader.load_documents(settings.docs_dir)
        print(f"加载了 {len(documents)} 个文档")

        # 创建索引
        print("正在创建索引...")
        index_manager = VectorIndexManager()
        index = index_manager.create_index(documents)

        # 不使用 Reranker
        print("\n--- 不使用 Reranker ---")
        engine_baseline = RAGQueryEngine(index=index, enable_rerank=False)
        result_baseline = engine_baseline.query("Python 编程的特点是什么？")
        print(f"答案: {result_baseline['answer'][:200]}...")
        print(f"来源: {[s['file_name'] if isinstance(s, dict) else s for s in result_baseline['sources']]}")

        # 使用 Reranker
        print("\n--- 使用 Reranker (Keyword) ---")
        engine_reranked = RAGQueryEngine(
            index=index,
            enable_rerank=True,
            reranker_type="keyword"
        )
        result_reranked = engine_reranked.query("Python 编程的特点是什么？")
        print(f"答案: {result_reranked['answer'][:200]}...")
        print(f"来源: {[s['file_name'] if isinstance(s, dict) else s for s in result_reranked['sources']]}")

        # 对比模式
        print("\n--- 对比模式 ---")
        engine_compare = RAGQueryEngine(
            index=index,
            enable_rerank=True,
            compare_mode=True
        )
        result_compare = engine_compare.query("Python 编程的特点是什么？")

        if "compare" in result_compare:
            baseline_sources = [s['file_name'] for s in result_compare['compare']['baseline']['sources']]
            reranked_sources = [s['file_name'] for s in result_compare['compare']['reranked']['sources']]
            print(f"Baseline 来源: {baseline_sources}")
            print(f"Reranked 来源: {reranked_sources}")

    except Exception as e:
        print(f"\n错误: {e}")
        print("提示: 请确保已配置 .env 文件并加载了文档")


def demo_custom_reranker():
    """演示如何创建自定义 Reranker"""
    print("\n" + "=" * 60)
    print("演示 3: 创建自定义 Reranker")
    print("=" * 60)

    from src.rerank.base import BaseReranker

    class SimpleLengthReranker(BaseReranker):
        """简单示例：按文本长度重排序（较长的文本优先）"""

        def rerank(self, query: str, nodes):
            # 按文本长度降序排序
            sorted_nodes = sorted(
                nodes,
                key=lambda x: len(x.node.get_content()),
                reverse=True
            )
            return sorted_nodes[:self.top_n]

    # 使用自定义 Reranker
    nodes = [
        NodeWithScore(node=TextNode(text="短文本"), score=0.9),
        NodeWithScore(node=TextNode(text="中等长度的文本内容"), score=0.7),
        NodeWithScore(node=TextNode(text="这是一个非常非常长的文本内容，包含更多的详细信息"), score=0.5),
    ]

    custom_reranker = SimpleLengthReranker(top_n=2)
    result = custom_reranker.rerank("test", nodes)

    print("\n按文本长度重排序:")
    for i, node in enumerate(result, 1):
        content = node.node.get_content()
        print(f"  {i}. [{len(content)} 字符] {content}")


def main():
    """主函数"""
    print("\n🦙 LlamaIndex RAG - Reranker 功能演示\n")

    # 演示 1: 直接使用 Reranker
    demo_reranker_direct()

    # 演示 2: 在查询引擎中使用
    # demo_query_engine_with_rerank()  # 取消注释以运行

    # 演示 3: 自定义 Reranker
    demo_custom_reranker()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
