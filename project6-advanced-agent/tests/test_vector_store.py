import pytest
from pathlib import Path
from memory.vector_store import VectorStore
from agents.base import AgentResponse

@pytest.fixture
def vector_store(tmp_path):
    """创建临时 VectorStore 实例"""
    store = VectorStore(persist_dir=str(tmp_path / "chroma"))
    return store

@pytest.fixture
def mock_analysis_result():
    """模拟分析结果"""
    return AgentResponse(
        content="# APK安全分析报告\n\n检测到高危恶意软件",
        metadata={
            "apk_path": "/test/app.apk",
            "risk_level": "HIGH",
            "package": "com.malware.test",
            "summary": "检测到高危恶意软件，具有短信盗窃行为"
        }
    )

def test_store_and_retrieve(vector_store, mock_analysis_result):
    """测试存储和检索"""
    apk_hash = "test123"

    # 存储
    result_id = vector_store.store_analysis(
        apk_hash=apk_hash,
        analysis_result=mock_analysis_result
    )

    assert result_id == apk_hash

    # 检索
    retrieved = vector_store.get_by_hash(apk_hash)
    assert retrieved is not None
    assert retrieved["metadata"]["package"] == "com.malware.test"

def test_search_similar(vector_store, mock_analysis_result):
    """测试相似度检索"""
    apk_hash = "test456"

    vector_store.store_analysis(
        apk_hash=apk_hash,
        analysis_result=mock_analysis_result
    )

    # 搜索相似
    results = vector_store.search_similar(
        query="恶意软件短信",
        n_results=1
    )

    assert len(results) > 0
    assert results[0]["apk_hash"] == apk_hash

def test_get_stats(vector_store):
    """测试统计信息"""
    stats = vector_store.get_stats()

    assert "total_count" in stats
    assert "high_risk_count" in stats
