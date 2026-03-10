"""
日志工具模块

提供统一的日志接口，使用标准 logging 模块。
"""
import logging
import sys
from typing import Optional

# 全局 logger 缓存
_loggers: dict[str, logging.Logger] = {}


def setup_logging(level: str = 'INFO') -> None:
    """
    设置全局日志配置

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置根 logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取或创建 Logger 实例

    Args:
        name: Logger 名称

    Returns:
        Logger 实例
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]
