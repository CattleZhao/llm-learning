"""
端到端集成测试

测试完整的 RAG 流程：文档加载 -> 索引创建 -> 查询
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from src.loaders.markdown_loader import MarkdownLoader
from src.indexes.vector_index import VectorIndexManager
from src.query.query_engine import RAGQueryEngine


@pytest.fixture(autouse=True)
def reset_settings():
    """在每个测试前重置设置"""
    from src.config import reset_settings
    reset_settings()
    yield


@pytest.fixture
def mock_env(monkeypatch):
    """配置测试环境变量"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://test.anthropic.com")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("EMBED_MODEL", "nomic-embed-text")
    monkeypatch.setenv("STORAGE_DIR", "/tmp/test_chroma_storage")
    monkeypatch.setenv("DOCS_DIR", "data/docs")


@pytest.fixture
def temp_docs_dir(tmp_path):
    """创建临时文档目录"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # 创建测试文档
    (docs_dir / "test1.md").write_text("""
# Test Document 1

This is the first test document.

## Content

It contains information about testing RAG systems.
The system should be able to retrieve this information.
    """)

    (docs_dir / "test2.md").write_text("""
# Test Document 2

This is the second test document.

## Features

- Feature 1: Semantic search
- Feature 2: Answer generation
- Feature 3: Source attribution
    """)

    return str(docs_dir)


@pytest.mark.integration
def test_end_to_end_rag_flow(temp_docs_dir, mock_env):
    """测试完整的 RAG 流程"""

    # 步骤 1: 加载文档
    loader = MarkdownLoader()
    documents = loader.load_documents(temp_docs_dir, recursive=True)

    assert len(documents) == 2
    assert any("Test Document 1" in doc.text for doc in documents)
    assert any("Test Document 2" in doc.text for doc in documents)

    # 步骤 2: 创建索引（使用 mock 避免实际 API 调用）
    with patch('src.indexes.vector_index.MarkdownNodeParser') as mock_parser_class, \
         patch('src.indexes.vector_index.chromadb.PersistentClient') as mock_client_class, \
         patch('src.indexes.vector_index.ChromaVectorStore') as mock_store_class, \
         patch('src.indexes.vector_index.VectorStoreIndex') as mock_index_class:

        # 配置 mocks
        mock_parser = Mock()
        mock_parser.get_nodes_from_documents.return_value = ["node1", "node2"]
        mock_parser_class.return_value = mock_parser

        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_index = Mock()
        mock_index_class.return_value = mock_index

        # 创建索引管理器并创建索引
        index_manager = VectorIndexManager()
        index = index_manager.create_index(documents)

        assert index is not None
        mock_parser.get_nodes_from_documents.assert_called_once_with(documents)

    # 步骤 3: 创建查询引擎
    query_engine = RAGQueryEngine(index=index)
    assert query_engine.index is not None
    assert query_engine.query_engine is not None

    # 步骤 4: 执行查询（使用 mock）
    mock_response = Mock()
    mock_response.__str__ = lambda self: "This is a test answer about RAG systems."

    source_node = Mock()
    source_node.metadata = {"file_name": "test1.md"}
    mock_response.source_nodes = [source_node]

    query_engine.query_engine.query.return_value = mock_response

    result = query_engine.query("What is this document about?")

    assert result is not None
    assert "answer" in result
    assert "sources" in result
    assert result["answer"] == "This is a test answer about RAG systems."
    assert "test1.md" in result["sources"]


@pytest.mark.integration
def test_document_loading_with_empty_directory(tmp_path, mock_env):
    """测试加载空目录"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    loader = MarkdownLoader()

    with pytest.raises(ValueError, match="No files found"):
        loader.load_documents(str(empty_dir))


@pytest.mark.integration
def test_document_loading_with_nested_directories(tmp_path, mock_env):
    """测试加载嵌套目录"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # 创建嵌套结构
    subdir = docs_dir / "subdir"
    subdir.mkdir()

    (docs_dir / "root.md").write_text("# Root Document")
    (subdir / "nested.md").write_text("# Nested Document")

    loader = MarkdownLoader()

    # 非递归
    docs_non_recursive = loader.load_documents(str(docs_dir), recursive=False)
    assert len(docs_non_recursive) == 1

    # 递归
    docs_recursive = loader.load_documents(str(docs_dir), recursive=True)
    assert len(docs_recursive) == 2


@pytest.mark.integration
def test_query_engine_without_index(mock_env):
    """测试在没有索引的情况下查询"""
    query_engine = RAGQueryEngine(index=None)

    with pytest.raises(ValueError, match="Query engine not initialized"):
        query_engine.query("Test question")


@pytest.mark.integration
def test_query_engine_set_index(mock_env):
    """测试动态设置索引"""
    query_engine = RAGQueryEngine(index=None)
    assert query_engine.query_engine is None

    mock_index = Mock()
    mock_query_engine = Mock()
    mock_index.as_query_engine.return_value = mock_query_engine

    query_engine.set_index(mock_index)

    assert query_engine.index is mock_index
    assert query_engine.query_engine is not None
    mock_index.as_query_engine.assert_called_once()


@pytest.mark.integration
def test_actual_document_files_exist():
    """测试实际示例文档存在"""
    project_root = Path(__file__).parent.parent.parent
    docs_dir = project_root / "data" / "docs"

    assert docs_dir.exists()
    assert docs_dir.is_dir()

    # 检查示例文档
    example_md = docs_dir / "example.md"
    assert example_md.exists()

    python_tips_md = docs_dir / "python-tips.md"
    assert python_tips_md.exists()

    ai_concepts_md = docs_dir / "ai-concepts.md"
    assert ai_concepts_md.exists()

    # 验证文档内容不为空
    assert example_md.read_text().strip()
    assert python_tips_md.read_text().strip()
    assert ai_concepts_md.read_text().strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
