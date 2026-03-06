# tests/test_document_loader.py
import pytest
from src.document_loader import DocumentLoader

def test_load_txt_file():
    """测试加载TXT文件"""
    loader = DocumentLoader()
    # 创建测试文件
    test_file = "data/documents/test.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("这是一段测试文本。")

    docs = loader.load_file(test_file)

    assert len(docs) > 0
    assert "测试文本" in docs[0].page_content

    # 清理
    import os
    os.remove(test_file)

def test_unsupported_format():
    """测试不支持的格式"""
    loader = DocumentLoader()
    with pytest.raises(ValueError):
        loader.load_file("test.xyz")
