# 项目2：RAG知识库问答系统 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 构建一个支持文档上传、向量化存储、语义检索的RAG问答Web应用

**架构:** 文档解析 → 文本分块 → 向量嵌入 → 向量数据库存储 → 检索增强生成

**Tech Stack:** Python, LangChain, ChromaDB, Sentence Transformers, Streamlit

---

## 前置准备

### Task 1: 环境设置

**Files:**
- Create: `project2-rag-system/requirements.txt`
- Create: `project2-rag-system/.env.example`
- Create: `project2-rag-system/README.md`
- Create: `project2-rag-system/src/__init__.py`

**Step 1: 创建项目目录**

```bash
cd /root/Learn/llm-learning
mkdir -p project2-rag-system/src
mkdir -p project2-rag-system/data/documents
mkdir -p project2-rag-system/data/chroma
mkdir -p project2-rag-system/tests
```

**Step 2: 创建 requirements.txt**

```txt
# 核心依赖
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10

# 向量数据库
chromadb>=0.4.0

# 文档处理
pypdf>=3.17.0
python-docx>=1.1.0
unstructured>=0.11.0

# 嵌入模型
sentence-transformers>=2.3.0

# Web框架
streamlit>=1.31.0

# 其他
python-dotenv>=1.0.0
pytest>=7.4.0
```

**Step 3: 创建 .env.example**

```env
# LLM配置
OPENAI_API_KEY=your_openai_api_key_here

# 嵌入模型配置
EMBEDDING_MODEL=openai  # openai | local
LOCAL_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# 向量数据库配置
CHROMA_PERSIST_DIR=./data/chroma

# RAG配置
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=3
```

**Step 4: 创建 README.md**

```markdown
# 项目2：RAG知识库问答系统

> 基于检索增强生成（RAG）的智能问答系统

## 功能

- 📄 支持PDF、TXT、MD、DOCX文档上传
- 🔍 智能语义检索
- 💬 基于检索内容的精准问答
- 📊 可视化检索结果

## 技术栈

- LangChain: 应用框架
- ChromaDB: 向量数据库
- Sentence Transformers: 文本嵌入
- Streamlit: Web界面

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run src/app.py
```

## 学习要点

- 文档分块策略
- 向量嵌入原理
- 相似度计算
- RAG优化技巧
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat(project2): initialize RAG system project structure"
```

---

## 模块1：文档处理

### Task 2: 实现文档加载器

**Files:**
- Create: `project2-rag-system/src/document_loader.py`
- Create: `project2-rag-system/tests/test_document_loader.py`

**Step 1: 编写测试**

```python
# tests/test_document_loader.py
import pytest
from pathlib import Path
from src.document_loader import DocumentLoader

def test_load_txt_file():
    """测试加载TXT文件"""
    loader = DocumentLoader()
    # 创建测试文件
    test_file = Path("data/documents/test.txt")
    test_file.write_text("这是一段测试文本。", encoding='utf-8')

    docs = loader.load_file(str(test_file))
    assert len(docs) > 0
    assert "测试文本" in docs[0].page_content

    # 清理
    test_file.unlink()

def test_load_pdf_file():
    """测试加载PDF文件"""
    # 需要准备测试PDF
    pass

def test_unsupported_format():
    """测试不支持的格式"""
    loader = DocumentLoader()
    with pytest.raises(ValueError):
        loader.load_file("test.xyz")
```

**Step 2: 实现文档加载器**

```python
# src/document_loader.py
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader
)

class DocumentLoader:
    """文档加载器 - 支持多种格式"""

    SUPPORTED_FORMATS = {
        '.pdf': PyPDFLoader,
        '.txt': TextLoader,
        '.md': UnstructuredMarkdownLoader,
        '.docx': UnstructuredWordDocumentLoader,
    }

    def __init__(self):
        self.loaders = self.SUPPORTED_FORMATS.copy()

    def load_file(self, file_path: str) -> List[Document]:
        """
        加载文档

        Args:
            file_path: 文档路径

        Returns:
            文档列表

        Raises:
            ValueError: 不支持的格式
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()

        if ext not in self.loaders:
            supported = ', '.join(self.loaders.keys())
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported formats: {supported}"
            )

        loader_class = self.loaders[ext]
        loader = loader_class(str(path))

        return loader.load()

    def is_supported(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = Path(file_path).suffix.lower()
        return ext in self.loaders
```

**Step 3: 运行测试**

```bash
cd project2-rag-system
pytest tests/test_document_loader.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project2): implement document loader"
```

---

### Task 3: 实现文档分块器

**Files:**
- Create: `project2-rag-system/src/text_splitter.py`
- Create: `project2-rag-system/tests/test_text_splitter.py`

**Step 1: 编写测试**

```python
# tests/test_text_splitter.py
import pytest
from langchain_core.documents import Document
from src.text_splitter import DocumentSplitter

def test_split_long_document():
    """测试分割长文档"""
    splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)

    # 创建一个长文档
    long_text = "这是一句话。" * 50
    doc = Document(page_content=long_text)

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 150 for chunk in chunks)  # 允许一些误差

def test_split_preserves_metadata():
    """测试分割保留元数据"""
    splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)

    doc = Document(
        page_content="测试内容" * 50,
        metadata={"source": "test.txt", "page": 1}
    )

    chunks = splitter.split_documents([doc])

    assert all(chunk.metadata.get("source") == "test.txt" for chunk in chunks)
```

**Step 2: 实现分块器**

```python
# src/text_splitter.py
from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentSplitter:
    """文档分块器 - 支持多种分块策略"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separators: 分隔符列表
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 默认分隔符（按优先级）
        default_separators = ["\n\n", "\n", "。", "！", "？", ".", " ", ""]
        self.separators = separators or default_separators

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档

        Args:
            documents: 文档列表

        Returns:
            分割后的文档块列表
        """
        return self.splitter.split_documents(documents)

    def split_text(self, text: str) -> List[str]:
        """
        分割文本

        Args:
            text: 待分割的文本

        Returns:
            文本块列表
        """
        return self.splitter.split_text(text)
```

**Step 3: 运行测试**

```bash
pytest tests/test_text_splitter.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project2): implement document splitter"
```

---

## 模块2：向量存储

### Task 4: 实现嵌入模型

**Files:**
- Create: `project2-rag-system/src/embeddings.py`
- Create: `project2-rag-system/tests/test_embeddings.py`

**Step 1: 编写测试**

```python
# tests/test_embeddings.py
import pytest
from src.embeddings import EmbeddingModel

def test_create_embedding():
    """测试创建嵌入向量"""
    embedder = EmbeddingModel(model_type="local")
    text = "这是一段测试文本"

    embedding = embedder.embed_query(text)

    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)

def test_embed_documents():
    """测试批量嵌入"""
    embedder = EmbeddingModel(model_type="local")
    texts = ["文本1", "文本2", "文本3"]

    embeddings = embedder.embed_documents(texts)

    assert len(embeddings) == len(texts)
```

**Step 2: 实现嵌入模型**

```python
# src/embeddings.py
import os
from typing import List
from sentence_transformers import SentenceTransformer
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

class EmbeddingModel:
    """嵌入模型 - 支持OpenAI和本地模型"""

    def __init__(self, model_type: str = "openai"):
        """
        初始化嵌入模型

        Args:
            model_type: 模型类型 (openai | local)
        """
        self.model_type = model_type

        if model_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        else:
            # 使用本地多语言模型
            model_name = os.getenv(
                "LOCAL_EMBEDDING_MODEL",
                "paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

    def embed_query(self, text: str) -> List[float]:
        """嵌入单段文本"""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        return self.embeddings.embed_documents(texts)

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        # 创建一个测试嵌入来获取维度
        return len(self.embed_query("test"))
```

**Step 3: 运行测试**

```bash
pytest tests/test_embeddings.py -v -s
```

注意：第一次运行会下载模型，需要时间

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project2): implement embedding model"
```

---

### Task 5: 实现向量存储

**Files:**
- Create: `project2-rag-system/src/vector_store.py`
- Create: `project2-rag-system/tests/test_vector_store.py`

**Step 1: 编写测试**

```python
# tests/test_vector_store.py
import pytest
from langchain_core.documents import Document
from src.vector_store import VectorStore
from src.embeddings import EmbeddingModel

def test_add_and_search():
    """测试添加和搜索文档"""
    store = VectorStore(collection_name="test")
    embedder = EmbeddingModel(model_type="local")

    # 添加文档
    docs = [
        Document(page_content="Python是一种编程语言"),
        Document(page_content="Java也是一种编程语言"),
    ]
    store.add_documents(docs, embedder)

    # 搜索
    results = store.search("编程语言", embedder, k=1)

    assert len(results) > 0
    assert "编程语言" in results[0].page_content or "语言" in results[0].page_content

def test_similarity_search_with_score():
    """测试带分数的相似度搜索"""
    store = VectorStore(collection_name="test")
    embedder = EmbeddingModel(model_type="local")

    docs = [Document(page_content="测试内容")]
    store.add_documents(docs, embedder)

    results = store.search_with_score("测试", embedder, k=1)

    assert len(results) == 2  # (doc, score) 元组
    assert isinstance(results[0][1], float)
```

**Step 2: 实现向量存储**

```python
# src/vector_store.py
import os
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.vectorstores import Chroma as ChromaStore
from src.embeddings import EmbeddingModel

class VectorStore:
    """向量存储管理器 - 基于ChromaDB"""

    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: str = None
    ):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIR",
            "./data/chroma"
        )
        self._store: Chroma = None

    def _get_store(self, embeddings):
        """获取或创建向量存储"""
        if self._store is None:
            self._store = ChromaStore(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
        return self._store

    def add_documents(
        self,
        documents: List[Document],
        embeddings: EmbeddingModel
    ) -> List[str]:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表
            embeddings: 嵌入模型

        Returns:
            添加的文档ID列表
        """
        store = self._get_store(embeddings.embeddings)
        return store.add_documents(documents)

    def search(
        self,
        query: str,
        embeddings: EmbeddingModel,
        k: int = 4
    ) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            embeddings: 嵌入模型
            k: 返回结果数量

        Returns:
            匹配的文档列表
        """
        store = self._get_store(embeddings.embeddings)
        return store.similarity_search(query, k=k)

    def search_with_score(
        self,
        query: str,
        embeddings: EmbeddingModel,
        k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        带分数的相似度搜索

        Args:
            query: 查询文本
            embeddings: 嵌入模型
            k: 返回结果数量

        Returns:
            (文档, 相似度分数) 元组列表，分数越高越相似
        """
        store = self._get_store(embeddings.embeddings)
        return store.similarity_search_with_score(query, k=k)

    def delete_collection(self):
        """删除当前集合"""
        if self._store is not None:
            self._store.delete_collection()
            self._store = None

    def clear(self, embeddings: EmbeddingModel):
        """清空所有文档"""
        store = self._get_store(embeddings.embeddings)
        store.delete_collection()
        self._store = None
```

**Step 3: 运行测试**

```bash
pytest tests/test_vector_store.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project2): implement vector store"
```

---

## 模块3：RAG链路

### Task 6: 实现RAG问答链

**Files:**
- Create: `project2-rag-system/src/rag_chain.py`
- Create: `project2-rag-system/tests/test_rag_chain.py`

**Step 1: 编写测试**

```python
# tests/test_rag_chain.py
import pytest
from langchain_core.documents import Document
from src.rag_chain import RAGChain
from src.vector_store import VectorStore
from src.embeddings import EmbeddingModel

def test_rag_answer():
    """测试RAG回答"""
    # 准备向量存储
    store = VectorStore(collection_name="test_rag")
    embedder = EmbeddingModel(model_type="local")

    docs = [Document(page_content="Python是由Guido van Rossum创建的编程语言")]
    store.add_documents(docs, embedder)

    # 创建RAG链
    rag = RAGChain(store, embedder)

    answer = rag.ask("谁创建了Python？")

    assert isinstance(answer, str)
    assert len(answer) > 0
```

**Step 2: 实现RAG链**

```python
# src/rag_chain.py
import os
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from src.vector_store import VectorStore
from src.embeddings import EmbeddingModel

# RAG提示词模板
RAG_TEMPLATE = """
你是一个有帮助的AI助手。请基于以下检索到的上下文信息回答用户问题。

如果上下文中没有相关信息，请明确说明你无法基于提供的信息回答。

上下文信息：
{context}

用户问题：{question}

你的回答：
"""

class RAGChain:
    """RAG问答链"""

    def __init__(
        self,
        vector_store: VectorStore,
        embeddings: EmbeddingModel,
        top_k: int = 3,
        temperature: float = 0.7
    ):
        """
        初始化RAG链

        Args:
            vector_store: 向量存储
            embeddings: 嵌入模型
            top_k: 检索的文档数量
            temperature: 生成温度
        """
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.top_k = top_k

        # 初始化LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=api_key
        )

        # 创建提示词模板
        self.prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)

        # 构建链路
        self.chain = (
            {
                "context": self._retrieve_context,
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _retrieve_context(self, question: str) -> str:
        """检索相关上下文"""
        docs = self.vector_store.search(
            question,
            self.embeddings,
            k=self.top_k
        )

        # 合并文档内容
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            content = doc.page_content
            context_parts.append(f"[文档{i} 来自 {source}]\n{content}")

        return "\n\n".join(context_parts)

    def ask(self, question: str) -> str:
        """
        提问并获取答案

        Args:
            question: 用户问题

        Returns:
            答案文本
        """
        return self.chain.invoke(question)

    def ask_with_sources(self, question: str) -> dict:
        """
        提问并获取答案和来源

        Args:
            question: 用户问题

        Returns:
            包含answer和sources的字典
        """
        # 检索文档
        docs = self.vector_store.search(
            question,
            self.embeddings,
            k=self.top_k
        )

        # 获取答案
        answer = self.ask(question)

        # 提取来源
        sources = list(set(
            doc.metadata.get("source", "未知")
            for doc in docs
        ))

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_docs": len(docs)
        }
```

**Step 3: 运行测试**

```bash
pytest tests/test_rag_chain.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project2): implement RAG chain"
```

---

## 模块4：Web界面

### Task 7: 实现Streamlit应用

**Files:**
- Create: `project2-rag-system/src/app.py`

**Step 1: 创建Streamlit应用**

```python
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
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ 请在.env文件中配置OPENAI_API_KEY")
        st.stop()

def init_embeddings():
    """初始化嵌入模型"""
    if st.session_state.embeddings is None:
        with st.spinner("加载嵌入模型..."):
            model_type = st.session_state.get("embedding_model", "local")
            st.session_state.embeddings = EmbeddingModel(model_type=model_type)
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

        # 嵌入模型选择
        embedding_model = st.selectbox(
            "嵌入模型",
            ["local", "openai"],
            index=0,
            help="local: 本地模型（免费）, openai: OpenAI嵌入（需API）"
        )
        st.session_state.embedding_model = embedding_model

        # RAG参数
        st.subheader("RAG参数")
        top_k = st.slider("检索文档数", 1, 10, 3)
        temperature = st.slider("生成温度", 0.0, 1.0, 0.7, 0.1)

        st.session_state.rag_top_k = top_k
        st.session_state.rag_temperature = temperature

        # 统计信息
        st.divider()
        st.subheader("📊 统计")
        st.metric("已处理文档", st.session_state.documents_processed)

def upload_section():
    """文档上传区域"""
    st.subheader("📤 上传文档")

    uploaded_files = st.file_uploader(
        "选择文档（PDF, TXT, MD, DOCX）",
        type=['pdf', 'txt', 'md', 'docx'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        if st.button("处理文档", type="primary"):
            process_documents(uploaded_files)

def process_documents(uploaded_files):
    """处理上传的文档"""
    init_embeddings()
    init_vector_store()

    loader = DocumentLoader()
    splitter = DocumentSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_files = len(uploaded_files)
    all_chunks = []

    for idx, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"正在处理: {uploaded_file.name}")

        # 保存临时文件
        temp_path = f"data/documents/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # 加载文档
            docs = loader.load_file(temp_path)

            # 分块
            chunks = splitter.split_documents(docs)

            # 添加来源元数据
            for chunk in chunks:
                chunk.metadata["source"] = uploaded_file.name

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
    st.subheader("💬 问答")

    if st.session_state.documents_processed == 0:
        st.info("👆 请先上传并处理文档")
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
    st.markdown(f"### 📚 来源 ({result['retrieved_docs']} 个相关片段)")
    for source in result["sources"]:
        st.caption(f"📄 {source}")

def main():
    """主函数"""
    check_api_key()

    st.title("📚 RAG知识库问答系统")
    st.markdown("上传文档，然后基于文档内容进行智能问答")

    sidebar()

    tab1, tab2 = st.tabs(["文档管理", "智能问答"])

    with tab1:
        upload_section()

    with tab2:
        qa_section()

if __name__ == "__main__":
    main()
```

**Step 2: 创建运行脚本**

```bash
# 创建 run.sh
echo '#!/bin/bash
streamlit run src/app.py' > run.sh
chmod +x run.sh
```

**Step 3: 提交**

```bash
git add .
git commit -m "feat(project2): implement Streamlit web interface"
```

---

## 项目收尾

### Task 8: 完善文档

**Files:**
- Modify: `project2-rag-system/README.md`

**Step 1: 更新README**

```markdown
# 项目2：RAG知识库问答系统

> 基于检索增强生成（RAG）的智能问答系统

## 🎯 项目目标

掌握RAG（检索增强生成）技术的核心概念和实现，解决大模型知识时效性和准确性问题。

## ✨ 功能特性

- 📄 **多格式支持**: PDF、TXT、Markdown、DOCX
- 🔍 **智能检索**: 基于语义相似度的文档检索
- 💬 **精准问答**: 结合检索内容的生成式回答
- 📊 **可视化展示**: 直观的Web界面
- 🌐 **中文优化**: 使用多语言嵌入模型

## 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 应用框架 | LangChain | RAG链路编排 |
| 向量数据库 | ChromaDB | 本地向量存储 |
| 嵌入模型 | Sentence Transformers | 本地多语言模型 |
| Web框架 | Streamlit | 快速构建UI |
| LLM | OpenAI GPT | 答案生成 |

## 📦 安装运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑.env，填入OPENAI_API_KEY

# 运行应用
streamlit run src/app.py
# 或使用
./run.sh
```

## 🎓 学习要点

### 1. 文档分块策略
- **固定大小**: 简单但可能破坏语义
- **语义分割**: 按段落、句子分割，保持完整性
- **滑动窗口**: 块之间有重叠，避免信息丢失

### 2. 向量嵌入
- 将文本转换为高维向量表示
- 相似内容在向量空间中距离更近
- 嵌入模型选择影响检索质量

### 3. 相似度计算
- **余弦相似度**: 最常用，计算向量夹角
- **点积**: 考虑向量长度
- **欧氏距离**: 几何距离

### 4. RAG优化技巧
- **重排序**: 检索后重新排序提高精度
- **混合检索**: 结合关键词和语义检索
- **查询改写**: 优化用户查询提高检索效果
- **动态Top-K**: 根据问题调整检索数量

## 📁 项目结构

```
project2-rag-system/
├── src/
│   ├── app.py              # Streamlit应用
│   ├── document_loader.py  # 文档加载器
│   ├── text_splitter.py    # 文本分块器
│   ├── embeddings.py       # 嵌入模型
│   ├── vector_store.py     # 向量存储
│   └── rag_chain.py        # RAG链路
├── data/
│   ├── documents/          # 上传的文档
│   └── chroma/             # 向量数据库
├── tests/                  # 测试文件
├── requirements.txt
└── README.md
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_vector_store.py -v
```

## 🚀 下一步

- 添加文档重排序功能
- 支持多轮对话历史
- 添加引用高亮
- 支持Web URL抓取

## 📝 参考资料

- [LangChain RAG教程](https://python.langchain.com/docs/use_cases/question_answering/)
- [ChromaDB文档](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
```

**Step 2: 最终提交**

```bash
git add .
git commit -m "docs(project2): complete documentation"
git push origin master
```

---

## 项目2完成检查清单

- [ ] 文档加载器支持多种格式
- [ ] 文档分块功能正常
- [ ] 嵌入模型正常工作
- [ ] 向量存储和检索功能正常
- [ ] RAG问答链路完整
- [ ] Web界面可正常使用
- [ ] 所有测试通过
- [ ] 文档完善
- [ ] 代码已推送到GitHub

**下一步**: 开始项目3 - 代码助手Agent
