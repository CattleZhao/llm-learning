# Project 5: LlamaIndex RAG 知识库 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 使用 LlamaIndex 框架构建本地 Markdown 技术文档知识库，支持自然语言问答

**Architecture:** 纯 LlamaIndex + Streamlit 方案。Markdown 文档通过 SimpleDirectoryReader 加载，经 MarkdownNodeParser 切分后向量化存入 ChromaDB，查询时使用 CitationQueryEngine 返回答案+引用。

**Tech Stack:** LlamaIndex 0.10+, ChromaDB, Streamlit, Ollama (本地 LLM)

---

## Project Setup

### Task 1: Initialize Project Structure

**Files:**
- Create: All directories
- Create: `README.md`
- Create: `.env.example`
- Create: `requirements.txt`

**Step 1: Create directory structure**

```bash
cd /root/Learn/llm-learning
mkdir -p project5-llamaindex-rag
cd project5-llamaindex-rag
mkdir -p src/{loaders,indexes,query}
mkdir -p app
mkdir -p tests/{unit,fixtures}
mkdir -p data/docs
mkdir -p storage
touch src/__init__.py src/loaders/__init__.py src/indexes/__init__.py src/query/__init__.py
touch app/__init__.py tests/__init__.py
```

**Step 2: Create README.md**

```markdown
# Project 5: LlamaIndex RAG 知识库

> 使用 LlamaIndex 构建的本地 Markdown 技术文档知识库

## 项目简介

基于 LlamaIndex 框架的 RAG（检索增强生成）系统，支持本地 Markdown 技术文档的智能问答。

## 功能特性

- 📁 加载本地 Markdown 文档
- 🔍 智能语义搜索
- 💬 自然语言问答
- 📚 答案附带来源引用

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 Ollama
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 运行应用
streamlit run app/web.py
```

## 技术栈

- **LlamaIndex** - RAG 框架
- **ChromaDB** - 向量数据库
- **Streamlit** - Web 界面
- **Ollama** - 本地 LLM 服务
```

**Step 3: Create .env.example**

```bash
# Ollama 服务地址
OLLAMA_BASE_URL=http://localhost:11434

# LLM 模型
LLM_MODEL=qwen2.5:7b

# 嵌入模型
EMBED_MODEL=nomic-embed-text

# 文档目录
DOCS_DIR=data/docs

# 存储目录
STORAGE_DIR=storage/chroma

# 索引参数
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=3
```

**Step 4: Create requirements.txt**

```txt
# LlamaIndex 核心
llama-index-core>=0.10.0
llama-index-readers-file>=0.1.0
llama-index-vector-stores-chroma>=0.1.0
llama-index-llms-ollama>=0.1.0
llama-index-embeddings-ollama>=0.1.0
llama-index-node-parser>=0.1.0

# 向量数据库
chromadb>=0.4.0

# Web UI
streamlit>=1.28.0

# 环境变量
python-dotenv>=1.0.0

# 测试
pytest>=7.4.0
pytest-mock>=3.12.0
```

**Step 5: Initialize git and commit**

```bash
cd /root/Learn/llm-learning
git add project5-llamaindex-rag/
git commit -m "feat: initialize project5-llamaindex-rag structure"
```

---

## Core Infrastructure

### Task 2: Implement Configuration Module

**Files:**
- Create: `src/config.py`
- Test: `tests/unit/test_config.py`

**Step 1: Write the failing test**

Create `tests/unit/test_config.py`:

```python
import os
import pytest
from src.config import Settings, get_settings

def test_settings_load_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://test:11434")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("CHUNK_SIZE", "256")

    settings = get_settings()
    assert settings.ollama_base_url == "http://test:11434"
    assert settings.llm_model == "test-model"
    assert settings.chunk_size == 256

def test_settings_default_values(monkeypatch):
    """测试默认配置值"""
    # 清除环境变量
    for key in ["OLLAMA_BASE_URL", "LLM_MODEL", "EMBED_MODEL", "CHUNK_SIZE"]:
        monkeypatch.delenv(key, raising=False)

    settings = get_settings()
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.llm_model == "qwen2.5:7b"
    assert settings.embed_model == "nomic-embed-text"
    assert settings.chunk_size == 512
```

**Step 2: Run test to verify it fails**

```bash
cd /root/Learn/llm-learning/project5-llamaindex-rag
pytest tests/unit/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.config'`

**Step 3: Write minimal implementation**

Create `src/config.py`:

```python
"""
配置管理模块
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """项目配置"""
    # Ollama 配置
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "qwen2.5:7b")
    )
    embed_model: str = field(
        default_factory=lambda: os.getenv("EMBED_MODEL", "nomic-embed-text")
    )

    # 文档配置
    docs_dir: str = field(
        default_factory=lambda: os.getenv("DOCS_DIR", "data/docs")
    )

    # 存储配置
    storage_dir: str = field(
        default_factory=lambda: os.getenv("STORAGE_DIR", "storage/chroma")
    )

    # 索引参数
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "512"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "50"))
    )
    top_k: int = field(
        default_factory=lambda: int(os.getenv("TOP_K", "3"))
    )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_config.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/config.py tests/unit/test_config.py
git commit -m "feat: add configuration module"
```

---

### Task 3: Implement MarkdownLoader

**Files:**
- Create: `src/loaders/markdown_loader.py`
- Test: `tests/unit/test_markdown_loader.py`

**Step 1: Write the failing test**

Create `tests/unit/test_markdown_loader.py`:

```python
import pytest
from pathlib import Path
from src.loaders.markdown_loader import MarkdownLoader

def test_load_documents_from_directory(tmp_path):
    """测试从目录加载 Markdown 文档"""
    # 创建测试文件
    (tmp_path / "doc1.md").write_text("# Test 1\nContent 1")
    (tmp_path / "doc2.md").write_text("# Test 2\nContent 2")
    (tmp_path / "readme.txt").write_text("Not markdown")

    loader = MarkdownLoader()
    documents = loader.load_documents(str(tmp_path))

    assert len(documents) == 2  # 只加载 .md 文件

def test_load_documents_empty_directory(tmp_path):
    """测试空目录"""
    loader = MarkdownLoader()
    documents = loader.load_documents(str(tmp_path))

    assert len(documents) == 0

def test_load_documents_recursive(tmp_path):
    """测试递归加载子目录"""
    (tmp_path / "sub").mkdir()
    (tmp_path / "doc1.md").write_text("# Doc 1")
    (tmp_path / "sub" / "doc2.md").write_text("# Doc 2")

    loader = MarkdownLoader()
    documents = loader.load_documents(str(tmp_path), recursive=True)

    assert len(documents) == 2
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_markdown_loader.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.loaders.markdown_loader'`

**Step 3: Write minimal implementation**

Create `src/loaders/markdown_loader.py`:

```python
"""
Markdown 文档加载器
"""
from pathlib import Path
from typing import List
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import MarkdownReader


class MarkdownLoader:
    """Markdown 文档加载器"""

    def __init__(self):
        self.reader = MarkdownReader()

    def load_documents(self, directory: str, recursive: bool = True) -> List:
        """
        从目录加载 Markdown 文档

        Args:
            directory: 文档目录路径
            recursive: 是否递归加载子目录

        Returns:
            文档列表
        """
        loader = SimpleDirectoryReader(
            input_dir=directory,
            recursive=recursive,
            file_extractor={".md": self.reader}
        )
        return loader.load_data()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_markdown_loader.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/loaders/ tests/unit/test_markdown_loader.py
git commit -m "feat: add MarkdownLoader for document loading"
```

---

### Task 4: Implement VectorIndexManager

**Files:**
- Create: `src/indexes/vector_index.py`
- Test: `tests/unit/test_vector_index.py`

**Step 1: Create implementation**

Create `src/indexes/vector_index.py`:

```python
"""
向量索引管理器
"""
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from src.config import get_settings


class VectorIndexManager:
    """向量索引管理器"""

    def __init__(self):
        self.settings = get_settings()
        self._configure_llamaindex()
        self.index = None

    def _configure_llamaindex(self):
        """配置 LlamaIndex 全局设置"""
        Settings.llm = Ollama(
            model=self.settings.llm_model,
            base_url=self.settings.ollama_base_url
        )
        Settings.embed_model = OllamaEmbedding(
            model_name=self.settings.embed_model,
            base_url=self.settings.ollama_base_url
        )

    def create_index(self, documents):
        """
        创建向量索引

        Args:
            documents: 文档列表

        Returns:
            创建的索引
        """
        # 解析文档为节点
        parser = MarkdownNodeParser(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
        nodes = parser.get_nodes_from_documents(documents)

        # 创建向量存储
        chroma_client = chromadb.PersistentClient(path=self.settings.storage_dir)
        chroma_store = ChromaVectorStore(
            chroma_collection=chroma_client.get_or_create_collection("docs")
        )

        # 创建索引
        self.index = VectorStoreIndex(nodes, vector_store=chroma_store)
        return self.index

    def load_index(self):
        """从存储加载已有索引"""
        chroma_client = chromadb.PersistentClient(path=self.settings.storage_dir)
        chroma_store = ChromaVectorStore(
            chroma_collection=chroma_client.get_collection("docs")
        )
        self.index = VectorStoreIndex.from_vector_store(vector_store=chroma_store)
        return self.index
```

**Step 2: Commit**

```bash
git add src/indexes/
git commit -m "feat: add VectorIndexManager"
```

---

### Task 5: Implement RAGQueryEngine

**Files:**
- Create: `src/query/query_engine.py`

**Step 1: Create implementation**

Create `src/query/query_engine.py`:

```python
"""
RAG 查询引擎
"""
from src.config import get_settings
from src.indexes.vector_index import VectorIndexManager


class RAGQueryEngine:
    """RAG 查询引擎"""

    def __init__(self, index=None):
        self.settings = get_settings()
        self.manager = VectorIndexManager()

        if index:
            self.index = index
            self._setup_query_engine()

    def set_index(self, index):
        """设置索引"""
        self.index = index
        self._setup_query_engine()

    def _setup_query_engine(self):
        """设置查询引擎"""
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=self.settings.top_k,
            verbose=True
        )

    def query(self, question: str) -> dict:
        """
        执行查询

        Args:
            question: 用户问题

        Returns:
            包含答案和来源的字典
        """
        response = self.query_engine.query(question)

        return {
            "answer": str(response),
            "sources": [s.metadata.get('file_name', 'unknown') for s in response.source_nodes]
        }
```

**Step 2: Commit**

```bash
git add src/query/
git commit -m "feat: add RAGQueryEngine"
```

---

## Web UI

### Task 6: Implement Streamlit Web Interface

**Files:**
- Create: `app/web.py`

**Step 1: Create implementation**

Create `app/web.py`:

```python
"""
Streamlit Web 界面
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.config import get_settings
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine

# 页面配置
st.set_page_config(
    page_title="LlamaIndex RAG 知识库",
    page_icon="📚",
    layout="wide"
)

# 初始化 session state
if "index_manager" not in st.session_state:
    st.session_state.index_manager = None
if "query_engine" not in st.session_state:
    st.session_state.query_engine = None
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False


def main():
    """主界面"""
    st.title("📚 LlamaIndex 技术文档知识库")
    st.markdown("---")

    settings = get_settings()

    # 侧边栏
    with st.sidebar:
        st.header("📁 文档管理")

        docs_dir = st.text_input("文档目录", value=settings.docs_dir)

        if st.button("🔄 加载文档并构建索引"):
            with st.spinner("正在加载文档..."):
                loader = MarkdownLoader()
                try:
                    documents = loader.load_documents(docs_dir)
                    st.success(f"✓ 加载了 {len(documents)} 个文档")

                    with st.spinner("正在构建索引..."):
                        manager = VectorIndexManager()
                        index = manager.create_index(documents)
                        st.session_state.index_manager = manager

                        query_engine = RAGQueryEngine(index)
                        st.session_state.query_engine = query_engine
                        st.session_state.documents_loaded = True

                        st.success("✓ 索引构建完成")
                except Exception as e:
                    st.error(f"✗ 错误: {e}")

        st.markdown("---")
        st.markdown("### 📖 使用说明")
        st.markdown("""
        1. 选择包含 Markdown 文档的目录
        2. 点击"加载文档并构建索引"
        3. 在主界面输入问题
        4. 查看答案和来源
        """)

    # 主区域
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("📖 知识库问答")

        question = st.text_area(
            "你的问题",
            placeholder="例如：这个项目是做什么的？",
            height=100
        )

        if st.button("🔍 搜索", type="primary", use_container_width=True):
            if not st.session_state.documents_loaded:
                st.warning("请先加载文档并构建索引")
            elif question:
                with st.spinner("正在思考..."):
                    try:
                        result = st.session_state.query_engine.query(question)

                        st.markdown("### 📝 答案")
                        st.write(result["answer"])

                        if result["sources"]:
                            st.markdown("### 📚 来源")
                            for source in result["sources"]:
                                st.write(f"• {source}")
                    except Exception as e:
                        st.error(f"✗ 查询失败: {e}")

    with col2:
        st.header("📊 状态")
        if st.session_state.documents_loaded:
            st.success("✓ 索引已就绪")
        else:
            st.info("等待加载文档...")


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add app/web.py
git commit -m "feat: add Streamlit web interface"
```

---

## Testing & Documentation

### Task 7: Add Sample Documents and Tests

**Files:**
- Create: `data/docs/example.md`
- Create: `tests/integration/test_e2e.py`

**Step 1: Create sample document**

Create `data/docs/example.md`:

```markdown
# LlamaIndex 示例文档

## 简介

这是一个示例文档，用于测试 LlamaIndex RAG 系统。

## 主要特性

LlamaIndex 是一个专门用于构建 LLM 应用的数据框架，特别擅长 RAG（检索增强生成）。

## 核心概念

### Documents

文档是 LlamaIndex 中的基本数据单元。

### Nodes

节点是文档的切分单元，包含文本块和元数据。

### Indexes

索引是对节点的组织和向量化，用于快速检索。
```

**Step 2: Create integration test**

Create `tests/integration/test_e2e.py`:

```python
"""
端到端集成测试
"""
import pytest
from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine


@pytest.mark.integration
def test_full_rag_workflow():
    """测试完整的 RAG 工作流"""
    # 1. 加载文档
    loader = MarkdownLoader()
    documents = loader.load_documents("data/docs")
    assert len(documents) > 0

    # 2. 创建索引
    manager = VectorIndexManager()
    index = manager.create_index(documents)
    assert index is not None

    # 3. 查询
    query_engine = RAGQueryEngine(index)
    result = query_engine.query("LlamaIndex 是什么？")

    assert "answer" in result
    assert "sources" in result
    assert len(result["answer"]) > 0
```

**Step 3: Commit**

```bash
git add data/docs/ tests/integration/
git commit -m "test: add sample documents and integration tests"
```

---

### Task 8: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `RUN_GUIDE.md`

**Step 1: Update README** - Add comprehensive usage guide

**Step 2: Create RUN_GUIDE.md** with detailed setup instructions

**Step 3: Commit**

```bash
git add README.md RUN_GUIDE.md
git commit -m "docs: update documentation"
```

---

## Final Steps

### Task 9: Final Verification

**Step 1: Run all tests**

```bash
pytest tests/ -v
```

**Step 2: Test the application**

```bash
# 确保 Ollama 正在运行
ollama serve

# 在另一个终端
streamlit run app/web.py
```

**Step 3: Final commit**

```bash
git add .
git commit -m "chore: final cleanup and verification"
```

---

## Implementation Complete

After all tasks are completed, the project should have:

- ✅ 完整的项目结构
- ✅ 配置管理模块
- ✅ Markdown 文档加载器
- ✅ 向量索引管理器
- ✅ RAG 查询引擎
- ✅ Streamlit Web 界面
- ✅ 单元测试和集成测试
- ✅ 示例文档
- ✅ 完整文档
