"""
配置管理模块

Project 6: 高级 Agent 应用
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MemorySettings:
    """长记忆系统配置"""

    # 向量存储配置
    chroma_persist_dir: Path = field(
        default_factory=lambda: Path("memory/chroma"),
        metadata={"description": "Chroma DB 持久化目录"}
    )

    # Embedding 模型配置 (使用 Ollama)
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBED_MODEL", "nomic-embed-text"),
        metadata={"description": "Ollama embedding 模型名称"}
    )

    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        metadata={"description": "Ollama 服务地址"}
    )

    # 相似度检索配置
    similarity_top_k: int = field(
        default=5,
        metadata={"description": "检索相似样本数量"}
    )

    similarity_threshold: float = field(
        default=0.7,
        metadata={"description": "相似度阈值"}
    )

    # 规则学习配置
    enable_auto_learning: bool = field(
        default=True,
        metadata={"description": "是否启用自动规则学习"}
    )

    candidate_rules_dir: Path = field(
        default_factory=lambda: Path("memory/pending_rules"),
        metadata={"description": "候选规则存储目录"}
    )


@dataclass
class Settings:
    """项目配置"""

    # ========== LLM 配置 ==========
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    anthropic_base_url: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    )
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    )

    # ========== Ollama 配置 ==========
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    # ========== 记忆配置 ==========
    memory_backend: str = field(
        default_factory=lambda: os.getenv("MEMORY_BACKEND", "local")  # local, postgres, redis
    )
    memory_store_path: str = field(
        default_factory=lambda: os.getenv("MEMORY_STORE_PATH", "data/memory")
    )

    # ========== 长记忆系统配置 ==========
    memory: MemorySettings = field(
        default_factory=MemorySettings,
        metadata={"description": "长记忆系统配置"}
    )

    # ========== 评估配置 ==========
    enable_evaluation: bool = field(
        default_factory=lambda: os.getenv("ENABLE_EVALUATION", "true").lower() == "true"
    )
    eval_dataset_path: str = field(
        default_factory=lambda: os.getenv("EVAL_DATASET_PATH", "data/eval")
    )

    # ========== 工具配置 ==========
    enable_tool_validation: bool = field(
        default_factory=lambda: os.getenv("ENABLE_TOOL_VALIDATION", "true").lower() == "true"
    )

    # ========== JADX 配置 ==========
    jadx_mcp_server_path: str = field(
        default_factory=lambda: os.getenv("JADX_MCP_SERVER_PATH", "/path/to/jadx-mcp-server")
    )
    jadx_gui_path: Optional[str] = field(
        default_factory=lambda: os.getenv("JADX_GUI_PATH")
    )

    # ========== 日志配置 ==========
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
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
    """获取全局配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """重置全局配置实例（主要用于测试）"""
    global _settings
    _settings = None
