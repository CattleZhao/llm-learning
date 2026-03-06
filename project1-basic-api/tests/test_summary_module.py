# tests/test_summary_module.py
import pytest
from src.summary_module import SummaryModule

def test_summary_short_text():
    """测试短文本摘要"""
    summary = SummaryModule(provider="glm")
    text = "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
    result = summary.summarize(text)
    assert isinstance(result, str)
    assert len(result) > 0

def test_summary_with_max_length():
    """测试指定最大长度"""
    summary = SummaryModule(provider="glm")
    text = "这是一段测试文本。" * 50  # 长文本
    result = summary.summarize(text, max_length=50)
    assert isinstance(result, str)
    assert len(result) > 0
    # 允许一些误差，但应该比原文短很多
    assert len(result) < len(text) * 0.5
