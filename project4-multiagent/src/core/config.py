"""
配置管理模块

负责管理所有项目配置，包括 API key、模型设置、代码执行配置等。
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class Config:
    """
    项目配置类

    所有配置都可以通过环境变量设置，如果没有设置则使用默认值。
    """

    # ========== LLM 配置 ==========
    api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    api_base: str = field(default_factory=lambda: os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'))
    model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', 'gpt-4o'))
    temperature: float = field(default_factory=lambda: float(os.getenv('TEMPERATURE', '0.7')))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('MAX_TOKENS', '2000')))

    # ========== 代码执行配置 ==========
    use_docker: bool = field(default_factory=lambda: os.getenv('USE_DOCKER', 'false').lower() == 'true')
    work_dir: str = field(default_factory=lambda: os.getenv('CODE_EXECUTION_WORK_DIR', './outputs'))

    # ========== 日志配置 ==========
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))

    # ========== Agent 配置 ==========
    timeout: int = field(default_factory=lambda: int(os.getenv('AGENT_TIMEOUT', '60')))
    max_consecutive_auto_reply: int = field(default_factory=lambda: int(os.getenv('MAX_CONSECUTIVE_AUTO_REPLY', '10')))

    def __post_init__(self):
        """初始化后验证"""
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. "
                "请设置环境变量或在 .env 文件中配置你的 API key。"
            )

        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)

    def get_llm_config(self) -> Dict[str, Any]:
        """
        获取 AutoGen 需要的 LLM 配置字典

        Returns:
            包含模型配置的字典
        """
        return {
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.api_base,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def get_code_execution_config(self) -> Dict[str, Any]:
        """
        获取代码执行配置

        Returns:
            包含代码执行配置的字典
        """
        return {
            "work_dir": self.work_dir,
            "use_docker": self.use_docker,
        }


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
