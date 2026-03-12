"""
Streamlit Web Interface for LlamaIndex RAG

提供基于 Streamlit 的 Web UI，用于文档管理和问答
"""
import streamlit as st
from pathlib import Path
from typing import Dict, List
from src.config import get_settings
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine
from src.metadata.filters import MetadataFilterBuilder

# 页面配置
st.set_page_config(
    page_title="LlamaIndex RAG",
    page_icon="🦙",
    layout="wide"
)

# 初始化 session state
if "index" not in st.session_state:
    st.session_state.index = None
if "query_engine" not in st.session_state:
    st.session_state.query_engine = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "enable_rerank" not in st.session_state:
    st.session_state.enable_rerank = False
if "reranker_type" not in st.session_state:
    st.session_state.reranker_type = "keyword"
if "compare_mode" not in st.session_state:
    st.session_state.compare_mode = False
if "enable_streaming" not in st.session_state:
    st.session_state.enable_streaming = True
if "metadata_filters" not in st.session_state:
    st.session_state.metadata_filters = {}
if "enable_metadata_filter" not in st.session_state:
    st.session_state.enable_metadata_filter = False


def load_documents():
    """加载文档并创建索引"""
    try:
        settings = get_settings()
        loader = MarkdownLoader()

        # 加载文档
        with st.spinner("正在加载文档..."):
            documents = loader.load_documents(settings.docs_dir)
            if not documents:
                st.warning(f"在 {settings.docs_dir} 目录中未找到文档")
                return False

        # 保存文档到 session state
        st.session_state.documents = documents

        # 创建索引
        with st.spinner("正在创建向量索引..."):
            index_manager = VectorIndexManager()
            index = index_manager.create_index(documents)
            st.session_state.index = index

            # 根据当前设置创建查询引擎
            _create_query_engine()

        st.session_state.documents_loaded = True
        return True

    except Exception as e:
        st.error(f"加载文档时出错: {str(e)}")
        return False


def _create_query_engine():
    """根据当前 session state 创建查询引擎"""
    if st.session_state.index is None:
        return

    # 构建元数据过滤器
    metadata_filters = None
    if st.session_state.enable_metadata_filter and st.session_state.metadata_filters:
        filter_builder = MetadataFilterBuilder()
        for field, value in st.session_state.metadata_filters.items():
            if value:  # 只添加非空值
                filter_builder.eq(field, value)
        metadata_filters = filter_builder.build()

    query_engine = RAGQueryEngine(
        index=st.session_state.index,
        enable_rerank=st.session_state.enable_rerank,
        reranker_type=st.session_state.reranker_type,
        compare_mode=st.session_state.compare_mode,
        streaming=st.session_state.enable_streaming,
        metadata_filters=metadata_filters
    )
    st.session_state.query_engine = query_engine


def _get_available_metadata_fields() -> set:
    """获取可用的元数据字段"""
    if not st.session_state.documents:
        return set()
    fields = set()
    for doc in st.session_state.documents:
        fields.update(doc.metadata.keys())
    return fields


def _get_metadata_values(field: str) -> List:
    """获取指定字段的所有唯一值"""
    if not st.session_state.documents:
        return []
    values = set()
    for doc in st.session_state.documents:
        value = doc.metadata.get(field)
        if value is not None:
            if isinstance(value, list):
                values.update(str(v) for v in value)
            else:
                values.add(str(value))
    return sorted(list(values))


def main():
    """主应用"""
    st.title("🦙 LlamaIndex RAG 问答系统")
    st.markdown("---")

    # 侧边栏 - 文档管理
    with st.sidebar:
        st.header("📁 文档管理")

        # 显示配置信息
        settings = get_settings()
        st.info(f"**文档目录:** `{settings.docs_dir}`")
        st.info(f"**存储目录:** `{settings.storage_dir}`")

        st.markdown("---")

        # 加载文档按钮
        if st.button("📥 加载文档", type="primary", use_container_width=True):
            if load_documents():
                st.success(f"✅ 成功加载文档并创建索引！")
                st.rerun()

        # 显示状态
        if st.session_state.documents_loaded:
            st.success("🟢 索引已就绪")
        else:
            st.warning("🟡 请先加载文档")

        st.markdown("---")

        # Reranking 配置
        st.header("🔄 重排序 (Rerank)")

        enable_rerank = st.checkbox(
            "启用重排序",
            value=st.session_state.enable_rerank,
            help="对检索结果进行重新排序以提高准确性"
        )

        reranker_type = st.selectbox(
            "Reranker 类型",
            options=["keyword", "cohere"],
            index=0 if st.session_state.reranker_type == "keyword" else 1,
            help="keyword: 基于关键词匹配 | cohere: 使用 Cohere API (需要 API key)"
        )

        compare_mode = st.checkbox(
            "对比模式",
            value=st.session_state.compare_mode,
            help="同时显示 rerank 前后的结果对比"
        )

        # 检测状态变化
        state_changed = (
            enable_rerank != st.session_state.enable_rerank or
            reranker_type != st.session_state.reranker_type or
            compare_mode != st.session_state.compare_mode
        )

        if state_changed and st.session_state.documents_loaded:
            st.session_state.enable_rerank = enable_rerank
            st.session_state.reranker_type = reranker_type
            st.session_state.compare_mode = compare_mode
            _create_query_engine()
            st.rerun()

        # 保存状态
        st.session_state.enable_rerank = enable_rerank
        st.session_state.reranker_type = reranker_type
        st.session_state.compare_mode = compare_mode

        # 显示当前配置
        if enable_rerank:
            st.success(f"🟢 已启用 {reranker_type} reranker")
        else:
            st.caption("🟡 Rerank 未启用")

        st.markdown("---")

        # 流式输出配置
        st.header("⚡ 流式输出")

        enable_streaming = st.checkbox(
            "启用流式输出",
            value=st.session_state.enable_streaming,
            help="实时显示生成的文本（打字机效果）"
        )

        # 保存状态并检测变化
        if enable_streaming != st.session_state.enable_streaming:
            st.session_state.enable_streaming = enable_streaming
            if st.session_state.documents_loaded:
                _create_query_engine()

        # 显示当前状态
        if enable_streaming:
            st.success("🟢 流式输出已启用")
        else:
            st.caption("🟡 流式输出未启用")

        st.markdown("---")

        # 元数据过滤配置
        st.header("🏷️ 元数据过滤")

        enable_metadata_filter = st.checkbox(
            "启用元数据过滤",
            value=st.session_state.enable_metadata_filter,
            help="按文档元数据（分类、标签等）过滤检索结果"
        )

        if enable_metadata_filter and st.session_state.documents_loaded:
            st.caption("可过滤字段：")

            # 获取可用字段
            available_fields = _get_available_metadata_fields()

            # 常用字段优先显示
            priority_fields = ["category", "author", "tags", "year", "file_type"]
            other_fields = [f for f in available_fields if f not in priority_fields]

            # 过滤掉不适合显示的字段
            exclude_fields = {"file_path", "file_size", "created_date", "modified_date",
                            "word_count", "char_count", "file_name"}
            display_fields = [f for f in priority_fields + other_fields
                            if f not in exclude_fields]

            # 为每个字段创建选择器
            for field in display_fields:
                values = _get_metadata_values(field)
                if values:
                    # 获取当前值
                    current_value = st.session_state.metadata_filters.get(field, "")

                    # 根据值数量选择合适的控件
                    if len(values) <= 5:
                        # 少量选项用 selectbox
                        options = [""] + values
                        index = options.index(current_value) if current_value in options else 0
                        new_value = st.selectbox(
                            field,
                            options=options,
                            index=index,
                            key=f"filter_{field}"
                        )
                    else:
                        # 多量选项用 text_input + 建议
                        new_value = st.text_input(
                            field,
                            value=current_value,
                            key=f"filter_{field}",
                            help=f"可选值: {', '.join(values[:5])}{'...' if len(values) > 5 else ''}"
                        )

                    # 更新过滤器
                    if new_value:
                        st.session_state.metadata_filters[field] = new_value
                    elif field in st.session_state.metadata_filters:
                        del st.session_state.metadata_filters[field]

            # 显示当前过滤条件
            if st.session_state.metadata_filters:
                st.markdown("**当前过滤:**")
                for field, value in st.session_state.metadata_filters.items():
                    st.caption(f"  {field}: {value}")

            # 应用过滤按钮
            if st.button("🔄 应用过滤", use_container_width=True):
                _create_query_engine()
                st.success("过滤条件已应用")

            # 清除过滤按钮
            if st.button("❌ 清除过滤", use_container_width=True):
                st.session_state.metadata_filters = {}
                _create_query_engine()
                st.success("过滤条件已清除")

        # 保存状态
        st.session_state.enable_metadata_filter = enable_metadata_filter

        st.markdown("---")
        st.caption("混合架构: Anthropic LLM (原生 SDK) + Ollama Embedding")

    # 主区域 - 问答
    if not st.session_state.documents_loaded:
        st.info("👈 请在侧边栏点击「加载文档」按钮开始使用")
        st.markdown("""
        ### 使用说明

        1. 将 Markdown 文档放入 `data/docs` 目录
        2. 点击侧边栏的「加载文档」按钮
        3. 等待索引创建完成
        4. 在下方输入框中提问

        ### 功能特性

        - 📄 支持 Markdown 文档
        - 🔍 语义搜索
        - 🎯 混合架构: Anthropic LLM (原生 SDK) + Ollama Embedding
        - 📊 显示答案来源
        """)
    else:
        st.header("💬 问答")

        # 显示配置
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"**LLM:** {settings.anthropic_model}")
        with col2:
            st.caption(f"**Embed:** {settings.embed_model}")
        with col3:
            rerank_status = "🟢" if st.session_state.enable_rerank else "🟡"
            compare_status = " (对比模式)" if st.session_state.compare_mode else ""
            st.caption(f"**Rerank:** {rerank_status}{compare_status}")
        with col4:
            stream_status = "🟢" if st.session_state.enable_streaming else "🟡"
            st.caption(f"**Stream:** {stream_status}")

        st.markdown("---")

        # 问题输入
        question = st.text_input(
            "请输入您的问题:",
            placeholder="例如: 这篇文档讲了什么内容？",
            key="question_input"
        )

        # 查询按钮
        if st.button("🔍 提问", type="primary", use_container_width=True):
            if question.strip():
                # 流式输出
                if st.session_state.enable_streaming:
                    try:
                        # 创建占位符用于流式显示
                        answer_placeholder = st.empty()
                        sources_placeholder = st.empty()

                        accumulated_text = ""
                        sources = []

                        # 流式查询
                        for chunk in st.session_state.query_engine.stream_query(question):
                            if chunk.get("text"):
                                accumulated_text += chunk["text"]
                                # 实时更新显示
                                with answer_placeholder.container():
                                    st.subheader("📝 答案")
                                    st.markdown(accumulated_text)

                            # 保存来源信息（在最后一个 chunk 中）
                            if chunk.get("sources"):
                                sources = chunk["sources"]

                            if chunk.get("done"):
                                # 查询完成，显示来源
                                with sources_placeholder.container():
                                    if sources:
                                        st.subheader("📚 来源")
                                        for i, source in enumerate(sources, 1):
                                            file_name = source["file_name"] if isinstance(source, dict) else source
                                            score = f" (score: {source['score']:.3f})" if isinstance(source, dict) and 'score' in source else ""
                                            st.write(f"{i}. `{file_name}`{score}")
                                    else:
                                        st.caption("未找到相关来源")

                    except Exception as e:
                        st.error(f"流式查询出错: {str(e)}")

                # 非流式输出
                else:
                    with st.spinner("正在查询..."):
                        try:
                            result = st.session_state.query_engine.query(question)

                            # 对比模式
                            if result.get("compare"):
                                st.markdown("### 📊 对比结果")

                                # Baseline 结果
                                with st.expander("🟡 基础检索 (无 Rerank)", expanded=False):
                                    st.write("**答案:**")
                                    st.write(result["compare"]["baseline"]["answer"])
                                    st.markdown("**来源:**")
                                    for i, source in enumerate(result["compare"]["baseline"]["sources"], 1):
                                        score = f" (score: {source['score']:.3f})" if 'score' in source else ""
                                        st.write(f"{i}. `{source['file_name']}`{score}")

                                # Reranked 结果
                                with st.expander("🟢 重排序后 (With Rerank)", expanded=True):
                                    st.write("**答案:**")
                                    st.write(result["compare"]["reranked"]["answer"])
                                    st.markdown("**来源:**")
                                    for i, source in enumerate(result["compare"]["reranked"]["sources"], 1):
                                        score = f" (score: {source['score']:.3f})" if 'score' in source else ""
                                        st.write(f"{i}. `{source['file_name']}`{score}")
                            else:
                                # 正常模式 - 显示答案
                                st.subheader("📝 答案")
                                st.write(result["answer"])

                                # 显示 Rerank 状态
                                if result.get("rerank_enabled"):
                                    st.caption("🔄 结果已通过重排序优化")

                                # 显示来源
                                if result["sources"]:
                                    st.subheader("📚 来源")
                                    for i, source in enumerate(result["sources"], 1):
                                        file_name = source["file_name"] if isinstance(source, dict) else source
                                        score = f" (score: {source['score']:.3f})" if isinstance(source, dict) and 'score' in source else ""
                                        st.write(f"{i}. `{file_name}`{score}")
                                else:
                                    st.caption("未找到相关来源")

                        except Exception as e:
                            st.error(f"查询出错: {str(e)}")
            else:
                st.warning("请输入问题")

        # 示例问题
        st.markdown("---")
        st.markdown("### 💡 示例问题")
        example_questions = [
            "文档的主要内容是什么？",
            "有哪些关键概念？",
            "总结一下这篇文章",
        ]

        for q in example_questions:
            if st.button(q, key=f"example_{q}"):
                st.session_state.question_input = q
                st.rerun()


if __name__ == "__main__":
    main()
