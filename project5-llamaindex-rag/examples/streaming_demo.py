#!/usr/bin/env python3
"""
流式输出演示脚本

展示如何使用流式查询功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine


def demo_streaming():
    """演示流式查询"""
    print("=" * 60)
    print("演示: 流式查询 vs 非流式查询")
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

        # 非流式查询
        print("\n" + "-" * 40)
        print("【非流式查询】")
        print("-" * 40)
        engine_non_stream = RAGQueryEngine(index=index, streaming=False)
        question = "Python 编程的特点是什么？"
        print(f"问题: {question}\n")
        print("等待响应...\n")
        result = engine_non_stream.query(question)
        print(result["answer"][:200] + "...")

        # 流式查询
        print("\n" + "-" * 40)
        print("【流式查询】")
        print("-" * 40)
        engine_stream = RAGQueryEngine(index=index, streaming=True)
        print(f"问题: {question}\n")
        print("实时响应:\n")

        accumulated = ""
        for chunk in engine_stream.stream_query(question):
            if chunk.get("text"):
                print(chunk["text"], end="", flush=True)
                accumulated += chunk["text"]

            if chunk.get("done"):
                print("\n\n流式查询完成！")
                print(f"来源: {[s['file_name'] for s in chunk.get('sources', [])]}")

        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n提示: 运行 'streamlit run app/web.py' 体验 Web 界面的流式输出")

    except Exception as e:
        print(f"\n错误: {e}")
        print("提示: 请确保已配置 .env 文件并加载了文档")


def demo_streaming_api():
    """演示流式 API 的使用方式"""
    print("\n" + "=" * 60)
    print("流式查询 API 使用示例")
    print("=" * 60)

    print("""
# 创建启用流式的查询引擎
engine = RAGQueryEngine(index=index, streaming=True)

# 方式1: 逐块处理
for chunk in engine.stream_query("你的问题"):
    if chunk.get("text"):
        # 处理每个文本块
        print(chunk["text"], end="")

    if chunk.get("done"):
        # 查询完成，获取来源
        sources = chunk.get("sources", [])


# 方式2: 获取累积文本
accumulated_text = ""
for chunk in engine.stream_query("你的问题"):
    if chunk.get("accumulated"):
        accumulated_text = chunk["accumulated"]

    if chunk.get("done"):
        print(f"完整答案: {accumulated_text}")
        print(f"来源: {chunk.get('sources', [])}")
    """)


if __name__ == "__main__":
    demo_streaming_api()
    demo_streaming()
