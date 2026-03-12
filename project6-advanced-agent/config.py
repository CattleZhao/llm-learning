"""
配置管理模块

Project 6: 高级 Agent 应用
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


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
