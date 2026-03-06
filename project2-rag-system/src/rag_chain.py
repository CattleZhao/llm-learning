# src/rag_chain.py
import os
from dotenv import load_dotenv
load_dotenv()

from typing import List
from src.vector_store import VectorStore
from src.embeddings import EmbeddingModel
from src.llm_client import SimpleLLMClient

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
        self.temperature = temperature

        # 初始化LLM客户端
        self.llm = SimpleLLMClient()

    def ask(self, question: str) -> str:
        """
        提问并获取答案

        Args:
            question: 用户问题

        Returns:
            答案文本
        """
        # 检索相关文档
        docs = self.vector_store.search(
            question,
            self.embeddings,
            k=self.top_k
        )

        if not docs:
            return "抱歉，知识库中没有找到相关信息。"

        # 构建上下文
        context = self._build_context(docs)

        # 生成提示词
        prompt = RAG_TEMPLATE.format(
            context=context,
            question=question
        )

        # 生成答案
        return self.llm.generate(prompt, temperature=self.temperature)

    def ask_with_sources(self, question: str) -> dict:
        """
        提问并获取答案和来源

        Args:
            question: 用户问题

        Returns:
            包含answer和sources的字典
        """
        # 检索文档（带分数）
        results = self.vector_store.search_with_score(
            question,
            self.embeddings,
            k=self.top_k
        )

        if not results:
            return {
                "answer": "抱歉，知识库中没有找到相关信息。",
                "sources": [],
                "retrieved_docs": 0
            }

        docs = [doc for doc, _ in results]
        sources = list(set(
            doc.metadata.get("source", "未知来源")
            for doc in docs
        ))

        # 生成答案
        context = self._build_context(docs)
        prompt = RAG_TEMPLATE.format(
            context=context,
            question=question
        )
        answer = self.llm.generate(prompt)

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_docs": len(docs)
        }

    def _build_context(self, docs: List) -> str:
        """
        构建上下文字符串

        Args:
            docs: 文档列表

        Returns:
            格式化的上下文字符串
        """
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            content = doc.page_content
            context_parts.append(f"[文档{i} 来自 {source}]\n{content}")

        return "\n\n".join(context_parts)
