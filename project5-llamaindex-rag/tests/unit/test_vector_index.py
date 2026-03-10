"""
测试 VectorIndexManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llama_index.core import Document
from src.indexes.vector_index import VectorIndexManager


@pytest.fixture
def mock_settings(monkeypatch):
    """配置测试环境变量"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("EMBED_MODEL", "nomic-embed-text")
    monkeypatch.setenv("STORAGE_DIR", "/tmp/test_storage")


@pytest.fixture
def vector_index_manager(mock_settings):
    """创建 VectorIndexManager 实例"""
    # 重置设置以使用新的环境变量
    from src.config import reset_settings
    reset_settings()
    return VectorIndexManager()


@pytest.fixture
def sample_documents():
    """创建示例文档"""
    return [
        Document(text="# Test Document 1\n\nContent of test 1.", metadata={"file_name": "test1.md"}),
        Document(text="# Test Document 2\n\nContent of test 2.", metadata={"file_name": "test2.md"}),
    ]


def test_vector_index_manager_initialization(vector_index_manager):
    """测试索引管理器初始化"""
    assert vector_index_manager.index is None
    assert vector_index_manager.settings is not None


@patch('src.indexes.vector_index.MarkdownNodeParser')
@patch('src.indexes.vector_index.chromadb.PersistentClient')
@patch('src.indexes.vector_index.ChromaVectorStore')
@patch('src.indexes.vector_index.VectorStoreIndex')
def test_create_index(
    mock_vector_store_index,
    mock_chroma_store,
    mock_persistent_client,
    mock_node_parser,
    vector_index_manager,
    sample_documents
):
    """测试创建索引"""
    # 配置 mock
    mock_parser_instance = Mock()
    mock_parser_instance.get_nodes_from_documents.return_value = ["node1", "node2"]
    mock_node_parser.return_value = mock_parser_instance

    mock_client_instance = Mock()
    mock_collection = Mock()
    mock_client_instance.get_or_create_collection.return_value = mock_collection
    mock_persistent_client.return_value = mock_client_instance

    mock_index_instance = Mock()
    mock_vector_store_index.return_value = mock_index_instance

    # 创建索引
    index = vector_index_manager.create_index(sample_documents)

    # 验证
    assert index is not None
    mock_node_parser.assert_called_once()
    mock_parser_instance.get_nodes_from_documents.assert_called_once_with(sample_documents)
    mock_persistent_client.assert_called_once()
    mock_client_instance.get_or_create_collection.assert_called_once_with("docs")
    mock_chroma_store.assert_called_once()
    mock_vector_store_index.assert_called_once()


def test_configure_llamaindex(vector_index_manager):
    """测试 LlamaIndex 配置"""
    from llama_index.core import Settings

    # 验证 LLM 配置
    assert Settings.llm is not None
    # api_key 是私有属性，只验证对象存在
    assert hasattr(Settings.llm, 'model')

    # 验证嵌入模型配置
    assert Settings.embed_model is not None
