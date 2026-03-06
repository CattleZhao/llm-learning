# tests/test_embeddings.py
import pytest
from src.embeddings import EmbeddingModel

def test_create_embedding():
    """测试创建嵌入向量"""
    embedder = EmbeddingModel()
    text = "这是一段测试文本"

    embedding = embedder.embed_query(text)

    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)

def test_embed_documents():
    """测试批量嵌入"""
    embedder = EmbeddingModel()
    texts = ["文本1", "文本2", "文本3"]

    embeddings = embedder.embed_documents(texts)

    assert len(embeddings) == len(texts)
    assert all(isinstance(emb, list) for emb in embeddings)

def test_embedding_dimension():
    """测试向量维度一致性"""
    embedder = EmbeddingModel()
    text1 = "第一个文本"
    text2 = "第二个文本"

    emb1 = embedder.embed_query(text1)
    emb2 = embedder.embed_query(text2)

    # 向量维度应该相同
    assert len(emb1) == len(emb2)
