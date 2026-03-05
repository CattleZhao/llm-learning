# tests/test_qa_module.py
import pytest
from src.qa_module import QAModule

def test_qa_module_answer_question():
    """测试问答功能"""
    qa = QAModule(provider="glm")  # 使用GLM，因为你有z.ai的key
    answer = qa.ask("什么是人工智能？")
    assert isinstance(answer, str)
    assert len(answer) > 0

def test_qa_module_with_context():
    """测试带上下文的问答"""
    qa = QAModule(provider="glm")
    context = "Python是一种高级编程语言，由Guido van Rossum创建。"
    answer = qa.ask("Python是什么？", context=context)
    assert isinstance(answer, str)
    assert len(answer) > 0
    # 验证答案中提到了上下文的信息
    assert "Python" in answer or "编程" in answer or "语言" in answer
