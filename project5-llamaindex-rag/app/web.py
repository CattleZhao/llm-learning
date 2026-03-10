"""
Streamlit Web Interface for LlamaIndex RAG

提供基于 Streamlit 的 Web UI，用于文档管理和问答
"""
import streamlit as st
from pathlib import Path
from src.config import get_settings
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine

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
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False


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

        # 创建索引
        with st.spinner("正在创建向量索引..."):
            index_manager = VectorIndexManager()
            index = index_manager.create_index(documents)
            st.session_state.index = index

            # 创建查询引擎
            query_engine = RAGQueryEngine(index=index)
            st.session_state.query_engine = query_engine

        st.session_state.documents_loaded = True
        return True

    except Exception as e:
        st.error(f"加载文档时出错: {str(e)}")
        return False


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
        st.caption("混合架构: Anthropic LLM + Ollama Embedding")

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
        - 🎯 混合架构: Anthropic LLM + Ollama Embedding
        - 📊 显示答案来源
        """)
    else:
        st.header("💬 问答")

        # 显示配置
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"**LLM 模型:** {settings.anthropic_model}")
        with col2:
            st.caption(f"**嵌入模型:** {settings.embed_model}")

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
                with st.spinner("正在查询..."):
                    try:
                        result = st.session_state.query_engine.query(question)

                        # 显示答案
                        st.subheader("📝 答案")
                        st.write(result["answer"])

                        # 显示来源
                        if result["sources"]:
                            st.subheader("📚 来源")
                            for i, source in enumerate(result["sources"], 1):
                                st.write(f"{i}. `{source}`")
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
