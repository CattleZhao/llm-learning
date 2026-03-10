"""
配置管理模块

混合架构: Anthropic LLM + Ollama Embedding
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """项目配置 - 混合 LLM 架构"""

    # ========== Anthropic LLM 配置 ==========
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    anthropic_base_url: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    )
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    )

    # ========== Ollama 嵌入配置 ==========
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    embed_model: str = field(
        default_factory=lambda: os.getenv("EMBED_MODEL", "nomic-embed-text")
    )

    # ========== 文档配置 ==========
    docs_dir: str = field(
        default_factory=lambda: os.getenv("DOCS_DIR", "data/docs")
    )

    # ========== 存储配置 ==========
    storage_dir: str = field(
        default_factory=lambda: os.getenv("STORAGE_DIR", "storage/chroma")
    )

    # ========== 索引参数 ==========
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "512"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "50"))
    )
    top_k: int = field(
        default_factory=lambda: int(os.getenv("TOP_K", "3"))
    )

    def __post_init__(self):
        """初始化后验证"""
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. "
                "请设置环境变量或在 .env 文件中配置你的 API key。"
            )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取全局配置实例（单例模式）

    Returns:
        Settings 实例
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """
    重置全局配置实例（主要用于测试）

    WARNING: 生产环境中不应使用此函数
    """
    global _settings
    _settings = None
