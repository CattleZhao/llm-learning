"""
测试 RAGQueryEngine
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.query.query_engine import RAGQueryEngine


@pytest.fixture
def mock_settings(monkeypatch):
    """配置测试环境变量"""
    from src.config import reset_settings
    reset_settings()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("EMBED_MODEL", "nomic-embed-text")
    monkeypatch.setenv("TOP_K", "3")
    yield


@pytest.fixture
def reset_conf():
    """重置配置 - 已集成到 mock_settings 中"""
    # 这个 fixture 为了向后兼容保留
    pass


@pytest.fixture
def mock_index():
    """创建模拟索引"""
    index = Mock()
    query_engine = Mock()
    index.as_query_engine.return_value = query_engine
    return index


@pytest.fixture
def mock_response():
    """创建模拟响应"""
    response = Mock()
    response.__str__ = lambda self: "This is a test answer."
    response.source_nodes = []

    # 创建模拟源节点
    source_node1 = Mock()
    source_node1.metadata = {"file_name": "test1.md"}

    source_node2 = Mock()
    source_node2.metadata = {"file_name": "test2.md"}

    response.source_nodes = [source_node1, source_node2]
    return response


def test_query_engine_initialization_with_index(mock_settings, mock_index):
    """测试带索引初始化查询引擎"""
    engine = RAGQueryEngine(index=mock_index)

    assert engine.index is not None
    assert engine.query_engine is not None
    mock_index.as_query_engine.assert_called_once_with(similarity_top_k=3, verbose=True)


def test_query_engine_initialization_without_index(reset_conf):
    """测试不带索引初始化查询引擎"""
    engine = RAGQueryEngine(index=None)

    assert engine.index is None
    assert engine.query_engine is None


def test_query_with_valid_engine(mock_settings, mock_index, mock_response):
    """测试执行查询"""
    engine = RAGQueryEngine(index=mock_index)
    engine.query_engine.query.return_value = mock_response

    result = engine.query("What is the test about?")

    assert result is not None
    assert "answer" in result
    assert "sources" in result
    assert result["answer"] == "This is a test answer."
    assert len(result["sources"]) == 2
    assert "test1.md" in result["sources"]
    assert "test2.md" in result["sources"]


def test_query_without_initialized_engine(reset_conf):
    """测试在未初始化的引擎上执行查询"""
    engine = RAGQueryEngine(index=None)

    with pytest.raises(ValueError, match="Query engine not initialized"):
        engine.query("Test question")


def test_set_index(mock_settings, mock_index):
    """测试设置索引"""
    engine = RAGQueryEngine(index=None)
    assert engine.query_engine is None

    engine.set_index(mock_index)

    assert engine.index is mock_index
    assert engine.query_engine is not None
    mock_index.as_query_engine.assert_called_once_with(similarity_top_k=3, verbose=True)


def test_query_with_no_source_nodes(mock_settings, mock_index):
    """测试没有源节点的查询响应"""
    engine = RAGQueryEngine(index=mock_index)

    # 创建没有源节点的响应
    mock_response = Mock()
    mock_response.__str__ = lambda self: "Answer without sources."
    mock_response.source_nodes = []

    engine.query_engine.query.return_value = mock_response

    result = engine.query("Test question")

    assert result["answer"] == "Answer without sources."
    assert result["sources"] == []


def test_query_with_missing_metadata(mock_settings, mock_index):
    """测试源节点缺少元数据的情况"""
    engine = RAGQueryEngine(index=mock_index)

    # 创建带有不完整元数据的源节点
    mock_response = Mock()
    mock_response.__str__ = lambda self: "Answer with partial metadata."

    source_node1 = Mock()
    source_node1.metadata = {"file_name": "test1.md"}

    source_node2 = Mock()
    source_node2.metadata = {}  # 缺少 file_name

    mock_response.source_nodes = [source_node1, source_node2]
    engine.query_engine.query.return_value = mock_response

    result = engine.query("Test question")

    assert result["answer"] == "Answer with partial metadata."
    assert len(result["sources"]) == 2
    assert "test1.md" in result["sources"]
    assert "unknown" in result["sources"]
