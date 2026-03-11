"""
向量索引管理器

管理 LlamaIndex 向量索引的创建和配置
使用 ChromaDB 作为向量存储
混合架构: Anthropic LLM (原生 SDK) + Ollama Embedding
"""
import chromadb
from anthropic import Anthropic
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from src.config import get_settings
from typing import Sequence, Optional
import httpx


class AnthropicLLM(CustomLLM):
    """
    原生 Anthropic SDK 包装器
    绕过 LlamaIndex 的模型验证，支持自定义网关和任意模型名
    """

    context_window: int = 200000
    num_output: int = 4096
    model_name: str = "anthropic-custom"

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(**kwargs)
        self._api_key = api_key
        self._base_url = base_url.rstrip('/')
        self._model = model
        # 初始化 Anthropic 客户端
        self._client = Anthropic(api_key=api_key, base_url=base_url)

        # 打印 client 详细信息
        print(f"\n{'='*50}")
        print(f"[DEBUG] AnthropicLLM 初始化:")
        print(f"[DEBUG]   api_key: {api_key[:20]}...{api_key[-10:]}")
        print(f"[DEBUG]   base_url: {base_url}")
        print(f"[DEBUG]   model: {model}")
        print(f"[DEBUG]   client.base_url: {self._client.base_url}")
        print(f"[DEBUG]   client.api_key: {self._client.api_key[:20]}...{self._client.api_key[-10:]}")
        print(f"{'='*50}\n")

        self._metadata = LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=model,
        )

    def _test_direct_api(self):
        """测试直接 API 调用"""
        print(f"[DEBUG] Testing direct API call to {self._base_url}")
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self._base_url}/v1/messages",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": self._model,
                        "max_tokens": 100,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                )
                print(f"[DEBUG] Direct API response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"[DEBUG] Direct API error: {response.text}")
        except Exception as e:
            print(f"[DEBUG] Direct API test failed: {e}")

    @property
    def metadata(self) -> LLMMetadata:
        return self._metadata

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        """同步完成方法"""
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=kwargs.get("max_tokens", 4096),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
            )
            return CompletionResponse(text=response.content[0].text)
        except Exception as e:
            print(f"[DEBUG] Anthropic API Error: {e}")
            print(f"[DEBUG] Using model: {self._model}")
            print(f"[DEBUG] API Key (first 10 chars): {self._client.api_key[:10]}...")
            raise

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs):
        """流式完成方法"""
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
        # 配置 Ollama 嵌入模型
        Settings.embed_model = OllamaEmbedding(
            model_name=self.settings.embed_model,
            base_url=self.settings.ollama_base_url
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
