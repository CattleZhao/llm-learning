"""
日志工具模块

提供统一的日志功能，使用 Rich 库实现彩色输出和更好的格式化。
"""
import logging
import sys
from typing import Optional

# Rich 是可选的，如果没有安装则使用标准库
try:
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# 全局变量
_loggers: dict = {}
_logging_setup: bool = False


def setup_logging(level: str = 'INFO', rich: Optional[bool] = None) -> None:
    """
    设置全局日志配置

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rich: 是否使用 Rich 彩色输出 (None 表示自动检测)
    """
    global _logging_setup

    if _logging_setup:
        return

    # 转换日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 决定是否使用 Rich
    use_rich = rich if rich is not None else RICH_AVAILABLE

    if use_rich:
        # 使用 Rich 处理器（彩色输出、更好的格式）
        handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            show_path=True,
        )
    else:
        # 使用标准库处理器
        handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(log_level)

    # 设置格式
    if not use_rich:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    _logging_setup = True


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    获取或创建一个日志记录器实例

    Args:
        name: 日志记录器名称
        level: 可选的日志级别

    Returns:
        Logger 实例
    """
    global _loggers

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)

    _loggers[name] = logger

    return logger
