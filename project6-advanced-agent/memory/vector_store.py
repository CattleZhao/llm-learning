"""
向量存储模块

使用 Chroma DB 存储 APK 分析结果的向量表示
"""
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from agents.base import AgentResponse
from config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储封装类"""

    def __init__(self, persist_dir: Optional[str] = None):
        """
        初始化向量存储

        Args:
            persist_dir: Chroma 持久化目录
        """
        settings = get_settings()

        if persist_dir is None:
            persist_dir = str(settings.memory.chroma_persist_dir)

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Chroma 客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="apk_analyses",
            metadata={"description": "APK analysis results"}
        )

        # 初始化 embedding 模型 (延迟加载)
        self.embedding_model = None
        self._embedding_model_name = settings.memory.embedding_model

        logger.info(f"VectorStore initialized at {self.persist_dir}")

    def _get_embedding_model(self):
        """延迟加载 embedding 模型"""
        if self.embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(self._embedding_model_name)
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(
                    f"Failed to load sentence-transformers model '{self._embedding_model_name}'. "
                    "Please ensure sentence-transformers is installed with PyTorch support. "
                    "Try: pip install sentence-transformers torch"
                )
        return self.embedding_model

    def _embed_with_retry(self, text: str, max_retries: int = 3) -> List[float]:
        """
        生成 embedding，带重试机制

        Args:
            text: 输入文本
            max_retries: 最大重试次数

        Returns:
            embedding 向量
        """
        for attempt in range(max_retries):
            try:
                model = self._get_embedding_model()
                return model.encode(
                    text,
                    convert_to_numpy=True,
                    show_progress_bar=False
                ).tolist()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Embedding failed after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Embedding failed (attempt {attempt + 1}), retrying...")
                time.sleep(2 ** attempt)

    def store_analysis(
        self,
        apk_hash: str,
        analysis_result: AgentResponse,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        存储分析结果

        Args:
            apk_hash: APK SHA256 hash
            analysis_result: 分析结果
            metadata: 额外的元数据

        Returns:
            存储的文档 ID
        """
        if not apk_hash:
            raise ValueError("apk_hash is required")

        if not analysis_result.content:
            raise ValueError("analysis_result.content is required")

        # 合并元数据
        final_metadata = metadata or {}
        final_metadata.update({
            "apk_hash": apk_hash,
            "risk_level": analysis_result.metadata.get("risk_level", "UNKNOWN"),
            "package": analysis_result.metadata.get("package", ""),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })

        # 使用 summary 或 content 生成 embedding
        text_to_embed = (
            analysis_result.metadata.get("summary") or
            analysis_result.content[:1000]
        )

        embedding = self._embed_with_retry(text_to_embed)

        # 删除已存在的（如果有的话）
        try:
            self.collection.delete(ids=[apk_hash])
        except:
            pass

        # 存储到 Chroma
        self.collection.add(
            ids=[apk_hash],
            embeddings=[embedding],
            documents=[analysis_result.content],
            metadatas=[final_metadata]
        )

        logger.info(f"Stored analysis for {apk_hash}")
        return apk_hash

    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相似分析

        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            相似分析列表
        """
        settings = get_settings()
        if n_results is None:
            n_results = settings.memory.similarity_top_k

        query_embedding = self._embed_with_retry(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )

        # 格式化结果
        formatted_results = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "apk_hash": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if "distances" in results else None
                })

        return formatted_results

    def get_by_hash(self, apk_hash: str) -> Optional[Dict[str, Any]]:
        """
        根据 hash 获取分析记录

        Args:
            apk_hash: APK hash

        Returns:
            分析记录，如果不存在返回 None
        """
        results = self.collection.get(
            ids=[apk_hash],
            include=["documents", "metadatas"]
        )

        if not results["ids"]:
            return None

        return {
            "apk_hash": results["ids"][0],
            "content": results["documents"][0] if results["documents"] else "",
            "metadata": results["metadatas"][0] if results["metadatas"] else {}
        }

    def delete_by_hash(self, apk_hash: str) -> bool:
        """
        删除分析记录

        Args:
            apk_hash: APK hash

        Returns:
            是否删除成功
        """
        try:
            self.collection.delete(ids=[apk_hash])
            return True
        except Exception as e:
            logger.error(f"Failed to delete {apk_hash}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        count = self.collection.count()

        # 获取所有记录的元数据
        all_data = self.collection.get(include=["metadatas"])

        high_risk_count = 0
        if all_data.get("metadatas"):
            high_risk_count = sum(
                1 for m in all_data["metadatas"]
                if m.get("risk_level") in ["HIGH", "CRITICAL"]
            )

        return {
            "total_count": count,
            "high_risk_count": high_risk_count
        }


def get_vector_store() -> VectorStore:
    """获取 VectorStore 单例"""
    return VectorStore()
