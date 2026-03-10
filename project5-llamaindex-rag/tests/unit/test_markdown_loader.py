"""
测试 MarkdownLoader
"""
import pytest
from pathlib import Path
from src.loaders.markdown_loader import MarkdownLoader


@pytest.fixture
def markdown_loader():
    """创建 MarkdownLoader 实例"""
    return MarkdownLoader()


@pytest.fixture
def temp_docs_dir(tmp_path):
    """创建临时测试文档目录"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # 创建测试文件
    (docs_dir / "test1.md").write_text("# Test Document 1\n\nContent of test 1.")
    (docs_dir / "test2.md").write_text("# Test Document 2\n\nContent of test 2.")

    # 创建子目录
    subdir = docs_dir / "subdir"
    subdir.mkdir()
    (subdir / "test3.md").write_text("# Test Document 3\n\nContent of test 3.")

    return str(docs_dir)


def test_load_documents_from_directory(markdown_loader, temp_docs_dir):
    """测试从目录加载文档"""
    documents = markdown_loader.load_documents(temp_docs_dir, recursive=False)

    # 非递归应该只加载根目录的文档
    assert len(documents) == 2
    assert "Test Document 1" in documents[0].text
    assert "Test Document 2" in documents[1].text


def test_load_documents_recursive(markdown_loader, temp_docs_dir):
    """测试递归加载文档"""
    documents = markdown_loader.load_documents(temp_docs_dir, recursive=True)

    # 递归应该加载所有文档，包括子目录
    assert len(documents) == 3
    texts = [doc.text for doc in documents]
    assert any("Test Document 1" in text for text in texts)
    assert any("Test Document 2" in text for text in texts)
    assert any("Test Document 3" in text for text in texts)


def test_load_documents_empty_directory(markdown_loader, tmp_path):
    """测试加载空目录"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # LlamaIndex 的 SimpleDirectoryReader 在空目录时会抛出 ValueError
    with pytest.raises(ValueError, match="No files found"):
        markdown_loader.load_documents(str(empty_dir))


def test_load_documents_nonexistent_directory(markdown_loader):
    """测试加载不存在的目录"""
    with pytest.raises(Exception):
        markdown_loader.load_documents("/nonexistent/directory")
