# tests/test_structured_output.py
import json
import pytest
from src.structured_output import StructuredExtractor

def test_extract_person_info():
    """测试提取人物信息"""
    extractor = StructuredExtractor(provider="glm")
    text = "张三，男，30岁，是一名软件工程师，居住在北京。"
    result = extractor.extract_person_info(text)
    assert isinstance(result, dict)
    assert "name" in result

def test_extract_with_json_output():
    """测试JSON格式输出"""
    extractor = StructuredExtractor(provider="glm")
    result = extractor.extract_person_info("李四是一名教师")
    # 验证是有效的JSON
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
