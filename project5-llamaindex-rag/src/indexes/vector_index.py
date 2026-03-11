"""
向量索引管理器

管理 LlamaIndex 向量索引的创建和配置
使用 ChromaDB 作为向量存储
混合架构: Anthropic LLM (原生 SDK) + Hugging Face Embedding
"""
import chromadb
from anthropic import Anthropic
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from src.config import get_settings
from typing import Sequence


class AnthropicLLM(CustomLLM):
    """
    原生 Anthropic SDK 包装器
    绕过 LlamaIndex 的模型验证，支持自定义网关和任意模型名
    """

    context_window: int = 200000
    num_output: int = 4096
    _client: Anthropic = None

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(**kwargs)
        self._client = Anthropic(api_key=api_key, base_url=base_url)
        self._model = model
        self.metadata = LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=model,
        )

    @property
    def metadata(self) -> LLMMetadata:
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def _complete(self, prompt: str, **kwargs) -> CompletionResponse:
        """原生 Anthropic SDK 调用"""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
        )
        return CompletionResponse(text=response.content[0].text)

    def _stream_complete(self, prompt: str, **kwargs):
        """流式输出支持（可选实现）"""
        raise NotImplementedError("流式输出暂未实现")


class VectorIndexManager:
    """向量索引管理器"""

    def __init__(self):
        """初始化索引管理器"""
        self.settings = get_settings()
        self._configure_llamaindex()
        self.index = None

    def _configure_llamaindex(self):
        """配置 LlamaIndex 全局设置"""
        # 配置原生 Anthropic LLM（支持自定义模型名）
        Settings.llm = AnthropicLLM(
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
