# tests/test_text_splitter.py
import pytest
from src.text_splitter import DocumentSplitter
from src.document_loader import Document

def test_split_long_document():
    """测试分割长文档"""
    splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)

    # 创建一个长文档
    long_text = "这是一句话。" * 50
    doc = Document(page_content=long_text, metadata={"source": "test.txt"})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1
    # 每个块应该在合理范围内
    assert all(len(chunk.page_content) <= 150 for chunk in chunks)  # 允许一些误差

def test_split_preserves_metadata():
    """测试分割保留元数据"""
    splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)

    doc = Document(
        page_content="测试内容" * 50,
        metadata={"source": "test.txt", "page": 1}
    )

    chunks = splitter.split_documents([doc])

    # 所有块都应该保留原始元数据
    assert all(chunk.metadata.get("source") == "test.txt" for chunk in chunks)
    assert all(chunk.metadata.get("page") == 1 for chunk in chunks)
