# src/app.py
import streamlit as st
import os
from dotenv import load_dotenv

from src.document_loader import DocumentLoader
from src.text_splitter import DocumentSplitter
from src.embeddings import EmbeddingModel
from src.vector_store import VectorStore
from src.rag_chain import RAGChain

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="RAG知识库问答",
    page_icon="📚",
    layout="wide"
)

# 初始化session state
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "documents_processed" not in st.session_state:
    st.session_state.documents_processed = 0

def check_api_key():
    """检查API密钥"""
    if not os.getenv("ZHIPUAI_API_KEY"):
        st.error("❌ 请在.env文件中配置ZHIPUAI_API_KEY")
        st.stop()

def init_embeddings():
    """初始化嵌入模型"""
    if st.session_state.embeddings is None:
        with st.spinner("加载嵌入模型..."):
            st.session_state.embeddings = EmbeddingModel()
        st.success("✅ 嵌入模型加载完成")

def init_vector_store():
    """初始化向量存储"""
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore(
            collection_name="knowledge_base"
        )

def sidebar():
    """侧边栏"""
    with st.sidebar:
        st.title("🔧 配置")

        # RAG参数
        st.subheader("RAG参数")
        top_k = st.slider("检索文档数", 1, 10, 3)
        temperature = st.slider("生成温度", 0.0, 1.0, 0.7, 0.1)
        chunk_size = st.slider("分块大小", 100, 1000, 500)
        chunk_overlap = st.slider("分块重叠", 0, 200, 50)

        st.session_state.rag_top_k = top_k
        st.session_state.rag_temperature = temperature
        st.session_state.chunk_size = chunk_size
        st.session_state.chunk_overlap = chunk_overlap

        # 统计信息
        st.divider()
        st.subheader("📊 统计")
        st.metric("已处理文档", st.session_state.documents_processed)
        if st.session_state.vector_store:
            st.metric("向量数量", st.session_state.vector_store.count())

        # 清空按钮
        if st.button("清空知识库"):
            if st.session_state.vector_store:
                st.session_state.vector_store.clear()
                st.session_state.documents_processed = 0
                st.rerun()

def upload_section():
    """文档上传区域"""
    st.subheader("📤 上传文档")

    # 手动输入文本
    st.write("**或者直接粘贴文本内容：**")
    text_input = st.text_area(
        "粘贴文档内容",
        height=200,
        placeholder="在此粘贴文档内容...",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        doc_name = st.text_input("文档名称（可选）", value="manual_input.txt")

    with col2:
        if st.button("添加文本到知识库", type="primary", use_container_width=True):
            if text_input.strip():
                add_text_to_knowledge_base(text_input, doc_name)
            else:
                st.warning("请输入文档内容")

    st.divider()
    st.write("**或上传文件（TXT/MD）**")

    uploaded_files = st.file_uploader(
        "选择文档",
        type=['txt', 'md'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        if st.button("处理上传的文件", type="primary"):
            process_uploaded_files(uploaded_files)

def add_text_to_knowledge_base(text: str, doc_name: str):
    """添加文本到知识库"""
    init_embeddings()
    init_vector_store()

    from src.document_loader import Document

    # 创建文档
    doc = Document(
        page_content=text,
        metadata={"source": doc_name}
    )

    # 分块
    splitter = DocumentSplitter(
        chunk_size=st.session_state.chunk_size,
        chunk_overlap=st.session_state.chunk_overlap
    )
    chunks = splitter.split_documents([doc])

    # 添加到向量存储
    st.session_state.vector_store.add_documents(
        chunks,
        st.session_state.embeddings
    )

    st.session_state.documents_processed += 1
    st.success(f"✅ 已添加 {len(chunks)} 个文本块到知识库")

def process_uploaded_files(uploaded_files):
    """处理上传的文件"""
    init_embeddings()
    init_vector_store()

    loader = DocumentLoader()
    splitter = DocumentSplitter(
        chunk_size=st.session_state.chunk_size,
        chunk_overlap=st.session_state.chunk_overlap
    )

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_files = len(uploaded_files)
    all_chunks = []

    for idx, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"正在处理: {uploaded_file.name}")

        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=f"_{uploaded_file.name}", delete=False, encoding='utf-8') as f:
            f.write(uploaded_file.getbuffer().decode('utf-8'))
            temp_path = f.name

        try:
            # 加载文档
            docs = loader.load_file(temp_path)

            # 分块
            chunks = splitter.split_documents(docs)

            all_chunks.extend(chunks)

        except Exception as e:
            st.error(f"处理 {uploaded_file.name} 时出错: {e}")

        progress_bar.progress((idx + 1) / total_files)

    # 添加到向量存储
    if all_chunks:
        status_text.text("正在向量化并存储...")
        st.session_state.vector_store.add_documents(
            all_chunks,
            st.session_state.embeddings
        )

        st.session_state.documents_processed += len(uploaded_files)

        status_text.text("完成！")
        progress_bar.empty()

        st.success(f"✅ 成功处理 {len(uploaded_files)} 个文档，共 {len(all_chunks)} 个文本块")
    else:
        st.warning("没有成功处理任何文档")

def qa_section():
    """问答区域"""
    st.subheader("💬 智能问答")

    if st.session_state.documents_processed == 0:
        st.info("👆 请先添加文档到知识库")
        return

    # 显示示例问题
    with st.expander("💡 示例问题"):
        st.write("- 文档的主要内容是什么？")
        st.write("- 总结一下关键要点")
        st.write("- 提取所有重要的数据和信息")

    # 问题输入
    question = st.text_input(
        "输入你的问题",
        placeholder="关于文档的任何问题...",
        label_visibility="collapsed"
    )

    if st.button("提问", type="primary") and question:
        answer_question(question)

def answer_question(question: str):
    """回答问题"""
    init_embeddings()
    init_vector_store()

    with st.spinner("正在思考..."):
        rag = RAGChain(
            st.session_state.vector_store,
            st.session_state.embeddings,
            top_k=st.session_state.rag_top_k,
            temperature=st.session_state.rag_temperature
        )

        result = rag.ask_with_sources(question)

    # 显示答案
    st.markdown("### 📝 答案")
    st.write(result["answer"])

    # 显示来源
    if result["sources"]:
        st.markdown(f"### 📚 来源 ({result['retrieved_docs']} 个相关片段)")
        for source in result["sources"]:
            st.caption(f"📄 {source}")

def main():
    """主函数"""
    check_api_key()

    st.title("📚 RAG知识库问答系统")
    st.markdown("添加文档到知识库，然后基于文档内容进行智能问答")

    sidebar()

    tab1, tab2 = st.tabs(["文档管理", "智能问答"])

    with tab1:
        upload_section()

    with tab2:
        qa_section()

if __name__ == "__main__":
    main()
