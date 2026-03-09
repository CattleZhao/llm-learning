"""
日志工具测试
"""
import logging
import pytest
from src.utils.logger import get_logger, setup_logging


def test_get_logger_returns_logger():
    """测试 get_logger 返回正确的 logger 实例"""
    logger = get_logger('test')
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'test'


def test_get_logger_same_instance():
    """测试相同名称返回同一个实例"""
    logger1 = get_logger('test')
    logger2 = get_logger('test')
    assert logger1 is logger2


def test_different_names_different_loggers():
    """测试不同名称返回不同实例"""
    logger1 = get_logger('test1')
    logger2 = get_logger('test2')
    assert logger1 is not logger2


def test_setup_logging_sets_level():
    """测试 setup_logging 设置正确的日志级别"""
    setup_logging('DEBUG')
    logger = get_logger('test')
    # 获取根日志记录器的级别
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_setup_logging_info_level():
    """测试 setup_logging 设置 INFO 级别"""
    setup_logging('INFO')
    logger = get_logger('test')
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_logger_has_handlers():
    """测试 logger 有正确的处理器"""
    setup_logging('INFO')
    logger = get_logger('test')
    # 根 logger 应该有处理器
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0


def test_logger_can_log_messages(caplog):
    """测试 logger 可以记录消息"""
    logger = get_logger('test_capture')
    setup_logging('INFO')

    with caplog.at_level(logging.INFO):
        logger.info("Test message")

    assert "Test message" in caplog.text
