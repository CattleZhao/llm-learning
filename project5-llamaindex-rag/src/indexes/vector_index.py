"""
向量索引管理器

管理 LlamaIndex 向量索引的创建和配置
使用 ChromaDB 作为向量存储
混合架构: Anthropic LLM + Hugging Face Embedding
"""
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from src.config import get_settings


class VectorIndexManager:
    """向量索引管理器"""

    def __init__(self):
        """初始化索引管理器"""
        self.settings = get_settings()
        self._configure_llamaindex()
        self.index = None

    def _configure_llamaindex(self):
        """配置 LlamaIndex 全局设置"""
        # 配置 Anthropic LLM
        Settings.llm = Anthropic(
            api_key=self.settings.anthropic_api_key,
            base_url=self.settings.anthropic_base_url,
            model=self.settings.anthropic_model
        )
        # 配置 Hugging Face 嵌入模型
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=self.settings.hf_embed_model,
            device=self.settings.embed_device
        )

    def create_index(self, documents):
        """
        从文档创建向量索引

        Args:
            documents: Document 对象列表

        Returns:
            VectorStoreIndex 实例
        """
        # 使用 Markdown 节点解析器
        parser = MarkdownNodeParser(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
        nodes = parser.get_nodes_from_documents(documents)

        # 配置 ChromaDB 向量存储
        chroma_client = chromadb.PersistentClient(path=self.settings.storage_dir)
        chroma_store = ChromaVectorStore(
            chroma_collection=chroma_client.get_or_create_collection("docs")
        )

        # 创建索引
        self.index = VectorStoreIndex(nodes, vector_store=chroma_store)
        return self.index
