import pytest
from pathlib import Path
from memory.document_importer import DocumentImporter

@pytest.fixture
def importer(tmp_path):
    """创建临时 importer 实例"""
    return DocumentImporter()

@pytest.fixture
def sample_text_file(tmp_path):
    """创建测试文本文件"""
    text_path = tmp_path / "test_report.txt"
    text_path.write_text("""
    APK 安全分析报告

    包名: com.malware.trojan
    恶意软件家族: TrojanAgent
    风险等级: CRITICAL

    威胁指标:
    - 192.168.1.100
    - malware.c2-server.com

    恶意行为:
    - 发送 premium 短信
    - 窃取通讯录
    - 远程控制

    权限:
    - SEND_SMS
    - READ_CONTACTS
    - ACCESS_FINE_LOCATION

    该木马具有典型的短信盗窃行为，会后台发送
    premium 短信并删除发送记录。
    """, encoding="utf-8")
    return text_path

def test_import_text_file(importer, sample_text_file):
    """测试文本文件导入"""
    result = importer.import_text_file(str(sample_text_file), extract_structured=False)

    assert result is not None
    assert result["source_file"] == sample_text_file.name
    assert "summary" in result

def test_extract_with_llm_mock(importer, sample_text_file):
    """测试 LLM 提取（mock 模式）"""
    text = sample_text_file.read_text(encoding="utf-8")

    # 使用 mock 模式
    result = importer._extract_with_llm(text, use_mock=True)

    assert result["package"] == "com.malware.trojan"
    assert result["risk_level"] == "CRITICAL"
