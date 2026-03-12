#!/usr/bin/env python3
"""
元数据过滤演示脚本

展示如何使用元数据过滤功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine
from src.metadata.filters import MetadataFilterBuilder, CommonFilters


def demo_metadata_extraction():
    """演示元数据提取"""
    print("=" * 60)
    print("演示 1: 元数据提取")
    print("=" * 60)

    settings = get_settings()
    loader = MarkdownLoader()

    # 加载文档
    print("\n正在加载文档...")
    documents = loader.load_documents(settings.docs_dir)
    print(f"加载了 {len(documents)} 个文档")

    # 显示可用元数据字段
    fields = loader.get_available_metadata_fields(documents)
    print(f"\n可用元数据字段: {sorted(fields)}")

    # 显示每个文档的元数据
    print("\n文档元数据:")
    for i, doc in enumerate(documents, 1):
        print(f"\n{i}. {doc.metadata.get('file_name', 'unknown')}")
        metadata = {k: v for k, v in doc.metadata.items()
                   if k not in ['file_path', 'file_size', 'word_count', 'char_count']}
        for key, value in metadata.items():
            if value:
                print(f"   {key}: {value}")


def demo_filter_builder():
    """演示过滤器构建器"""
    print("\n" + "=" * 60)
    print("演示 2: 过滤器构建器")
    print("=" * 60)

    # 使用流式 API 构建过滤器
    filter_builder = (MetadataFilterBuilder()
                     .eq("category", "人工智能")
                     .gte("year", 2024))

    filters = filter_builder.build()
    print(f"\n构建的过滤器: {filters}")

    # 使用预设过滤器
    print("\n预设过滤器示例:")
    print(f"- 按分类: {CommonFilters.by_category('编程').to_dict()}")
    print(f"- 按作者: {CommonFilters.by_author('AI 助手').to_dict()}")
    print(f"- 最近两年: {CommonFilters.recent_years(2).to_dict()}")


def demo_metadata_filtering():
    """演示元数据过滤查询"""
    print("\n" + "=" * 60)
    print("演示 3: 元数据过滤查询")
    print("=" * 60)

    try:
        settings = get_settings()
        loader = MarkdownLoader()

        # 加载文档并创建索引
        print("\n正在加载文档...")
        documents = loader.load_documents(settings.docs_dir)
        print(f"加载了 {len(documents)} 个文档")

        print("正在创建索引...")
        index_manager = VectorIndexManager()
        index = index_manager.create_index(documents)

        question = "文档中介绍了哪些主要内容？"

        # 不使用过滤
        print(f"\n--- 不使用过滤 ---")
        print(f"问题: {question}")
        engine_no_filter = RAGQueryEngine(index=index)
        result = engine_no_filter.query(question)
        print(f"答案: {result['answer'][:150]}...")
        print(f"来源: {[s['file_name'] for s in result['sources']]}")

        # 使用过滤（按分类）
        print(f"\n--- 使用过滤 (category = '人工智能') ---")
        filter_builder = MetadataFilterBuilder().eq("category", "人工智能")
        engine_with_filter = RAGQueryEngine(
            index=index,
            metadata_filters=filter_builder.build()
        )
        result = engine_with_filter.query(question)
        print(f"答案: {result['answer'][:150]}...")
        print(f"来源: {[s['file_name'] for s in result['sources']]}")

        # 使用多个过滤条件
        print(f"\n--- 使用多个过滤条件 ---")
        filter_builder = (MetadataFilterBuilder()
                         .eq("category", "编程语言")
                         .contains("tags", "Python"))
        engine_multi_filter = RAGQueryEngine(
            index=index,
            metadata_filters=filter_builder.build()
        )
        result = engine_multi_filter.query(question)
        print(f"答案: {result['answer'][:150]}...")
        print(f"来源: {[s['file_name'] for s in result['sources']]}")

    except Exception as e:
        print(f"\n错误: {e}")
        print("提示: 请确保已配置 .env 文件并加载了文档")


def main():
    """主函数"""
    print("\n🦙 LlamaIndex RAG - 元数据过滤演示\n")

    # 演示 1: 元数据提取
    demo_metadata_extraction()

    # 演示 2: 过滤器构建器
    demo_filter_builder()

    # 演示 3: 元数据过滤查询（需要 API）
    # demo_metadata_filtering()  # 取消注释以运行

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n提示: 运行 'streamlit run app/web.py' 体验 Web 界面的元数据过滤")


if __name__ == "__main__":
    main()
