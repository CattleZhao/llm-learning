"""
配置管理模块

负责管理所有项目配置，包括 API key、模型设置、代码执行配置等。
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class Config:
    """
    项目配置类

    所有配置都可以通过环境变量设置，如果没有设置则使用默认值。
    """

    # ========== Anthropic 配置 ==========
    api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    model: str = field(default_factory=lambda: os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'))
    temperature: float = field(default_factory=lambda: float(os.getenv('TEMPERATURE', '0.7')))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('MAX_TOKENS', '2000')))

    # ========== 代码执行配置 ==========
    work_dir: str = field(default_factory=lambda: os.getenv('CODE_EXECUTION_WORK_DIR', './outputs'))

    # ========== 日志配置 ==========
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))

    def __post_init__(self):
        """初始化后验证"""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. "
                "请设置环境变量或在 .env 文件中配置你的 API key。"
            )

        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)


# ========== 全局配置实例管理 ==========
_config: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例（单例模式）

    Returns:
        Config 实例
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """
    设置全局配置实例（主要用于测试）

    Args:
        config: Config 实例
    """
    global _config
    _config = config
